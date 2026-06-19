export interface Header {
  readonly version: number;
  readonly status: number;
  readonly tickRate: number;
  readonly sessionInfoUpdate: number;
  readonly sessionInfoLength: number;
  readonly sessionInfoOffset: number;
  readonly numVars: number;
  readonly varHeaderOffset: number;
  readonly numBuf: number;
  readonly bufLen: number;
  readonly bufOffset: number;
}
