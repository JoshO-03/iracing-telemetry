import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

df = pd.read_csv("data/telemetry.csv")


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
        start = event["startdist"]
        stop = event["enddist"]

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
            if not brakeApplicationDist or brakeApplicationDist[-1]["enddist"] is not None:
                brakeApplicationDist.append({"startdist": sample.LapDistPct, "enddist": None})
        else:
            if brakeApplicationDist and brakeApplicationDist[-1]["enddist"] is None:
                brakeApplicationDist[-1]["enddist"] = sample.LapDistPct
    

    if brakeApplicationDist and brakeApplicationDist[-1]["enddist"] is None:
        brakeApplicationDist[-1]["enddist"] = float(lap.iloc[-1]["LapDistPct"])

    return brakeApplicationDist

def detectThrottleApplication(df, lap_number):
    throttleApplicationDist = []
    lap = df[df["Lap"] == lap_number].copy()
    for sample in lap.itertuples():

        if sample.Throttle < .95:
            if not throttleApplicationDist or throttleApplicationDist[-1]["enddist"] is not None:
                throttleApplicationDist.append({"startdist": sample.LapDistPct, "enddist": None})
        else:
            if throttleApplicationDist and throttleApplicationDist[-1]["enddist"] is None:
                throttleApplicationDist[-1]["enddist"] = sample.LapDistPct

    if throttleApplicationDist and throttleApplicationDist[-1]["enddist"] is None:
        throttleApplicationDist[-1]["enddist"] = float(lap.iloc[-1]["LapDistPct"])
    
    return throttleApplicationDist

def detectSteeringInput(df, lap_number):
    #Todo: Smooth out data values to account of steering corrections and small adjustments. This will help to avoid false positives in detecting steering input.
    steeringInputDist = []
    lap = df[df["Lap"] == lap_number].copy()
    peakSteeringAngle = 0
    peakSteeringDist = 0
    for sample in lap.itertuples():

        if abs(sample.SteeringWheelAngle) > .4:
            if not steeringInputDist or steeringInputDist[-1]["enddist"] is not None:
                steeringInputDist.append({"startdist": sample.LapDistPct, "enddist": None})
                if abs(sample.SteeringWheelAngle) > peakSteeringAngle:
                    peakSteeringAngle = abs(sample.SteeringWheelAngle)
                    peakSteeringDist = sample.LapDistPct
        else:
            if steeringInputDist and steeringInputDist[-1]["enddist"] is None:
                print("called")
                steeringInputDist[-1]["enddist"] = sample.LapDistPct
                steeringInputDist[-1]["peakSteeringAngle"] = peakSteeringAngle
                steeringInputDist[-1]["peakSteeringDist"] = peakSteeringDist
                peakSteeringAngle = 0
                peakSteeringDist = 0
    
    return steeringInputDist

#print(detectBrakeApplication(df, 3))
print(detectThrottleApplication(df, 3))
print(detectSteeringInput(df, 3))
showGraph(df, 3, detectSteeringInput(df, 3), type="SteeringWheelAngle")