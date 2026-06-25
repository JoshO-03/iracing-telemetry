import { Session, Lap, TelemetrySample, Corner} from "../types/session";
import { CornerPerformance, SessionAnalysis, BrakingPerformance, AccelPerformance, SteeringPerformance } from "../types/lap-analysis";
import { getTrackModel } from "./utils";
import { TrackModel } from "../types/track";
import { Sample } from "../types/sample";

const parseLaps = (session: Session): SessionAnalysis | null => {
    const trackModel = getTrackModel(String(session.info.TrackID));

    if (!trackModel) {
        throw new Error(`Track model for ID ${session.info.TrackID} not found.`);
    }
    return null;
}

const getLapAnalysis = (lap: Lap[], trackModel: TrackModel) => {

}

export const getCornerAnalysis = (
    lap: Lap,
    trackModel: TrackModel | null
): CornerPerformance | null => {
    if (!trackModel) {
        console.error("Track model is null. Cannot perform corner analysis.");
        return null;
    }

    const cornerTelemetry: Corner[] = trackModel.corners.map(corner => ({
        cornerId: corner.cornerId,
        samples: [] as TelemetrySample[],
    }));

    for (const sample of lap.samples) {
        const distPct = Number(sample.LapDistPct);

        const cornerIndex = trackModel.corners.findIndex(
            corner =>
                distPct >= corner.startDistPct &&
                distPct <= corner.endDistPct
        );

        if (cornerIndex === -1) {
            continue;
        }

        cornerTelemetry[cornerIndex].samples.push(sample);
    }

    const brakingPerformance = detectBreakingPerformance(cornerTelemetry);
    const accelPerformance = detectAccelPerformance(cornerTelemetry);

    console.log("Accel Performance:", accelPerformance);

    return null;
};


const detectBreakingPerformance = (cornerTelemetry: Corner[]): BrakingPerformance[] | null => {
    const brakingPerformance: BrakingPerformance[] =[];
    for(const corner of cornerTelemetry) {
        for (const sample of corner.samples) {
            const brakePedal = Number(sample.Brake);
            const cornerObj = brakingPerformance.find(braking => braking.cornerId === corner.cornerId);
            if(brakePedal > 0) {
                if(cornerObj) {
                    cornerObj.brakingStartPct = Number(sample.LapDistPct);
                }else{
                    brakingPerformance.push({
                        cornerId: corner.cornerId,
                        brakingStartPct: Number(sample.LapDistPct),
                        brakingEndPct: 0
                    });
                }
            }else{
                if(cornerObj) {
                    cornerObj.brakingEndPct = Number(sample.LapDistPct);
                }
            }
        }
    }
    return brakingPerformance;
}

const detectAccelPerformance = (cornerTelemetry: Corner[]): AccelPerformance[] | null => {
    // Implement logic to detect acceleration performance based on cornerTelemetry
    const accelPerformance: AccelPerformance[] = [];
    for(const corner of cornerTelemetry) {
        for (const sample of corner.samples) {
            const throttlePedal = Number(sample.Throttle);
            const cornerObj = accelPerformance.find(accel => accel.cornerId === corner.cornerId);
            if(throttlePedal > 0) {
                if(cornerObj) {
                    cornerObj.accelStartPct = Number(sample.LapDistPct);
                }else{
                    accelPerformance.push({
                        cornerId: corner.cornerId,
                        accelStartPct: Number(sample.LapDistPct),
                        fullAccelPct: 0
                    });
                }
            }else{
                if(cornerObj) {
                    cornerObj.fullAccelPct = Number(sample.LapDistPct);
                }
            }
        }
    }
    return accelPerformance;
}

const detectSteeringPerformance = (cornerTelemetry: Corner[]): SteeringPerformance[] | null => {
    // Implement logic to detect steering performance based on cornerTelemetry
    return null;
}