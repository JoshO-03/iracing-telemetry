"""
exportTrackGeometry.py

Builds left/right/centerline geometry for a track from two KML files
(as in plotTrackGeometry.py) and exports it to a single <track_name>.json
for consumption by a TypeScript telemetry analyser.

USAGE:
    PYTHONPATH=src python3 src/tracks/tools/exportTrackGeometry.py \
        --left path/to/left.kml \
        --right path/to/right.kml \
        --name "Okayama International Circuit" \
        --config-name "Full Course" \
        --slug okayama-full-course \
        --track-id 166 \
        --out src/tracks/models

This produces: src/tracks/models/okayama-full-course.json
"""

import argparse
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

import numpy as np

from tracks.tools.coordinateSystem import gps_to_xy


RESAMPLE_POINTS = 1000
NORMAL_MAX_SEARCH_DIST = 40  # metres; clip to a bit more than your widest track section


# ======================
# KML LOADER
# ======================

def load_kml_coordinates(filename):
    tree = ET.parse(filename)
    root = tree.getroot()
    namespace = {"kml": "http://www.opengis.net/kml/2.2"}

    coordinates_element = root.find(".//kml:LineString/kml:coordinates", namespace)
    if coordinates_element is None:
        raise ValueError(f"No LineString found in {filename}")

    points = []
    for coordinate in coordinates_element.text.strip().split():
        lon, lat, *_ = coordinate.split(",")
        points.append((float(lat), float(lon)))

    return points


# ======================
# GEOMETRY HELPERS
# ======================

def point_distance(a, b):
    return np.linalg.norm(np.array(a) - np.array(b))


def polygon_direction(points):
    area = 0
    for i in range(len(points)):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % len(points)]
        area += (x2 - x1) * (y2 + y1)
    return 1 if area > 0 else -1


def ensure_same_direction(left, right):
    if polygon_direction(left) != polygon_direction(right):
        right = right[::-1]
    return right


def rotate_boundary(points, offset):
    return points[offset:] + points[:offset]


def align_boundary_start(left, right):
    start = left[0]
    closest_index = min(
        range(len(right)),
        key=lambda i: point_distance(start, right[i])
    )
    return rotate_boundary(right, closest_index)


def cumulative_distance(points):
    distances = [0.0]
    for i in range(1, len(points)):
        distances.append(distances[-1] + point_distance(points[i], points[i - 1]))
    return np.array(distances)


def closed_loop_length(points, cumulative_distances):
    return float(cumulative_distances[-1] + point_distance(points[-1], points[0]))


def resample_boundary(points, num_points):
    points = np.array(points)
    distances = cumulative_distance(points)
    total_distance = distances[-1]
    target_distances = np.linspace(0, total_distance, num_points)

    x = np.interp(target_distances, distances, points[:, 0])
    y = np.interp(target_distances, distances, points[:, 1])

    return list(zip(x, y)), target_distances


def find_normal_intersection(point, normal, boundary_array, max_dist):
    best_point = None
    best_t = None

    px, py = point
    dx, dy = normal

    for i in range(len(boundary_array) - 1):
        ax, ay = boundary_array[i]
        bx, by = boundary_array[i + 1]
        ex, ey = bx - ax, by - ay

        denom = dx * (-ey) - dy * (-ex)
        if abs(denom) < 1e-12:
            continue

        rhsx, rhsy = ax - px, ay - py
        t = (rhsx * (-ey) - rhsy * (-ex)) / denom
        s = (dx * rhsy - dy * rhsx) / denom

        if 0.0 <= s <= 1.0 and abs(t) <= max_dist:
            if best_t is None or abs(t) < abs(best_t):
                best_t = t
                best_point = (px + t * dx, py + t * dy)

    return best_point


def build_centerline(left_resampled, right_xy, max_dist=NORMAL_MAX_SEARCH_DIST):
    """
    For each point on left_resampled, cast a ray along the local normal
    (perpendicular to the smoothed tangent direction) and find where it
    crosses the raw right boundary. Centerline point = midpoint.
    Falls back to nearest-point if no clean intersection is found.

    Returns: list of (x, y), list of (normal_x, normal_y) per left point,
             fallback_count
    """
    left_arr = np.array(left_resampled)
    right_arr = np.array(right_xy)
    n = len(left_arr)

    centerline = []
    normals = []
    fallback_count = 0

    for i in range(n):
        p_prev = left_arr[(i - 1) % n]
        p_next = left_arr[(i + 1) % n]

        tangent = p_next - p_prev
        tnorm = np.hypot(tangent[0], tangent[1])
        tangent = tangent / tnorm if tnorm > 1e-9 else np.array([1.0, 0.0])

        normal = np.array([-tangent[1], tangent[0]])

        p = left_arr[i]
        hit = find_normal_intersection(p, normal, right_arr, max_dist)

        if hit is None:
            diffs = right_arr - p
            dist = np.hypot(diffs[:, 0], diffs[:, 1])
            hit = right_arr[np.argmin(dist)]
            fallback_count += 1

        cx = (p[0] + hit[0]) / 2
        cy = (p[1] + hit[1]) / 2
        centerline.append((cx, cy))
        normals.append((float(normal[0]), float(normal[1])))

    if fallback_count:
        print(f"Normal projection fell back to nearest-point for {fallback_count} / {n} points")

    return centerline, normals


