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

writeFileSync(
  "data/varHeaders.txt",
  varHeader
    .map(v => v.name)
    .filter(name => name.toLowerCase())
    .join("\n")
);


  const samples = readSamples(header, telemetryFile, usefulVarHeaders, wantedHeaders);

  const laps = [...new Set(samples.map(sample => sample.Lap))];

  for (const lap of [0, 1, 2, 3, 4]) {
    const lapSamples = samples.filter(s => s.Lap === lap);

    console.log(
        "Lap:",
        lap,
        "Samples:",
        lapSamples.length,
        "Start LapDistPct:",
        lapSamples[0]?.LapDistPct,
        "End LapDistPct:",
        lapSamples[lapSamples.length - 1]?.LapDistPct
    );
}


  return samples;



}

async function main() {
    const samples = parseIBT("data/telemetry.ibt");
    //const laps = segmentLaps(samples);
    //const lap2 = laps.find((lap) => lap.lapNumber === 2);
    
    //console.log(lap2);
//     for (let sample of samples) {
//       console.log(sample.Lat, sample.Lon
// )
//     }

    console.log(`Read ${samples.length} samples from telemetry.ibt`);
    console.log(await getTrackModel("okayama"));
    // const session = compileSession(samples);
    // //console.log(session["laps"].find((lap) => lap.lapNumber === 4));
    // const csvRows = exportToCSV(wantedHeaders, samples);

    // writeFileSync("data/telemetry.csv", csvRows.join("\n"));

    // console.log(`Exported ${csvRows.length - 1} samples to telemetry.csv`);

}

main();