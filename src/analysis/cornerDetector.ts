import { AnalysableSample, Lap, TelemetrySample } from "../types/session";
import { Corner } from "../types/lap-components";
import { convertToAnalysableSample } from "./utils";

export const detectSpeedChange = (lap: Lap | undefined, threshold: number = 0.5) => {
    if (!lap) {
        console.log("No lap provided");
        return [];
    }
    let previousSpeed = 0
    let speed_changes = []
    let inCorner = false;

    const samples = lap.samples
        .map(convertToAnalysableSample)
        .filter((sample): sample is AnalysableSample => sample !== undefined);

    for (const sample of samples) {
        const speed = sample.Speed;
        
        if (previousSpeed > 0 && speed < previousSpeed) {
            // in a corner
            if(speed_changes.length === 0 || inCorner === false) {
                speed_changes.push({
                    startdist: sample.LapDist,
                    enddist: 0
                });
                inCorner = true;
            }else{
                if (speed_changes.length > 0 && speed_changes[speed_changes.length - 1].enddist === 0 && sample.LapDist - speed_changes[speed_changes.length - 1].startdist > 0.03) {
                    speed_changes[speed_changes.length - 1].enddist = sample.LapDist;
                    inCorner = false;
                }
            }
        }
        previousSpeed = speed;
    }
    return speed_changes;
}

// const detectCorners = (lap: Lap) : Corner[] =>  {

// }