def convert_points(points, origin_lat, origin_lon):
    result = []
    for lat, lon in points:
        x, y = gps_to_xy(lat, lon, origin_lat, origin_lon)
        result.append((x, y))
    return result


# ======================
# CORNER DETECTION (geometric, from centerline curvature)
# ======================
#
# A corner is a property of the track, not of how someone drove it -- so it
# is detected here, once, from the centerline shape itself. This is
# deliberately independent of any telemetry/lap data: no braking, throttle,
# or steering input is used. That's what lets this catch flat-out corners
# (track curves, but the driver barely changes their inputs) as well as
# hairpins, with no special-casing, and it means a track model can be built
# from KML files alone -- no .ibt or telemetry CSV required.
#
# Method: at each resampled centerline point, compute the local heading
# (the same tangent direction used to build the normals/centerline) and look
# at how much that heading changes per metre travelled -- i.e. curvature.
# Straights have near-zero curvature. Corners show a sustained, elevated
# curvature region. We threshold, then merge nearby/overlapping regions into
# discrete corners, the same gap-merging idea as the old telemetry-based
# detector, just applied to geometry instead of driver input.

CURVATURE_THRESHOLD_DEG_PER_M = 0.3   # heading change (degrees) per metre; tune per track
CORNER_GAP_THRESHOLD_M = 15           # merge corner regions separated by less than this
MIN_CORNER_LENGTH_M = 8                # discard corner regions shorter than this


def compute_heading_deg(points):
    """
    Local heading (degrees) at each point, from the tangent direction
    p[i+1] - p[i-1] (same construction as the normals in build_centerline).
    Track is closed, so indices wrap.
    """
    pts = np.array(points)
    n = len(pts)
    headings = np.zeros(n)

    for i in range(n):
        p_prev = pts[(i - 1) % n]
        p_next = pts[(i + 1) % n]
        dx, dy = p_next - p_prev
        headings[i] = np.degrees(np.arctan2(dy, dx))

    return headings


def compute_curvature(points, cumdist):
    """
    Curvature in degrees of heading-change per metre, at each centerline
    point. Handles the +/-180 degree wraparound when computing the heading
    difference between consecutive points.

    Note: cumdist[-1] is the distance to the LAST point, not the full closed
    loop -- it does not include the closing segment back to point 0 (the
    resampling in resample_boundary doesn't guarantee point[-1] lands exactly
    on point[0], so that final gap, however small, must be measured and
    added explicitly here. Skipping it causes a near-zero ddist at the
    wraparound and a curvature spike.)
    """
    headings = compute_heading_deg(points)
    n = len(headings)
    closing_dist = point_distance(points[-1], points[0])
    curvature = np.zeros(n)

    for i in range(n):
        i_next = (i + 1) % n
        dheading = headings[i_next] - headings[i]
        # Wrap to [-180, 180] so e.g. 179 -> -179 reads as a small turn, not a u-turn
        dheading = (dheading + 180) % 360 - 180

        if i_next == 0:
            ddist = closing_dist
        else:
            ddist = cumdist[i_next] - cumdist[i]
        ddist = max(ddist, 1e-6)

        curvature[i] = abs(dheading) / ddist

    return curvature


