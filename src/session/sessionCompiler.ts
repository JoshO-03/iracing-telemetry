import { Lap, Session } from "../types/session";

const getSessionInfoValue = (sessionData: string, key: string): string => {
    const line = sessionData
        .split(/\r?\n/)
        .find((sessionInfoLine) => sessionInfoLine.trimStart().startsWith(`${key}:`));

    return line?.split(/:(.*)/s)[1]?.trim() ?? "";
};

const parseDistanceMeters = (distanceText: string): number => {
    const match = distanceText.match(/^([\d.]+)\s*([a-zA-Z]+)?/);
    if (!match) {
        return 0;
    }

    const value = Number(match[1]);
    const unit = match[2]?.toLowerCase();

    if (unit === "km") {
        return value * 1000;
    }

    return value;
};

const getDriverBlock = (sessionData: string, carIdx: number): string => {
    const lines = sessionData.split(/\r?\n/);
    const startIndex = lines.findIndex(
        (line) => line.trim() === `- CarIdx: ${carIdx}`
    );

    if (startIndex === -1) {
        return "";
    }

    const blockLines = [lines[startIndex]];

    for (let i = startIndex + 1; i < lines.length; i++) {
        if (lines[i].trimStart().startsWith("- CarIdx:")) {
            break;
        }

        blockLines.push(lines[i]);
    }

    return blockLines.join("\n");
};

export const compileSession = (laps: Lap[], sessionData: string): Session => {

    //Metadata
    const trackName = getSessionInfoValue(sessionData, "TrackName");
    const trackId = Number(getSessionInfoValue(sessionData, "TrackID"));
    const trackSessionLengthMeters = parseDistanceMeters(getSessionInfoValue(sessionData, "TrackLength"));
    const driverCarIdx = Number(getSessionInfoValue(sessionData, "DriverCarIdx"));
    const driverBlock = getDriverBlock(sessionData, driverCarIdx);
    const carName = getSessionInfoValue(driverBlock, "CarScreenName");
    const driverName = getSessionInfoValue(driverBlock, "UserName");
    const sessionType = getSessionInfoValue(sessionData, "SessionType");

    //Summary
    const sampleCount = laps.reduce((acc, lap) => acc + lap.sampleCount, 0);
    const lapCount = laps.length;
    const validLapCount = laps.filter((lap) => lap.isValid).length;
    const completeLapCount = laps.filter((lap) => lap.isComplete).length;
    const validLapTimes = laps
        .filter((lap) => lap.isValid)
        .map((lap) => lap.lapTimeSeconds);
    const fastestLapTimeSeconds = validLapTimes.length > 0
        ? Math.min(...validLapTimes)
        : 0;
    const fastestLapNumber = laps.findIndex((lap) => lap.lapTimeSeconds === fastestLapTimeSeconds);
    const sessionStartTimeSeconds = laps[0]?.startSessionTimeSeconds ?? 0;
    const sessionEndTimeSeconds = laps[laps.length - 1]?.endSessionTimeSeconds ?? 0;
    const durationSeconds = sessionEndTimeSeconds - sessionStartTimeSeconds;

    return {
        trackModelRef: {
            trackName,
            trackId,
            trackModelVersion: 1 // Assuming a default version
        },
        metadata: {
            trackSessionLengthMeters,
            carName,
            driverName,
            sessionType
        },
        laps: laps,
        summary: {
            sampleCount,
            lapCount,
            validLapCount,
            completeLapCount,
            fastestLapTimeSeconds,
            sessionStartTimeSeconds,
            sessionEndTimeSeconds,
            durationSeconds,
            fastestLapNumber
        }
    }
};
