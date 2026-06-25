import { TrackModel } from "../types/track";
import { readFileSync } from "fs";
export const getTrackModel = (trackID: number): TrackModel | null => {
    // Implementation for fetching track model based on trackID
    const trackConfig = JSON.parse(readFileSync(`tracks/models/${trackID}.json`, "utf-8"));
    if (!trackConfig) {
        console.error(`Track model for ID ${trackID} not found.`);
        return null;
    }

    const trackModel: TrackModel = {
        trackName: trackConfig.trackName,
        corners: trackConfig.corners,
    };

    return trackModel;
}