import { IBTParseResult } from "../parser/parseIBT";
import { TelemetrySample, Lap } from "../types/session";

const MIN_COMPLETE_LAP_SECONDS = 20;

const toNumber = (value: TelemetrySample[keyof TelemetrySample]): number => {
    if (typeof value === "number") {
        return value;
    }

    if (typeof value === "string") {
        return Number(value);
    }

    return value ? 1 : 0;
};

const buildLap = (lapNumber: number, lapSamples: TelemetrySample[]): Lap => {
    const firstSample = lapSamples[0];
    const lastSample = lapSamples[lapSamples.length - 1];

    const startLapDistPct = toNumber(firstSample.lapDistPct);
    const endLapDistPct = toNumber(lastSample.lapDistPct);
    const lapTimeSeconds =
        toNumber(lastSample.sessionTimeSeconds) - toNumber(firstSample.sessionTimeSeconds);
    const invalidReasons: string[] = [];

    const hasFullLapDistanceRange = startLapDistPct <= 0.05 && endLapDistPct >= 0.95;
    const hasPlausibleDuration = lapTimeSeconds >= MIN_COMPLETE_LAP_SECONDS;
    const isLapZero = lapNumber <= 0;
    const isComplete = hasFullLapDistanceRange && hasPlausibleDuration && !isLapZero;

    if (!isComplete) {
        invalidReasons.push("incomplete_lap");
    }

    if (isLapZero) {
        invalidReasons.push("lap_zero");
    }

    if (!hasPlausibleDuration) {
        invalidReasons.push("too_short");
    }

    return {
        lapNumber,
        samples: lapSamples,
        startSessionTimeSeconds: toNumber(firstSample.sessionTimeSeconds),
        endSessionTimeSeconds: toNumber(lastSample.sessionTimeSeconds),
        startLapDistPct,
        endLapDistPct,
        isComplete,
        isValid: invalidReasons.length === 0,
        invalidReasons,
        sampleCount: lapSamples.length,
        lapTimeSeconds,
    };
};

export const compileLaps = (result: IBTParseResult): Lap[] => {
    const samples = result.samples;
    const laps: Lap[] = [];
    let currentLapNumber: number | null = null;
    let lapSamples: TelemetrySample[] = [];

    for (const sample of samples) {
        const sampleLapNumber = toNumber(sample.lapNumber);

        if (currentLapNumber === null) {
            currentLapNumber = sampleLapNumber;
        }

        if (sampleLapNumber !== currentLapNumber) {
            laps.push(buildLap(currentLapNumber, lapSamples));
            currentLapNumber = sampleLapNumber;
            lapSamples = [];
        }

        lapSamples.push(sample);
    }

    if (currentLapNumber !== null && lapSamples.length > 0) {
        laps.push(buildLap(currentLapNumber, lapSamples));
    }

    return laps;
};
