"""
plotTrackGeometry.py

Plots a track's left/right boundaries and centerline from a
<track_name>.json file produced by exportTrackGeometry.py, optionally
overlaying a racing line from an iRacing telemetry CSV (parsed from a
.ibt file) for a specific lap.

If the JSON includes a "corners" list (from exportTrackGeometry.py's
geometric corner detection), each corner is drawn as a thick coloured arc
over the centerline with a numbered label, so detection results can be
checked visually. Pass --no-corners to turn this off.

This script does NOT recompute any track geometry -- it just reads and
visualises what's already in the JSON. Telemetry GPS (Lat/Lon) is
converted into the same local XY frame as the track using the origin
stored in the track JSON, so it overlays correctly.

USAGE:
    PYTHONPATH=src python3 src/tracks/tools/plotTrackGeometry.py \
        --json src/tracks/models/okayama.json

    With a racing line overlay:
    PYTHONPATH=src python3 src/tracks/tools/plotTrackGeometry.py \
        --json src/tracks/models/okayama.json \
        --telemetry path/to/telemetry.csv \
        --lap 2

    Optional:
        --label-interval 100   (label every Nth centerline point, default 100)
        --save out.png         (save instead of / as well as showing)
        --no-corners           (don't highlight detected corners)
"""

import argparse
import csv
import json

import matplotlib.pyplot as plt
from matplotlib import colormaps

from tracks.tools.coordinateSystem import gps_to_xy


# ======================
# TRACK JSON
# ======================

def load_track_json(json_path):
    with open(json_path, "r") as f:
        return json.load(f)


def extract_xy(points):
    xs = [p["x"] for p in points]
    ys = [p["y"] for p in points]
    return xs, ys


# ======================
# CORNER HIGHLIGHTING
# ======================
#
# Corners (if present in the JSON) are drawn as thick coloured arcs over the
# centerline, with a numbered label at the midpoint. This is read-only, same
# as the rest of this script -- it just visualises corners already detected
# by exportTrackGeometry.py, it doesn't recompute anything.

def points_in_corner(center_points, track_length, start_pct, end_pct):
    """
    Returns the subset of centerline points that fall within a corner's
    [startDistPct, endDistPct] range, expressed as fractions of track
    length (0-1). Handles corners that wrap across the start/finish line
    (startDistPct > endDistPct, e.g. 0.97 -> 0.02).
    """
    if start_pct <= end_pct:
        return [
            p for p in center_points
            if start_pct <= (p["distance"] / track_length) <= end_pct
        ]

    return [
        p for p in center_points
        if (p["distance"] / track_length) >= start_pct
        or (p["distance"] / track_length) <= end_pct
    ]


def plot_corners(ax, geometry):
    """
    Draws each corner in geometry["corners"] as a thick coloured arc over
    the centerline, labelled with its cornerId at the midpoint. Returns the
    number of corners drawn (0 if none present/empty), so callers can decide
    whether to mention corners in the title/summary.
    """
    corners = geometry.get("corners") or []
    if not corners:
        return 0

    center_points = geometry["centerline"]["points"]
    track_length = geometry["track"]["trackLength"]

    cmap = colormaps.get_cmap("tab20")

    for i, corner in enumerate(corners):
        pts = points_in_corner(
            center_points,
            track_length,
            corner["startDistPct"],
            corner["endDistPct"],
        )

        if not pts:
            continue

        xs = [p["x"] for p in pts]
        ys = [p["y"] for p in pts]
        color = cmap(i % cmap.N)

        ax.plot(xs, ys, linewidth=5, color=color, zorder=4, solid_capstyle="round")

        mid = pts[len(pts) // 2]
        ax.annotate(
            str(corner["cornerId"]),
            (mid["x"], mid["y"]),
            fontsize=9,
            fontweight="bold",
            ha="center",
            va="center",
            zorder=5,
            bbox=dict(boxstyle="circle,pad=0.25", facecolor="white", edgecolor="black", linewidth=1),
        )

    return len(corners)


# ======================
# TELEMETRY CSV
# ======================

def load_telemetry_lap(csv_path, lap_number):
    """
    Loads rows for a specific lap number from an iRacing telemetry CSV
    (as parsed from an .ibt file), keyed by the 'Lap' column.

    Skips rows with (Lat, Lon) == (0, 0), which show up at the very start
    of a session before the car has a GPS fix (e.g. in the garage).

    Returns: list of dicts with at least 'lat', 'lon', 'lapDistPct',
             'speed' (m/s, as reported by iRacing) for the requested lap,
             in original row order (i.e. chronological order around the lap).
    """
    rows = []

    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)

        for row in reader:
            if int(row["Lap"]) != lap_number:
                continue

            lat = float(row["Lat"])
            lon = float(row["Lon"])

            if lat == 0.0 and lon == 0.0:
                continue

            rows.append({
                "lat": lat,
                "lon": lon,
                "lapDistPct": float(row["LapDistPct"]),
                "speed": float(row["Speed"]),
            })

    if not rows:
        raise ValueError(
            f"No usable telemetry rows found for lap {lap_number} in {csv_path}. "
            f"Check the --lap value against the CSV's 'Lap' column."
        )

    return rows


