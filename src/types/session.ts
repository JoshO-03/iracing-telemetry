export type TelemetryValue = string | number | boolean;

export type TelemetrySample = {
    sampleIndex: number;
    [key: string]: TelemetryValue;
};

export type SessionInfo = {
  TrackID: number;
  TrackName: string;
  TrackDisplayName: string;
  TrackLength: string;
}

export type Session = {
  info: SessionInfo;
  laps : Lap[];
}

export type Lap = {
  lapNumber: number;
  samples: TelemetrySample[];
}

export type Corner = {
  cornerId: number;
  samples: TelemetrySample[];
}

export type Driver = {

}
