"""
plotTrackGeometry.py

Plots a track's left/right boundaries and centerline from a
<track_name>.json file produced by exportTrackGeometry.py, optionally
overlaying a racing line from an iRacing telemetry CSV (parsed from a
.ibt file) for a specific lap.

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
"""

import argparse
import csv
import json

import matplotlib.pyplot as plt

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
                racing_line_xy=None, lap_label=None):

    track_info = geometry["track"]
    left_points = geometry["left"]["points"]
    right_points = geometry["right"]["points"]
    center_points = geometry["centerline"]["points"]

    left_x, left_y = extract_xy(left_points)
    right_x, right_y = extract_xy(right_points)
    center_x, center_y = extract_xy(center_points)

    plt.figure(figsize=(12, 12))

    plt.plot(left_x, left_y, label="Left", color="tab:blue")
    plt.plot(right_x, right_y, label="Right", color="tab:orange")
    plt.plot(center_x, center_y, label="Centerline", color="tab:green")

    if racing_line_xy:
        rx = [p[0] for p in racing_line_xy]
        ry = [p[1] for p in racing_line_xy]
        line_label = f"Racing line ({lap_label})" if lap_label else "Racing line"
        plt.plot(rx, ry, label=line_label, color="tab:red", linewidth=1.5, zorder=5)

    if label_interval and label_interval > 0:
        for i in range(0, len(center_points), label_interval):
            plt.text(
                center_points[i]["x"],
                center_points[i]["y"],
                f"{i}",
                fontsize=8
            )

    plt.axis("equal")
    plt.grid(True)

    name = track_info.get("name", "Track")
    length = track_info.get("trackLength")
    title = f"{name} — Track Geometry"
    if length:
        title += f" ({length:.0f} m)"
    plt.title(title)

    plt.xlabel("X metres")
    plt.ylabel("Y metres")
    plt.legend()

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


def main():
    parser = argparse.ArgumentParser(description="Plot track geometry, optionally with a telemetry racing line overlay")
    parser.add_argument("--json", required=True, help="Path to <track_name>.json")
    parser.add_argument("--label-interval", type=int, default=100, help="Label every Nth centerline point (0 to disable)")
    parser.add_argument("--save", default=None, help="Path to save the plot to (e.g. out.png). If omitted, shows interactively.")
    parser.add_argument("--telemetry", default=None, help="Path to a telemetry CSV (parsed from an .ibt file) to overlay as a racing line")
    parser.add_argument("--lap", type=int, default=None, help="Lap number to plot from the telemetry CSV (matches the 'Lap' column). Required if --telemetry is given.")

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
        lap_label=lap_label
    )


if __name__ == "__main__":
    main()