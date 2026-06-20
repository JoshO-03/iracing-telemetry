import { AnalysableSample, TelemetrySample } from "../types/session";

export const convertToAnalysableSample = (
    sample: TelemetrySample | undefined
): AnalysableSample | undefined => {

    if (!sample) {
        return undefined;
    }

    if (
        sample["Lap"] === undefined ||
        sample["LapDist"] === undefined ||
        sample["Speed"] === undefined ||
        sample["SteeringWheelAngle"] === undefined
    ) {
        return undefined;
    }

    const analysableSample: AnalysableSample = {
        sampleIndex: Number(sample["sampleIndex"]),
        Lap: Number(sample["Lap"]),
        LapDist: Number(sample["LapDist"]),
        Speed: Number(sample["Speed"]),
        SteeringWheelAngle: Number(sample["SteeringWheelAngle"])
    };

    return analysableSample;
};