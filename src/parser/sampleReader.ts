import { Header } from "../types/header";
import { fileToBuffer } from "./fileReader";
import { VarHeader } from "../types/var-header";
import { getSampleValue } from "./sampleValueReader";
import { TelemetrySample } from "../types/session";



export const readSamples = (header: Header, telemetryFile: number, usefulVarHeaders: VarHeader[], wantedHeaders: string[]) => {

    

    let sample = 0;
    let endOfSamplesReached = false;
    const samples: TelemetrySample[] = [];

    while (!endOfSamplesReached) {
    const start = header.bufOffset + sample * header.bufLen;

    try {
        const sampleBuffer = fileToBuffer(
        telemetryFile,
        start,
        header.bufLen
        );

        const row: TelemetrySample = {
            sampleIndex: sample,
        };


        usefulVarHeaders.forEach((variable) => {
            row[variable.name] = getSampleValue(sampleBuffer, variable);
        });

        samples.push(row);

        sample++;
    } catch (err) {
        endOfSamplesReached = true;
    }
    }

    return samples;
}