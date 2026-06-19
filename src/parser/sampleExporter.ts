import { TelemetrySample } from "./types/session";

export const exportToCSV = (
  wantedHeaders: string[],
  samples: TelemetrySample[]
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

  return csvRows;
};