import matplotlib.pyplot as plt
import numpy as np


def generate_track_map(df, corners, lap_number=3):

    # Select lap
    df = df[df["Lap"] == lap_number].copy()

    df = df[
        (df["Lat"] != 0) &
        (df["Lon"] != 0)
    ].copy()

    if len(df) == 0:
        print("No valid data")
        return


    # Coordinates
    lon = df["Lon"].values
    lat = df["Lat"].values


    # Plot base track
    plt.figure(figsize=(10,10))

    plt.plot(
        lon,
        lat,
        linewidth=2,
        label="Racing Line"
    )


    # Corner colouring
    for i, corner in enumerate(corners):

        section = df[
            (df["LapDistPct"] >= corner["startdist"]) &
            (df["LapDistPct"] <= corner["enddist"])
        ]

        if len(section) == 0:
            continue


        plt.plot(
            section["Lon"],
            section["Lat"],
            linewidth=5,
            label=f"Corner {i+1}"
        )


    plt.axis("equal")
    plt.legend()
    plt.title("Track Map")

    plt.show()