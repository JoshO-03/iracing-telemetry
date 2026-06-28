export type TelemetryValue = string | number | boolean;

export type TelemetrySampleRaw = {
    sampleIndex: number;
    [key: string]: TelemetryValue;
};

export type TelemetrySample = {
    sampleIndex: number;
    sessionTimeSeconds: TelemetryValue;
    sessionTick: TelemetryValue;
    isOnTrack: TelemetryValue;
    playerTrackSurface: TelemetryValue;
    onPitRoad: TelemetryValue;
    steeringWheelAngleRadians: TelemetryValue;
    throttle: TelemetryValue;
    brake: TelemetryValue;
    clutch: TelemetryValue;
    gear: TelemetryValue;
    rpm: TelemetryValue;
    lapNumber: TelemetryValue;
    lapCompleted: TelemetryValue;
    lapDistMeters: TelemetryValue;
    lapDistPct: TelemetryValue;
    speedMetersPerSecond: TelemetryValue;
    yawRate: TelemetryValue;
    latAccel: TelemetryValue;
    longAccel: TelemetryValue;
};

export type Lap = {
    lapNumber: number;
    samples: TelemetrySample[];
    startSessionTimeSeconds: number;
    endSessionTimeSeconds: number;
    startLapDistPct: number;
    endLapDistPct: number;
    isComplete: boolean;
    isValid: boolean;
    invalidReasons: string[];
    sampleCount: number;
    lapTimeSeconds: number;
}

export type Session = {
    trackModelRef: {
        trackName: string;
        trackId: number;
        trackModelVersion: number;
    }
    metadata: {
        trackSessionLengthMeters: number;
        carName: string;
        driverName: string;
        sessionType: string;
    }
    laps: Lap[];
    summary: {
        sampleCount: number;
        lapCount: number;
        validLapCount: number;
        completeLapCount: number;
        fastestLapTimeSeconds: number;
        fastestLapNumber: number;
        sessionStartTimeSeconds: number;
        sessionEndTimeSeconds: number;
        durationSeconds: number;
    }
}
