import pandas as pd
import matplotlib.pyplot as plt
import json

from tracks.tools.coordinateSystem import gps_to_xy

# ======================
# CONFIG
# ======================

CSV_FILE = "data/telemetry.csv"
REFERENCE_FILE = "src/tracks/models/okayama_reference.json"

LAP = 3


# ======================
# LOAD REFERENCE
# ======================

with open(REFERENCE_FILE) as f:
    reference = json.load(f)


origin = reference["reference_points"][0]

origin_lat = origin["lat"]
origin_lon = origin["lon"]


print("Origin:")
print(origin_lat, origin_lon)


# ======================
# LOAD TELEMETRY
# ======================

df = pd.read_csv(CSV_FILE)

lap = df[df["Lap"] == LAP].copy()


# ======================
# CONVERT TELEMETRY GPS TO XY
# ======================

xy = []

for _, row in lap.iterrows():

    x, y = gps_to_xy(
        row["Lat"],
        row["Lon"],
        origin_lat,
        origin_lon
    )

    xy.append((x, y))


lap["X"] = [p[0] for p in xy]
lap["Y"] = [p[1] for p in xy]


# ======================
# CONVERT REFERENCE POINTS TO XY
# ======================

reference_xy = []

for point in reference["reference_points"]:

    x, y = gps_to_xy(
        point["lat"],
        point["lon"],
        origin_lat,
        origin_lon
    )

    reference_xy.append(
        {
            "name": point["name"],
            "x": x,
            "y": y
        }
    )


# ======================
# PLOT
# ======================

plt.figure(figsize=(10, 10))


# Racing line
plt.plot(
    lap["X"],
    lap["Y"],
    linewidth=2,
    label="iRacing Racing Line"
)


# Start finish origin
plt.scatter(
    0,
    0,
    c="red",
    s=80,
    label="Start Finish"
)


# Google Earth reference points
for point in reference_xy:

    plt.scatter(
        point["x"],
        point["y"],
        c="orange",
        s=60
    )

    plt.text(
        point["x"],
        point["y"],
        point["name"],
        fontsize=8
    )


plt.axis("equal")
plt.grid(True)

plt.xlabel("X metres")
plt.ylabel("Y metres")

plt.title("Okayama GPS Coordinate Validation")

plt.legend()

plt.show()