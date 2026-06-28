import { TelemetrySample, TelemetrySampleRaw } from "../types/session";
import { rawToNormalizedChannelMap } from "./telemetryChannels";

export const normalizeSamples = (
  rawSamples: TelemetrySampleRaw[]
): TelemetrySample[] => {
  return rawSamples.map((rawSample) => {
    const normalizedSample = {
      sampleIndex: rawSample.sampleIndex,
    } as TelemetrySample;

    for (const [rawName, normalizedName] of Object.entries(
      rawToNormalizedChannelMap
    )) {
      normalizedSample[normalizedName] = rawSample[rawName];
    }

    return normalizedSample;
  });
};
