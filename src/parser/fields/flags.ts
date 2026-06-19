export const Flags = {
  // global flags
  checkered: 1 << 0,
  white: 2 << 0,
  green: 4 << 0,
  yellow: 8 << 0,
  red: 1 << 1,
  blue: 2 << 1,
  debris: 4 << 1,
  crossed: 8 << 1,
  yellowWaving: 1 << 2,
  oneLapToGreen: 2 << 2,
  greenHeld: 4 << 2,
  tenToGo: 8 << 2,
  fiveToGo: 1 << 3,
  randomWaving: 2 << 3,
  caution: 4 << 3,
  cautionWaving: 8 << 3,

  // drivers black flags
  black: 1 << 4,
  disqualify: 2 << 4,
  servicible: 4 << 4, // car is allowed service (not a flag)
  furled: 8 << 4,
  repair: 1 << 5,

  // start lights
  startHidden: 1 << 7,
  startReady: 2 << 7,
  startSet: 4 << 7,
  startGo: 8 << 7,
};

export const EngineFlags = {
  waterTempWarning: 1 << 0,
  fuelPressureWarning: 2 << 0,
  oilPressureWarning: 4 << 0,
  engineStalled: 8 << 0,
  pitSpeedLimiter: 1 << 1,
  revLimiterActive: 2 << 1,
};

export const PitServiceFlags = {
  LFTireChange: 1 << 0,
  RFTireChange: 2 << 0,
  LRTireChange: 4 << 0,
  RRTireChange: 8 << 0,
  FuelFill: 1 << 1,
  WindshieldTearoff: 2 << 1,
  FastRepair: 4 << 1,
};
