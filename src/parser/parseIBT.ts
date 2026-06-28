import { openSync, writeFileSync } from "fs";
import { DiskSubHeader } from "../types/disk-sub-header";
import { TelemetrySample, TelemetrySampleRaw } from "../types/session";
import { fileToBuffer } from "./fileReader";
import { getValue } from "./valueReader";
import { readHeader } from "./headerReader";
import { readVarHeader } from "./varHeaderReader";
import { readSamples } from "./sampleReader";
import { normalizeSamples } from "./normalizeSamples";
import { wantedHeaders } from "./telemetryChannels";

const HEADER_LENGTH = 112;
const DISK_SUB_HEADER_LENGTH = 32;
const VAR_HEADER_SIZE = 144;

type RawIBTParseResult = {
  samples: TelemetrySampleRaw[];
  sessionInfo: string;
};

export type IBTParseResult = {
  samples: TelemetrySample[];
  sessionInfo: string;
};

const readDiskSubHeader = (buffer: Buffer): DiskSubHeader => {
  const sessionStartDate = getValue(buffer, 0);

  return {
    sessionStartDate: new Date(sessionStartDate * 1000),
    startTime: getValue(buffer, 8, "double"),
    endTime: getValue(buffer, 16, "double"),
    lapCount: getValue(buffer, 24),
    recordCount: getValue(buffer, 28),
  };
};

export const parseIBTRaw = (path: string): RawIBTParseResult => {
  const telemetryFile = openSync(path, "r");

  const headerBuffer = fileToBuffer(telemetryFile, 0, HEADER_LENGTH);
  const header = readHeader(headerBuffer);

  const diskSubHeaderBuffer = fileToBuffer(
    telemetryFile,
    HEADER_LENGTH,
    DISK_SUB_HEADER_LENGTH
  );
  readDiskSubHeader(diskSubHeaderBuffer);

  const sessionInfoBuffer = fileToBuffer(
    telemetryFile,
    header.sessionInfoOffset,
    header.sessionInfoLength
  );

  const sessionInfo = sessionInfoBuffer.toString("ascii");
  writeFileSync("data/sessionInfo.txt", sessionInfo);

  const varHeaderBuffer = fileToBuffer(
    telemetryFile,
    header.varHeaderOffset,
    header.numVars * VAR_HEADER_SIZE
  );

  const varHeader = readVarHeader(varHeaderBuffer, header);
  const usefulVarHeaders = varHeader.filter((variable) =>
    wantedHeaders.includes(variable.name)
  );

  const samples = readSamples(
    header,
    telemetryFile,
    usefulVarHeaders,
    wantedHeaders
  );

  return { samples, sessionInfo };
};

export const parseIBT = (path: string): IBTParseResult => {
  const rawSession = parseIBTRaw(path);

  return {
    samples: normalizeSamples(rawSession.samples),
    sessionInfo: rawSession.sessionInfo,
  };
};
