import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

df = pd.read_csv("data/telemetry.csv")

def showTrackMap(df, lap_number, corners):
    lap = df[df["Lap"] == lap_number].copy()

    plt.figure(figsize=(10, 10))

    # Plot full track
    plt.plot(
        lap["PositionX"],
        lap["PositionY"],
        color="black",
        alpha=0.3,
        label="Track"
    )

    # Plot detected corners
    for i, corner in enumerate(corners):
        corner_data = lap[
            (lap["LapDistPct"] >= corner["startDistPct"]) &
            (lap["LapDistPct"] <= corner["endDistPct"])
        ]

        plt.plot(
            corner_data["PositionX"],
            corner_data["PositionY"],
            linewidth=4,
            label=f"Corner {i+1}"
        )

        # Add corner number at start
        if not corner_data.empty:
            start = corner_data.iloc[0]

            plt.text(
                start["PositionX"],
                start["PositionY"],
                str(i+1),
                fontsize=12
            )

    plt.title(f"Detected Corners - Lap {lap_number}")
    plt.xlabel("Position X")
    plt.ylabel("Position Y")

    plt.axis("equal")
    plt.grid(True)

    plt.legend()
    plt.show()


def showGraph(df, lap_number, data, type="Speed"):
    lap = df[df["Lap"] == lap_number].copy()

    if type == "Speed":
        lap["Speed"] = lap["Speed"] * 3.6

    plt.plot(lap["LapDistPct"], lap[type], label=f"Lap {lap_number}")

    plt.xlabel("Lap Distance %")
    plt.ylabel(f"{type}")
    plt.title(f"{type} Trace Comparison")
    plt.legend()

    for event in data:
        start = event["startDistPct"]
        stop = event["endDistPct"]

        plt.axvspan(start, stop if stop else 1.0, color='gray', alpha=0.3)

    plt.show()

def showTelemetryOverview(df, lap_number):
    lap = df[df["Lap"] == lap_number].copy()

    # Normalise signals
    speed = lap["Speed"] / lap["Speed"].max()
    brake = lap["Brake"]
    throttle = lap["Throttle"]

    steering = lap["SteeringWheelAngle"].abs()
    steering = steering / steering.max()

    plt.figure(figsize=(15, 6))

    plt.plot(lap["LapDistPct"], speed, label="Speed")
    plt.plot(lap["LapDistPct"], brake, label="Brake")
    plt.plot(lap["LapDistPct"], throttle, label="Throttle")
    plt.plot(lap["LapDistPct"], steering, label="|Steering|")

    plt.xlabel("Lap Distance %")
    plt.ylabel("Normalised Value")
    plt.title(f"Telemetry Overview - Lap {lap_number}")

    plt.legend()
    plt.grid(True)

    plt.show()

def detectBrakeApplication(df, lap_number):
    brakeApplicationDist = []
    lap = df[df["Lap"] == lap_number].copy()
    for sample in lap.itertuples():

        if sample.Brake > 0:
            if not brakeApplicationDist or brakeApplicationDist[-1]["endDistPct"] is not None:
                brakeApplicationDist.append({"startDistPct": sample.LapDistPct, "endDistPct": None})
        else:
            if brakeApplicationDist and brakeApplicationDist[-1]["endDistPct"] is None:
                brakeApplicationDist[-1]["endDistPct"] = sample.LapDistPct
    

    if brakeApplicationDist and brakeApplicationDist[-1]["endDistPct"] is None:
        brakeApplicationDist[-1]["endDistPct"] = float(lap.iloc[-1]["LapDistPct"])

    return brakeApplicationDist

def detectThrottleApplication(df, lap_number):
    throttleApplicationDist = []
    lap = df[df["Lap"] == lap_number].copy()
    for sample in lap.itertuples():

        if sample.Throttle < .95:
            if not throttleApplicationDist or throttleApplicationDist[-1]["endDistPct"] is not None:
                throttleApplicationDist.append({"startDistPct": sample.LapDistPct, "endDistPct": None})
        else:
            if throttleApplicationDist and throttleApplicationDist[-1]["endDistPct"] is None:
                throttleApplicationDist[-1]["endDistPct"] = sample.LapDistPct

    if throttleApplicationDist and throttleApplicationDist[-1]["endDistPct"] is None:
        throttleApplicationDist[-1]["endDistPct"] = float(lap.iloc[-1]["LapDistPct"])
    
    return throttleApplicationDist

