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

export type Session = {
  trackName: string;
  laps : Lap[];
}

export type Lap = {
  lapNumber: number;
  samples: TelemetrySample[];
}

export type TrackModel = {
  trackName: string;
  sectors: Sector[];
  corners: Corner[];
};

export type Sector = {
  startDistPct: number;
  endDistPct: number;
  sectorId?: number;
};

export type Corner = {
  startDistPct: number;
  endDistPct: number;
  apexDistPct: number;
  cornerId?: number;
};