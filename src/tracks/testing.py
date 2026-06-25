import pandas as pd
import matplotlib.pyplot as plt
import sys


# ======================
# CONFIG
# ======================

CSV_FILE = "data/telemetry.csv"
LAP = 3


# Allow command line override
if len(sys.argv) > 1:
    CSV_FILE = sys.argv[1]

if len(sys.argv) > 2:
    LAP = int(sys.argv[2])


print("=" * 50)
print("GPS TRACK TEST")
print("=" * 50)
print(f"CSV: {CSV_FILE}")
print(f"Lap: {LAP}")
print("=" * 50)


# ======================
# LOAD TELEMETRY
# ======================

df = pd.read_csv(CSV_FILE)

lap = df[df["Lap"] == LAP].copy()

if lap.empty:
    raise Exception(f"No data found for lap {LAP}")


lat = lap["Lat"]
lon = lap["Lon"]


print(f"Samples: {len(lap)}")
print(f"Latitude range: {lat.min()} - {lat.max()}")
print(f"Longitude range: {lon.min()} - {lon.max()}")


# ======================
# PLOT GPS TRACK
# ======================

plt.figure(figsize=(8, 8))

plt.plot(
    lon,
    lat,
    linewidth=2,
    label=f"Lap {LAP}"
)

# Mark start point
plt.scatter(
    lon.iloc[0],
    lat.iloc[0],
    color="green",
    s=80,
    label="Start"
)

# Mark end point
plt.scatter(
    lon.iloc[-1],
    lat.iloc[-1],
    color="red",
    s=80,
    label="End"
)


plt.xlabel("Longitude")
plt.ylabel("Latitude")

plt.title("iRacing GPS Track Plot")

plt.axis("equal")
plt.grid(True)
plt.legend()

plt.show()