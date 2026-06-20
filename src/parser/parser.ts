import { openSync, writeFileSync } from "fs";
import { DiskSubHeader } from "../types/disk-sub-header";
import { fileToBuffer } from "./fileReader";
import { getValue } from "./valueReader";
import { readHeader } from "./headerReader";
import { readVarHeader } from "./varHeaderReader";
import { readSamples } from "./sampleReader";
import { exportToCSV } from "./sampleExporter";
import { compileSession } from "./sessionCompiler";
import { detectSpeedChange } from "../analysis/cornerDetector";

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
  ];


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

  // const sessionInfoBuffer = await fileToBuffer(
  //   telemetryFile,
  //   header.sessionInfoOffset,
  //   header.sessionInfoLength
  // );

  //const sessionInfo = sessionInfoBuffer.toString("ascii");

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

  return samples;



}

function main() {
    const samples = parseIBT("data/telemetry.ibt");
    //const laps = segmentLaps(samples);
    //const lap2 = laps.find((lap) => lap.lapNumber === 2);

    //console.log(lap2);

    const session = compileSession(samples);
    //console.log(session["laps"].find((lap) => lap.lapNumber === 4));
    console.log(detectSpeedChange(session["laps"].find((lap) => lap.lapNumber === 4)));
    const csvRows = exportToCSV(wantedHeaders, samples);

    writeFileSync("data/telemetry.csv", csvRows.join("\n"));

    console.log(`Exported ${csvRows.length - 1} samples to telemetry.csv`);

}

main();