def convert_telemetry_to_xy(telemetry_rows, origin_lat, origin_lon):
    xy_points = []
    for row in telemetry_rows:
        x, y = gps_to_xy(row["lat"], row["lon"], origin_lat, origin_lon)
        xy_points.append((x, y))
    return xy_points


# ======================
# PLOTTING
# ======================

def plot_track(geometry, label_interval=100, save_path=None,
                racing_line_xy=None, lap_label=None, show_corners=True):

    track_info = geometry["track"]
    left_points = geometry["left"]["points"]
    right_points = geometry["right"]["points"]
    center_points = geometry["centerline"]["points"]

    left_x, left_y = extract_xy(left_points)
    right_x, right_y = extract_xy(right_points)
    center_x, center_y = extract_xy(center_points)

    fig, ax = plt.subplots(figsize=(12, 12))

    ax.plot(left_x, left_y, label="Left", color="tab:blue", linewidth=1, alpha=0.6)
    ax.plot(right_x, right_y, label="Right", color="tab:orange", linewidth=1, alpha=0.6)
    ax.plot(center_x, center_y, label="Centerline", color="gray", linewidth=1.5, zorder=2)

    num_corners_drawn = 0
    if show_corners:
        num_corners_drawn = plot_corners(ax, geometry)
        if num_corners_drawn:
            # One proxy legend entry for "corners" rather than one per corner --
            # the numbered labels on the plot itself identify individual corners.
            ax.plot([], [], linewidth=5, color="tab:red", label=f"Corners ({num_corners_drawn})")

    if racing_line_xy:
        rx = [p[0] for p in racing_line_xy]
        ry = [p[1] for p in racing_line_xy]
        line_label = f"Racing line ({lap_label})" if lap_label else "Racing line"
        ax.plot(rx, ry, label=line_label, color="black", linewidth=1.2, zorder=6, linestyle="--")

    if label_interval and label_interval > 0:
        for i in range(0, len(center_points), label_interval):
            ax.text(
                center_points[i]["x"],
                center_points[i]["y"],
                f"{i}",
                fontsize=8
            )

    ax.axis("equal")
    ax.grid(True, alpha=0.3)

    name = track_info.get("name", "Track")
    length = track_info.get("trackLength")
    title = f"{name} — Track Geometry"
    if length:
        title += f" ({length:.0f} m)"
    if num_corners_drawn:
        title += f" — {num_corners_drawn} corners"
    ax.set_title(title)

    ax.set_xlabel("X metres")
    ax.set_ylabel("Y metres")
    ax.legend()

    if save_path:
        plt.savefig(save_path, dpi=150)
        print(f"Saved plot to {save_path}")
    else:
        plt.show()


def print_summary(geometry):
    track_info = geometry["track"]
    centerline = geometry["centerline"]["points"]

    print(f"Track: {track_info.get('name')}")
    print(f"Generated at: {track_info.get('generatedAt')}")
    print(f"Track length: {track_info.get('trackLength'):.2f} m")
    print(f"Point count: {track_info.get('pointCount')}")

    widths = [p["width"] for p in centerline]
    print(f"Width range: {min(widths):.2f} m – {max(widths):.2f} m")

    corners = geometry.get("corners") or []
    print(f"Corners: {len(corners)}")

    sectors = geometry.get("sectors") or []
    print(f"Sectors: {len(sectors)}")


def main():
    parser = argparse.ArgumentParser(description="Plot track geometry, optionally with a telemetry racing line overlay")
    parser.add_argument("--json", required=True, help="Path to <track_name>.json")
    parser.add_argument("--label-interval", type=int, default=100, help="Label every Nth centerline point (0 to disable)")
    parser.add_argument("--save", default=None, help="Path to save the plot to (e.g. out.png). If omitted, shows interactively.")
    parser.add_argument("--telemetry", default=None, help="Path to a telemetry CSV (parsed from an .ibt file) to overlay as a racing line")
    parser.add_argument("--lap", type=int, default=None, help="Lap number to plot from the telemetry CSV (matches the 'Lap' column). Required if --telemetry is given.")
    parser.add_argument("--no-corners", action="store_true", help="Don't highlight detected corners, even if present in the JSON")

    args = parser.parse_args()

    if args.telemetry and args.lap is None:
        parser.error("--lap is required when --telemetry is given")

    geometry = load_track_json(args.json)
    print_summary(geometry)

    racing_line_xy = None
    lap_label = None

    if args.telemetry:
        origin = geometry["track"]["origin"]

        telemetry_rows = load_telemetry_lap(args.telemetry, args.lap)
        racing_line_xy = convert_telemetry_to_xy(
            telemetry_rows,
            origin["lat"],
            origin["lon"]
        )

        print(f"\nLoaded {len(racing_line_xy)} telemetry points for lap {args.lap}")
        lap_label = f"lap {args.lap}"

    plot_track(
        geometry,
        label_interval=args.label_interval,
        save_path=args.save,
        racing_line_xy=racing_line_xy,
        lap_label=lap_label,
        show_corners=not args.no_corners,
    )


if __name__ == "__main__":
    main()