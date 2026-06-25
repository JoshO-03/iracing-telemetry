import pandas as pd
import json
import math


# ======================
# CONFIG
# ======================

CSV_FILE = "data/telemetry.csv"
REFERENCE_FILE = "src/tracks/models/okayama_reference.json"

LAP = 3


# ======================
# DISTANCE FUNCTION
# ======================

def gps_distance(lat1, lon1, lat2, lon2):
    """
    Approximate distance between two GPS coordinates in metres
    """

    lat_diff = (lat2 - lat1) * 111320
    lon_diff = (lon2 - lon1) * 111320 * math.cos(math.radians(lat1))

    return math.sqrt(
        lat_diff ** 2 +
        lon_diff ** 2
    )


# ======================
# LOAD DATA
# ======================

df = pd.read_csv(CSV_FILE)

lap = df[df["Lap"] == LAP].copy()

if lap.empty:
    raise Exception(f"No telemetry found for lap {LAP}")


with open(REFERENCE_FILE) as f:
    reference = json.load(f)


print("=" * 60)
print("TRACK POINT VALIDATION")
print("=" * 60)

print(f"Lap samples: {len(lap)}")
print(f"Reference points: {len(reference['reference_points'])}")

print("=" * 60)


# ======================
# CHECK EACH POINT
# ======================

for point in reference["reference_points"]:

    target_lat = point["lat"]
    target_lon = point["lon"]

    closest_distance = float("inf")
    closest_sample = None


    for _, sample in lap.iterrows():

        distance = gps_distance(
            target_lat,
            target_lon,
            sample["Lat"],
            sample["Lon"]
        )

        if distance < closest_distance:
            closest_distance = distance
            closest_sample = sample


    print()
    print(point["name"])

    print(
        f"  Google Earth: "
        f"{target_lat:.6f}, {target_lon:.6f}"
    )

    print(
        f"  iRacing:      "
        f"{closest_sample['Lat']:.6f}, "
        f"{closest_sample['Lon']:.6f}"
    )

    print(
        f"  Error:        "
        f"{closest_distance:.2f} metres"
    )


print()
print("=" * 60)
print("Finished")
print("=" * 60)