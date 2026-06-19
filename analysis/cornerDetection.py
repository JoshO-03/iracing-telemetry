import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

df = pd.read_csv("telemetry.csv")


def showGraph(df, lap_number, data, type="Speed"):
    lap = df[df["Lap"] == lap_number].copy()
    if type == "Speed":
        lap["Speed"] = lap["Speed"] * 3.6
    plt.plot(lap["LapDistPct"], lap[type], label=f"Lap {lap_number}")

    plt.xlabel("Lap Distance %")
    plt.ylabel(f"{type}")
    plt.title(f"{type} Trace Comparison")
    plt.legend()

    for start, stop in data:
        plt.axvspan(start, stop if stop else 1.0, color='gray', alpha=0.3)

    plt.show()


def detect_speed_change(df, lap_number, threshold=0.5):
    previousSpeed = 0
    speed_changes = []
    
    for dist in np.arange(0, 1.0, 0.002):
        speed1 = df[(df["Lap"] == lap_number) & (df["LapDistPct"] >= dist)].iloc[0]["Speed"] * 3.6
        

        if previousSpeed > 0 and speed1 < previousSpeed:
            # In a corner
            if not speed_changes or inCorner == False: # if we are entering a new corner
                speed_changes.append([float(dist), True])
                inCorner = True
        else:
            # Not in a corner
            if speed_changes and speed_changes[-1][1] == True and dist - speed_changes[-1][0] > 0.03: # if we are exiting a corner
                speed_changes[-1][1] = float(dist)
                inCorner = False
        
        previousSpeed = speed1
    return speed_changes


def detect_steering_change_old(df, lap_number, debug=False, threshold=0.5):
    previousSteering = []
    steering_changes = []

    for dist in np.arange(0, 1.0, 0.002):
        steering1 = df[(df["Lap"] == lap_number) & (df["LapDistPct"] >= dist)].iloc[0]["SteeringWheelAngle"]

        previousSteering.append([float(dist), float(steering1)])


        if len(previousSteering) == 10:
            if abs(previousSteering[0][1] - previousSteering[-1][1]) < threshold:
                # In a corner
                steering_changes.append([previousSteering[0][0], previousSteering[-1][0]])
            previousSteering = []
                
    if debug:
        showGraph(df, lap_number, steering_changes, type="SteeringWheelAngle")

    return steering_changes


def detect_steering_change(df, lap_number, debug=False, threshold=0.5):
    steering_changes = []
    inCorner = False
    for dist in np.arange(0, 1.0, 0.001):
        steering1 = df[
            (df["Lap"] == lap_number) &
            (df["LapDistPct"] >= dist)
        ].iloc[0]["SteeringWheelAngle"]

        if abs(steering1) > threshold:
            if not inCorner:
                cornerStart = float(dist)
                inCorner = True
        else:
            if inCorner:
                steering_changes.append([cornerStart, float(dist)])
                inCorner = False
    

    if len(steering_changes[-1]) == 1:
        steering_changes[-1].append(1.0)

    if debug:
        showGraph(df, lap_number, steering_changes, type="SteeringWheelAngle")
    
    return steering_changes


def detect_corner(df, lap_number, debug=False):
    speed_changes = detect_speed_change(df, lap_number)
    steering_changes = detect_steering_change(df, lap_number)

    corners = []
    for speed_start, speed_end in speed_changes:
        for steer_start, steer_end in steering_changes:
            if (steer_start <= speed_start <= steer_end) or (steer_start <= speed_end <= steer_end):
                corners.append([speed_start, speed_end])
                break

    if debug:
        showGraph(df, lap_number, corners, type="Speed")

    return corners

detect_corner(df, 1, debug=True)