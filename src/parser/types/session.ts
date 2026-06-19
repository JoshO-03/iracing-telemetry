export type TelemetryValue = string | number | boolean;

export type TelemetrySample = {
  sampleIndex: number;
  [key: string]: TelemetryValue;
};

export type TelemetrySession = {
  metadata: {
    trackName?: string;
    trackDisplayName?: string;
    trackConfigName?: string;
    trackLength?: string;
  };

  samples: TelemetrySample[];
};