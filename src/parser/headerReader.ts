import { Header } from "./types/header";
import { getValue } from "./valueReader";

export const readHeader = (buffer: Buffer): Header => {
  return {
    version: getValue(buffer, 0),
    status: getValue(buffer, 4),
    tickRate: getValue(buffer, 8),
    sessionInfoUpdate: getValue(buffer, 12),
    sessionInfoLength: getValue(buffer, 16),
    sessionInfoOffset: getValue(buffer, 20),
    numVars: getValue(buffer, 24),
    varHeaderOffset: getValue(buffer, 28),
    numBuf: getValue(buffer, 32),
    bufLen: getValue(buffer, 36),
    bufOffset: getValue(buffer, 52),
  };
};