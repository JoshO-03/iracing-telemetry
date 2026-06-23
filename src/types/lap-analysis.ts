export type BrakingPerformance = {
    brakingStartPct : number;
    brakingEndPct : number;
}

export type AccelPerformance = {
    accelStartPct: number;
    fullAccelPct: number;
}

export type SteeringPerformance = {
    steeringStartPct: number;
    maxAngle: number;
    maxSteeringPct: number;
}

export type CornerPerformance = {
    cornerId: number;
    exitSpeed: number;
    minimumSpeed: number;
    brakingPerformance: BrakingPerformance;
    accelPerformance: AccelPerformance;
    steeringPerformance: SteeringPerformance;
}

export type LapAnalysis = {
    lapNumber: number;
    lapTime: number;
    isLapValid: boolean;
    corners: CornerPerformance[];
}

export type SessionAnalysis = {
    trackName: string;
    lapAnalyses: LapAnalysis[];
}