def detectSteeringInput(df, lap_number,threshold=0.4, min_steering_duration=0.01):
    #Todo: Smooth out data values to account of steering corrections and small adjustments. This will help to avoid false positives in detecting steering input.
    steeringInputDist = []
    lap = df[df["Lap"] == lap_number].copy()
    peakSteeringAngle = 0
    peakSteeringDist = 0
    for sample in lap.itertuples():

        if abs(sample.SteeringWheelAngle) > threshold:
            if not steeringInputDist or steeringInputDist[-1]["endDistPct"] is not None:
                steeringInputDist.append({"startDistPct": sample.LapDistPct, "endDistPct": None})
            if abs(sample.SteeringWheelAngle) > peakSteeringAngle:
                peakSteeringAngle = abs(sample.SteeringWheelAngle)
                peakSteeringDist = sample.LapDistPct
        else:
            if steeringInputDist and steeringInputDist[-1]["endDistPct"] is None:
                steeringInputDist[-1]["endDistPct"] = sample.LapDistPct
                steeringInputDist[-1]["peakSteeringAngle"] = peakSteeringAngle
                steeringInputDist[-1]["peakSteeringDist"] = peakSteeringDist
                peakSteeringAngle = 0
                peakSteeringDist = 0
        
        if steeringInputDist:
            steeringInputDist[-1]["peakSteeringDist"] = peakSteeringDist
    
    steeringInputDist = [event for event in steeringInputDist if event.get("endDistPct") and event["endDistPct"] - event["startDistPct"] >= min_steering_duration]

    return steeringInputDist

def detectSpeedChange(df, lap_number, threshold = 0.0001):
    speedChangeDist = []
    previousSpeed = 0
    lap = df[df["Lap"] == lap_number].copy()
    minSpeedDist = None
    minSpeed = float('inf')
    
    for sample in lap.itertuples():
        if sample.Speed - previousSpeed < threshold:
            # Speed is decreasing or flat
            if not speedChangeDist or speedChangeDist[-1]["endDistPct"] is not None:
                speedChangeDist.append({"startDistPct": sample.LapDistPct, "endDistPct": None})
                minSpeedDist = sample.LapDistPct
                minSpeed = sample.Speed
            else:
                # Track minimum speed within this event
                if sample.Speed < minSpeed:
                    minSpeed = sample.Speed
                    minSpeedDist = sample.LapDistPct
        else:
            # Speed is increasing - end current event
            if speedChangeDist and speedChangeDist[-1]["endDistPct"] is None:
                speedChangeDist[-1]["endDistPct"] = sample.LapDistPct
                speedChangeDist[-1]["minSpeedDist"] = minSpeedDist
                minSpeedDist = None
                minSpeed = float('inf')
            
        previousSpeed = sample.Speed

    # Handle last event if it's still open
    if speedChangeDist and speedChangeDist[-1]["endDistPct"] is None:
        speedChangeDist[-1]["endDistPct"] = float(lap.iloc[-1]["LapDistPct"])
        speedChangeDist[-1]["minSpeedDist"] = minSpeedDist
    
    return speedChangeDist

def detectCorners(df, lap_number, gap_threshold=0.005, min_corner_length=0.002):
    lap = df[df["Lap"] == lap_number].copy()
    lap_end = float(lap.iloc[-1]["LapDistPct"])

    rawData = [
        {"data": detectSteeringInput(df, lap_number)},
        {"data": detectBrakeApplication(df, lap_number)},
        {"data": detectThrottleApplication(df, lap_number)},
    ]

    all_ranges = []

    for item in rawData:
        for event in item["data"]:
            startDistPct = float(event["startDistPctPct"])
            endDistPct = float(event["endDistPctPct"]) if event["endDistPctPct"] is not None else lap_end
            all_ranges.append({
                "startDistPct": startDistPct,
                "endDistPct": endDistPct,
            })

    if not all_ranges:
        return []

    all_ranges.sort(key=lambda x: x["startDistPctPct"])

    corners = []
    corner_id = 1
    current = all_ranges[0].copy()

    for event in all_ranges[1:]:
        if event["startDistPctPct"] <= current["endDistPct"] + gap_threshold:
            current["endDistPct"] = max(current["endDistPct"], event["endDistPct"])
        else:
            if current["endDistPct"] - current["startDistPctPct"] >= min_corner_length:
                # Find apex distance (minimum speed point within corner)
                corner_data = lap[
                    (lap["LapDistPct"] >= current["startDistPctPct"]) &
                    (lap["LapDistPct"] <= current["endDistPctPct"])
                ]
                if not corner_data.empty:
                    min_speed_idx = corner_data["Speed"].idxmin()
                    apex_dist = corner_data.loc[min_speed_idx, "LapDistPct"]
                    current["apexDistPct"] = round(apex_dist, 4)
                else:
                    current["apexDistPct"] = None
                
                
                current["cornerId"] = corner_id
                corner_id += 1
                corners.append(current)
            current = event.copy()

    if current["endDistPct"] - current["startDistPctPct"] >= min_corner_length:
        # Find apex distance for last corner
        corner_data = lap[
            (lap["LapDistPct"] >= current["startDistPctPct"]) &
            (lap["LapDistPct"] <= current["endDistPct"])
        ]
        if not corner_data.empty:
            min_speed_idx = corner_data["Speed"].idxmin()
            apex_dist = corner_data.loc[min_speed_idx, "LapDistPct"]
            current["apexDistPct"] = round(apex_dist, 4)
        else:
            current["apexDistPct"] = None
        
        current["cornerId"] = corner_id
        corners.append(current)

    return corners

lap3 = df[df["Lap"] == 3].copy()
corners = detectCorners(df, 3)
for corner in corners:
    print(corner["startDistPct"], corner["endDistPctPct"], corner.get("apexDistPct"))