def smooth_curvature(curvature, window=5):
    """Light moving-average smoothing so single noisy points don't fragment a corner."""
    kernel = np.ones(window) / window
    padded = np.pad(curvature, (window // 2, window // 2), mode="wrap")
    return np.convolve(padded, kernel, mode="valid")[: len(curvature)]


def detect_corners_from_curvature(
    centerline_xy,
    centerline_cumdist,
    threshold=CURVATURE_THRESHOLD_DEG_PER_M,
    gap_threshold_m=CORNER_GAP_THRESHOLD_M,
    min_length_m=MIN_CORNER_LENGTH_M,
):
    """
    Returns a list of corners, each as:
        {
            "cornerId": int,
            "startDistPct": float,   # 0-1, fraction of track length
            "endDistPct": float,
            "apexDistPct": float,    # point of maximum curvature within the corner
            "maxCurvatureDegPerMeter": float,   # useful later for corner-type classification
        }

    Purely geometric -- no telemetry involved. Designed to be run once per
    track (via main()) and visually checked with plotTrackGeometry.py before
    trusting the output, same workflow as the telemetry-based detector it
    replaces.
    """
    track_length = closed_loop_length(centerline_xy, centerline_cumdist)
    n = len(centerline_xy)

    curvature = compute_curvature(centerline_xy, centerline_cumdist)
    curvature = smooth_curvature(curvature)

    above = curvature >= threshold

    # Find contiguous (wrap-aware) runs of "above threshold" points.
    # Walk twice around the lap so a region spanning the start/finish line
    # isn't artificially cut in half.
    raw_regions = []
    in_region = False
    region_start = None

    for i in range(2 * n):
        idx = i % n
        if above[idx] and not in_region:
            region_start = i
            in_region = True
        elif not above[idx] and in_region:
            raw_regions.append((region_start, i - 1))
            in_region = False
        if i >= n and not in_region:
            break

    if in_region:
        raw_regions.append((region_start, region_start + n - 1))

    # Deduplicate regions that are just the start/finish wraparound counted twice
    seen = set()
    deduped = []
    for start, end in raw_regions:
        key = (start % n, end % n)
        if key in seen:
            continue
        seen.add(key)
        deduped.append((start, end))

    if not deduped:
        return []

    def region_dist(start, end):
        s, e = start % n, end % n
        if e >= s:
            return centerline_cumdist[e] - centerline_cumdist[s]
        return (track_length - centerline_cumdist[s]) + centerline_cumdist[e]

    deduped.sort(key=lambda r: r[0])

    # Merge regions that are close together (e.g. a corner with a brief
    # straightening mid-apex that dips just under threshold)
    merged = [deduped[0]]
    for start, end in deduped[1:]:
        last_start, last_end = merged[-1]
        gap = region_dist(last_end, start)
        if gap <= gap_threshold_m:
            merged[-1] = (last_start, end)
        else:
            merged.append((start, end))

    corners = []
    corner_id = 1
    for start, end in merged:
        length = region_dist(start, end)
        if length < min_length_m:
            continue

        # Walk the region (wrap-aware) to find the apex: point of max curvature
        indices = [j % n for j in range(start, end + 1)]
        local_curvatures = [curvature[j] for j in indices]
        apex_local_idx = int(np.argmax(local_curvatures))
        apex_idx = indices[apex_local_idx]

        start_idx, end_idx = start % n, end % n

        corners.append({
            "cornerId": corner_id,
            "startDistPct": round(centerline_cumdist[start_idx] / track_length, 4),
            "endDistPct": round(centerline_cumdist[end_idx] / track_length, 4),
            "apexDistPct": round(centerline_cumdist[apex_idx] / track_length, 4),
            "maxCurvatureDegPerMeter": round(float(curvature[apex_idx]), 4),
        })
        corner_id += 1

    return corners


# ======================
# SECTORS (manual entry only)
# ======================
#
# Unlike corners, sectors are not a geometric property of the track -- they
# are an arbitrary choice of where splits fall. Deliberately manual-only:
# track model creation should never depend on having a telemetry/.ibt file
# available.
#
# Shape matches the TrackModel schema: each sector is just a START
# percentage around the lap, not a start+end pair. Sector 1 always starts at
# 0.0 (the start/finish line). Sector ends are derived in runtime code from
# the next sector's start, with the final sector ending at 1.0.

def sectors_from_starts(start_pcts):
    """
    start_pcts: sorted list of sector start percentages (0-1), NOT including
    the implicit 0.0 for sector 1 -- e.g. [0.259885, 0.509689, 0.694809] for
    a track with 4 sectors total.

    Returns sectors as {sectorId, startDistPct}. End percentages are
    deliberately not stored in TrackModel.
    """
    all_starts = [0.0] + sorted(start_pcts)
    sectors = []

    for i, start_pct in enumerate(all_starts):
        sectors.append({
            "sectorId": i + 1,
            "startDistPct": round(start_pct, 6),
        })

    return sectors


def collect_sector_data(track_length_m):
    """
    Interactive prompt for sector start percentages around the lap (0-1),
    matching the shape iRacing itself uses for sectors. Sector 1's start
    (0.0, the start/finish line) is implicit and not asked for. Returns
    sectors as {sectorId, startDistPct}, or None if skipped/invalid.
    Entirely independent of any telemetry data.
    """
    print("\n" + "=" * 50)
    print("SECTOR CONFIGURATION (manual entry)")
    print("=" * 50)
    print(f"Track length: {track_length_m:.1f} m")
    print(
        "Enter each additional sector's START as a fraction of the lap "
        "(0-1), e.g. 0.26 for a sector that starts 26% of the way around. "
        "Sector 1 always starts at 0.0 and is added automatically."
    )

    try:
        answer = input("\nAdd sectors now? (y/N): ").strip().lower()
        if answer != "y":
            return None

        num_extra_sectors = int(input("How many sectors in total (including sector 1)? "))
        if num_extra_sectors <= 1:
            print("Need at least 2 sectors to be meaningful. Skipping sector data.")
            return None

        start_pcts = []
        previous_start = 0.0

        for i in range(2, num_extra_sectors + 1):
            sector_start = float(input(f"Enter sector {i} start (fraction of lap, 0-1): "))

            if sector_start <= previous_start or sector_start >= 1.0:
                print(f"Invalid start percentage. Must be > {previous_start} and < 1.0")
                return None

            start_pcts.append(sector_start)
            previous_start = sector_start

        sectors = sectors_from_starts(start_pcts)

        print("\nSector data collected:")
        for sector in sectors:
            print(f"  Sector {sector['sectorId']}: starts at {sector['startDistPct']:.4f}")

        return sectors

    except ValueError:
        print("Invalid input. Skipping sector data.")
        return None


# ======================
# MAIN BUILD
# ======================

def build_track_geometry(
    left_kml_path,
    right_kml_path,
    track_name,
    track_id,
    config_name,
    slug,
    country=None,
    notes=None,
):

    left_gps = load_kml_coordinates(left_kml_path)
    right_gps = load_kml_coordinates(right_kml_path)

    origin_lat = left_gps[0][0]
    origin_lon = left_gps[0][1]

    left_xy = convert_points(left_gps, origin_lat, origin_lon)
    right_xy = convert_points(right_gps, origin_lat, origin_lon)

    right_xy = ensure_same_direction(left_xy, right_xy)
    right_xy = align_boundary_start(left_xy, right_xy)

    left_resampled, left_cumdist = resample_boundary(left_xy, RESAMPLE_POINTS)
    right_resampled, right_cumdist = resample_boundary(right_xy, RESAMPLE_POINTS)

    centerline_xy, centerline_normals = build_centerline(left_resampled, right_xy)

    # Cumulative distance ALONG THE CENTERLINE ITSELF (this is the
    # distance-along-track metric, not the left boundary's own arc length).
    centerline_cumdist = cumulative_distance(centerline_xy)
    track_length = closed_loop_length(centerline_xy, centerline_cumdist)

    # Track width at each centerline point, measured as the distance from
    # the centerline point to its corresponding left-boundary point, x2
    # (since centerline is the midpoint, this is half the full width).
    widths = []
    for i in range(len(centerline_xy)):
        half_width = point_distance(centerline_xy[i], left_resampled[i])
        widths.append(half_width * 2)

    # Track each point's corresponding GPS coordinate too, by re-deriving
    # lat/lon from the resampled XY via inverse of the same origin (we
    # don't have an inverse gps_to_xy, so instead we re-find nearest GPS
    # point from the original list as an approximation -- good enough for
    # cross-checking purposes, not for precision navigation).
    def nearest_gps_for_xy_points(xy_points, raw_xy, raw_gps):
        raw_xy_arr = np.array(raw_xy)
        gps_out = []
        for p in xy_points:
            diffs = raw_xy_arr - np.array(p)
            dist = np.hypot(diffs[:, 0], diffs[:, 1])
            idx = int(np.argmin(dist))
            gps_out.append(raw_gps[idx])
        return gps_out

    left_gps_resampled = nearest_gps_for_xy_points(left_resampled, left_xy, left_gps)
    right_gps_resampled = nearest_gps_for_xy_points(right_resampled, right_xy, right_gps)
    centerline_gps = nearest_gps_for_xy_points(centerline_xy, left_xy, left_gps)

    # ======================
    # ASSEMBLE JSON
    # ======================

    def boundary_block(xy_points, gps_points, cumdist):
        return {
            "points": [
                {
                    "x": round(float(x), 4),
                    "y": round(float(y), 4),
                    "lat": round(float(lat), 8),
                    "lon": round(float(lon), 8),
                    "distanceMeters": round(float(d), 3),
                }
                for (x, y), (lat, lon), d in zip(xy_points, gps_points, cumdist)
            ]
        }

    centerline_block = {
        "points": [
            {
                "x": round(float(x), 4),
                "y": round(float(y), 4),
                "lat": round(float(lat), 8),
                "lon": round(float(lon), 8),
                "distanceMeters": round(float(d), 3),
                "widthMeters": round(float(w), 4),
                "normalX": round(nx, 6),
                "normalY": round(ny, 6),
            }
            for (x, y), (lat, lon), d, w, (nx, ny)
            in zip(centerline_xy, centerline_gps, centerline_cumdist, widths, centerline_normals)
        ]
    }

    corners = detect_corners_from_curvature(centerline_xy, centerline_cumdist)

    geometry = {
        "schemaVersion": 1,
        "track": {
            "trackId": int(track_id),
            "name": track_name,
            "configName": config_name,
            "slug": slug,
            "trackLengthMeters": round(track_length, 3),
            "closed": True,
        },
        "generation": {
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "source": "exportTrackGeometry.py",
            "pointCount": RESAMPLE_POINTS,
        },
        "coordinateSystem": {
            "type": "local_xy_meters",
            "originLat": round(float(origin_lat), 8),
            "originLon": round(float(origin_lon), 8),
            "xUnit": "meters",
            "yUnit": "meters",
        },
        "geometry": {
            "leftBoundary": boundary_block(left_resampled, left_gps_resampled, left_cumdist),
            "rightBoundary": boundary_block(right_resampled, right_gps_resampled, right_cumdist),
            "centerline": centerline_block,
        },
        "sectors": sectors_from_starts([]),
        "corners": corners,
    }

    if country:
        geometry["track"]["country"] = country
    if notes:
        geometry["generation"]["notes"] = notes

    return geometry


def main():
    parser = argparse.ArgumentParser(description="Export track boundary/centerline/corner geometry to JSON")
    parser.add_argument("--left", required=True, help="Path to left boundary KML file")
    parser.add_argument("--right", required=True, help="Path to right boundary KML file")
    parser.add_argument("--name", required=True, help="Human-readable track name")
    parser.add_argument("--config-name", required=True, help="Human-readable track configuration/layout name")
    parser.add_argument("--slug", required=True, help="Stable app/file-friendly track slug, used as the output filename")
    parser.add_argument("--track-id", required=True, type=int, help="iRacing TrackID for this track/configuration")
    parser.add_argument("--country", default=None, help="Optional track country")
    parser.add_argument("--notes", default=None, help="Optional generation notes")
    parser.add_argument("--out", default=".", help="Output directory (default: current directory)")
    parser.add_argument("--skip-sectors", action="store_true", help="Skip the interactive sector prompt entirely")

    args = parser.parse_args()

    geometry = build_track_geometry(
        args.left,
        args.right,
        args.name,
        args.track_id,
        args.config_name,
        args.slug,
        country=args.country,
        notes=args.notes,
    )

    print(f"\nDetected {len(geometry['corners'])} corner(s) from centerline curvature:")
    for corner in geometry["corners"]:
        print(
            f"  Corner {corner['cornerId']}: "
            f"{corner['startDistPct']:.4f} - {corner['endDistPct']:.4f} "
            f"(apex {corner['apexDistPct']:.4f}, curvature {corner['maxCurvatureDegPerMeter']:.3f} deg/m)"
        )
    print(
        "  (Cross-check this count against the track's official turn count "
        "from WeekendInfo.TrackNumTurns in a session's sessionInfo, if you have one handy. "
        "If it's off, adjust CURVATURE_THRESHOLD_DEG_PER_M / CORNER_GAP_THRESHOLD_M at the top "
        "of this file and re-run -- don't trust the count blindly.)"
    )

    sectors = None
    if not args.skip_sectors:
        sectors = collect_sector_data(geometry["track"]["trackLengthMeters"])
    if sectors:
        geometry["sectors"] = sectors

    out_path = f"{args.out.rstrip('/')}/{args.slug}.json"
    with open(out_path, "w") as f:
        json.dump(geometry, f, indent=2)

    print(f"\nWrote {out_path}")
    print(f"Track length: {geometry['track']['trackLengthMeters']:.1f} m")
    print(f"Points per boundary: {geometry['generation']['pointCount']}")
    print(f"Corners: {len(geometry['corners'])}")
    print(f"Sectors: {len(geometry.get('sectors', []))}")


if __name__ == "__main__":
    main()
