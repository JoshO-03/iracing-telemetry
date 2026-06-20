export type TelemetryValue = string | number | boolean;

export type TelemetrySample = {
    sampleIndex: number;
    [key: string]: TelemetryValue;
};

export type AnalysableSample = {
    sampleIndex: number;
    Lap: number;
    LapDist: number;
    Speed: number;
    SteeringWheelAngle: number;
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

export type Session = {
  laps : Lap[];
}

export type Lap = {
  lapNumber: number;
  samples: TelemetrySample[];
}