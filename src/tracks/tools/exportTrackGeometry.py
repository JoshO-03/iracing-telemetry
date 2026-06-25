"""
exportTrackGeometry.py

Builds left/right/centerline geometry for a track from two KML files
(as in plotTrackGeometry.py) and exports it to a single <track_name>.json
for consumption by a TypeScript telemetry analyser.

USAGE:
    PYTHONPATH=src python3 src/tracks/tools/exportTrackGeometry.py \
        --left path/to/left.kml \
        --right path/to/right.kml \
        --name okayama \
        --out src/tracks/models

This produces: src/tracks/models/okayama.json
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
# MAIN BUILD
# ======================

def build_track_geometry(left_kml_path, right_kml_path, track_name):

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
    track_length = float(centerline_cumdist[-1])

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
                    "distance": round(float(d), 3),
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
                "distance": round(float(d), 3),
                "width": round(float(w), 4),
                "normalX": round(nx, 6),
                "normalY": round(ny, 6),
            }
            for (x, y), (lat, lon), d, w, (nx, ny)
            in zip(centerline_xy, centerline_gps, centerline_cumdist, widths, centerline_normals)
        ]
    }

    geometry = {
        "schemaVersion": 1,
        "track": {
            "name": track_name,
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "origin": {
                "lat": round(float(origin_lat), 8),
                "lon": round(float(origin_lon), 8),
            },
            "pointCount": RESAMPLE_POINTS,
            "trackLength": round(track_length, 3),
            "closed": True,
        },
        "left": boundary_block(left_resampled, left_gps_resampled, left_cumdist),
        "right": boundary_block(right_resampled, right_gps_resampled, right_cumdist),
        "centerline": centerline_block,
    }

    return geometry


def main():
    parser = argparse.ArgumentParser(description="Export track boundary/centerline geometry to JSON")
    parser.add_argument("--left", required=True, help="Path to left boundary KML file")
    parser.add_argument("--right", required=True, help="Path to right boundary KML file")
    parser.add_argument("--name", required=True, help="Track name (used as output filename and in JSON)")
    parser.add_argument("--out", default=".", help="Output directory (default: current directory)")

    args = parser.parse_args()

    geometry = build_track_geometry(args.left, args.right, args.name)

    out_path = f"{args.out.rstrip('/')}/{args.name}.json"
    with open(out_path, "w") as f:
        json.dump(geometry, f, indent=2)

    print(f"\nWrote {out_path}")
    print(f"Track length: {geometry['track']['trackLength']:.1f} m")
    print(f"Points per boundary: {geometry['track']['pointCount']}")


if __name__ == "__main__":
    main()
