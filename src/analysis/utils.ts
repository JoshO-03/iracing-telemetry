import { TrackModel } from "../types/track";
import path from "path";
import { readFile } from "fs/promises";

export async function loadJsonFile<T>(filePath: string): Promise<T | null> {
  try {
    const fileContents = await readFile(filePath, "utf-8");
    return JSON.parse(fileContents) as T;
  } catch (err: any) {
    // File not found OR invalid JSON OR permission issue
    if (err.code === "ENOENT") {
      return null; // file doesn't exist
    }

    // If JSON is malformed, this is actually useful to crash early
    if (err instanceof SyntaxError) {
      throw new Error(`Invalid JSON in file: ${filePath}`);
    }

    // Unknown error (permissions, disk issues, etc.)
    throw err;
  }
}

export const getTrackModel = async (trackName: string): Promise<TrackModel | null> => {
    const filePath = path.join(
    process.cwd(),
        "src",
        "tracks",
        "models",
        `${trackName}.json`
    );

    console.log(filePath);

    // Open track model file and return the corresponding model
    const track = await loadJsonFile<TrackModel>(
    filePath
    );

    if (!track) {
        console.error(`Track model for ${trackName} not found.`);
        return null;
    }

    const trackModel: TrackModel = {
        trackName: trackName,
        sectors: track.sectors,
        corners: track.corners,
    };

    
    return trackModel;

}