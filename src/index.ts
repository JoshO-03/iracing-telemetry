import { parseIBT } from "./parser/parseIBT";
import { exportToCSV } from "./parser/sampleExporter";
import { normalizedHeaders } from "./parser/telemetryChannels";
import { compileLaps } from "./session/lapCompiler";
import { getSession } from "./session/main";

const main = () => {
  const data = parseIBT("data/telemetry.ibt");

  const laps = compileLaps(data);
  const session = getSession(data, data.sessionInfo);
  console.log(session);
  exportToCSV(normalizedHeaders, data.samples);

  console.log(`Read ${data.samples.length} samples from telemetry.ibt`);
};

main();

// getLaps -> getSession