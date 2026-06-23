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