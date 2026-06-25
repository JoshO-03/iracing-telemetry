import { openSync, writeFileSync } from "fs";
import { DiskSubHeader } from "../types/disk-sub-header";
import { fileToBuffer } from "./fileReader";
import { getValue } from "./valueReader";
import { readHeader } from "./headerReader";
import { readVarHeader } from "./varHeaderReader";
import { readSamples } from "./sampleReader";
import { exportToCSV } from "./sampleExporter";
import { compileSession } from "./sessionCompiler";
import { getTrackModel } from "../analysis/utils";
import yaml from "yaml";
import { Session, SessionInfo } from "../types/session";
import { getCornerAnalysis } from "../analysis/SessionParser";

const HEADER_LENGTH = 112;
const DISK_SUB_HEADER_LENGTH = 32;
const VAR_HEADER_SIZE = 144;
const wantedHeaders = [
  "SessionTime",
  "SessionTick",
  "Lap",
  "LapCompleted",
  "LapDist",
  "LapDistPct",
  "LapCurrentLapTime",
  "LapLastLapTime",
  "LapBestLapTime",
  "Speed",
  "Throttle",
  "Brake",
  "SteeringWheelAngle",
  "Gear",
  "RPM",
  "LatAccel",
  "LongAccel",
  "YawRate",
  "IsOnTrack",
  "OnPitRoad",
  "PlayerCarPosition",
  "Lat",
  "Lon",
  "Alt",
  "Yaw",
  "VelocityX",
  "VelocityY",
  "VelocityZ",
  "LapBestLapTime",
  "LapLastLapTime",
  "LapDeltaToBestLap",
  "LapDeltaToOptimalLap"
];

const wantedSessionInfo = [
  "TrackID",
  "TrackName",
  "TrackDisplayName",
  "TrackLength"
]


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


const parseIBT = (path: string) =>  {
  const telemetryFile = openSync(path, "r");

  const headerBuffer = fileToBuffer(telemetryFile, 0, HEADER_LENGTH);
  const header = readHeader(headerBuffer);

  const diskSubHeaderBuffer = fileToBuffer(
    telemetryFile,
    HEADER_LENGTH,
    DISK_SUB_HEADER_LENGTH
  );
  const diskSubHeader = readDiskSubHeader(diskSubHeaderBuffer);

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


  const samples = readSamples(header, telemetryFile, usefulVarHeaders, wantedHeaders);

  const laps = [...new Set(samples.map(sample => sample.Lap))];

  for (const lap of [0, 1, 2, 3, 4]) {
    const lapSamples = samples.filter(s => s.Lap === lap);

}


  return { samples, sessionInfo };



}

const getSessionFromIBT = (path: string) : Session => {
  const data = parseIBT(path);

  const info = yaml.parse(data.sessionInfo);

  const trackInfo = Object.fromEntries(
      wantedSessionInfo.map(field => [
          field,
          info.WeekendInfo[field]
      ])
  ) as SessionInfo;

  const session = compileSession(data.samples, trackInfo);

  console.log(session.info.TrackID);
  return session;
}

async function main() {
    const samples = parseIBT("data/telemetry.ibt");
    const session = getSessionFromIBT("data/telemetry.ibt");

    getCornerAnalysis(session.laps[2], await getTrackModel(String(session.info.TrackID)));



    console.log(`Read ${samples.samples.length} samples from telemetry.ibt`);

}

main();