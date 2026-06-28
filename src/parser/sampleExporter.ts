import { TelemetrySampleRaw } from "../types/session";
import { mkdirSync, writeFileSync } from "fs";

export const exportToCSV = (
  wantedHeaders: string[],
  samples: TelemetrySampleRaw[]
): string[] => {
  const csvHeaders = ["sampleIndex", ...wantedHeaders];
  const csvRows: string[] = [];

  csvRows.push(csvHeaders.join(","));

  for (const sample of samples) {
    const csvLine = csvHeaders
      .map((headerName) => sample[headerName] ?? "")
      .join(",");

    csvRows.push(csvLine);
  }

  mkdirSync("data", { recursive: true });
  writeFileSync("data/telemetry.csv", csvRows.join("\n"));

  return csvRows;
};
