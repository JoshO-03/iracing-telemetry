export type TelemetryValue = string | number | boolean;

export type TelemetrySample = {
    sampleIndex: number;
    [key: string]: TelemetryValue;
};
