import { TelemetrySample, Lap, Session } from "./types/session";
const segmentLaps = (samples: TelemetrySample[]): Lap[] => {
    const laps : Lap[] = [];
    samples.forEach((sample) => {
        
        let lapFound = false
        laps.forEach((lap) => {
            if (lap.lapNumber === sample.Lap) {
                lap.samples.push(sample);
                lapFound = true;
            }
        })

        if (!lapFound) {
            const newLap : Lap = {
                lapNumber: Number(sample["Lap"]),
                samples: [sample]
            }
            laps.push(newLap);
        }

    })
    return laps;
}


export const compileSession = (samples: TelemetrySample[]): Session => {
    const laps = segmentLaps(samples);
    const session : Session = {
        laps: laps
    }

    return session;
}