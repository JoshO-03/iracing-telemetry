import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import json
import sys
import os
from matplotlib.lines import Line2D
from analysis.cornerDetection import detectCorners

# ======================
# CONFIG
# ======================

# Default values
CSV_FILE = "data/telemetry.csv"
CALIBRATION_FILE = "src/tracks/models/166.json"
IMAGE_FILE = "src/tracks/models/166.png"
LAP = 2

# Parse command-line arguments
if len(sys.argv) > 1:
    # Usage: python3 TestCalibration.py [csv_file] [calibration_file] [lap] [image_file]
    if len(sys.argv) > 1:
        CSV_FILE = sys.argv[1]
    if len(sys.argv) > 2:
        CALIBRATION_FILE = sys.argv[2]
    if len(sys.argv) > 3:
        LAP = int(sys.argv[3])
    if len(sys.argv) > 4:
        IMAGE_FILE = sys.argv[4]
    else:
        # Try to read IMAGE_FILE from calibration JSON
        if os.path.exists(CALIBRATION_FILE):
            with open(CALIBRATION_FILE) as f:
                cal_data = json.load(f)
                IMAGE_FILE = cal_data.get('image_file', IMAGE_FILE)

print(f"\n{'='*50}")
print("TEST CALIBRATION")
print(f"{'='*50}")
print(f"CSV File: {CSV_FILE}")
print(f"Calibration: {CALIBRATION_FILE}")
print(f"Image File: {IMAGE_FILE}")
print(f"Lap: {LAP}")
print(f"{'='*50}\n")

df = pd.read_csv(CSV_FILE)


# ======================
# CORNERS
# ======================

# Replace this with your detectCorners() output

corners = detectCorners(df, LAP)


# ======================
# LOAD CALIBRATION
# ======================

print("Loading calibration...")

with open(CALIBRATION_FILE) as f:
    calibration = json.load(f)

matrix = np.array(calibration["matrix"])


# ======================
# LOAD TELEMETRY
# ======================

print("Loading telemetry...")

df = pd.read_csv(CSV_FILE)

df = df[df["Lap"] == LAP].reset_index(drop=True)


# ======================
# LOAD IMAGE
# ======================

print("Loading track map...")

image = mpimg.imread(IMAGE_FILE)


# ======================
# CONVERT GPS TO IMAGE
# ======================

lat = df["Lat"].values
lon = df["Lon"].values

lat_scale = 111320
lon_scale = 111320 * np.cos(np.mean(lat) * np.pi / 180)

x = (lon - np.mean(lon)) * lon_scale
y = (lat - np.mean(lat)) * lat_scale


points = []

for px, py in zip(x, y):

    image_x = (
        matrix[0] * px +
        matrix[1] * py +
        matrix[2]
    )

    image_y = (
        matrix[3] * px +
        matrix[4] * py +
        matrix[5]
    )

    points.append([image_x, image_y])


points = np.array(points)


# ======================
# CHECK IF POINT IS CORNER
# ======================

def is_corner(distance, corners):

    for corner in corners:

        if corner["startDistPct"] <= distance <= corner["endDistPct"]:
            return True

    return False



# ======================
# DISPLAY
# ======================

fig, ax = plt.subplots(figsize=(12, 10))


# Background

ax.imshow(image)


# ======================
# DRAW RACING LINE
# ======================

lap_dist = df["LapDistPct"].values


for i in range(len(points)-1):

    start = points[i]
    end = points[i+1]

    distance = lap_dist[i]


    if is_corner(distance, corners):

        colour = "red"

    else:

        colour = "grey"


    ax.plot(
        [start[0], end[0]],
        [start[1], end[1]],
        color=colour,
        linewidth=2,
        zorder=5
    )


# ======================
# DRAW APEX POINTS
# ======================

for i, corner in enumerate(corners):
    apex_dist = corner.get("apexDist")
    
    if apex_dist is not None:
        # Find the closest point to apex distance
        closest_idx = np.argmin(np.abs(lap_dist - apex_dist))
        apex_point = points[closest_idx]
        
        ax.plot(
            apex_point[0],
            apex_point[1],
            marker='o',
            markersize=10,
            color='yellow',
            markeredgecolor='black',
            markeredgewidth=2,
            zorder=10,
            label='Apex' if i == 0 else ''  # Label only first point
        )



# ======================
# LEGEND
# ======================

legend_elements = [

    Line2D(
        [0],
        [0],
        color="grey",
        lw=3,
        label="Racing line"
    ),

    Line2D(
        [0],
        [0],
        color="red",
        lw=3,
        label="Corner sections"
    ),

    Line2D(
        [0],
        [0],
        marker='o',
        color='w',
        markerfacecolor='yellow',
        markeredgecolor='black',
        markeredgewidth=2,
        markersize=10,
        label="Apex point"
    )

]


ax.legend(
    handles=legend_elements,
    loc="upper left",
    fontsize=12
)


# ======================
# FINAL DISPLAY
# ======================

ax.set_aspect("equal")

ax.set_title(
    f"Track Map with Corner Detection - Lap {LAP}",
    fontsize=14,
    fontweight="bold"
)


plt.tight_layout()
plt.show()