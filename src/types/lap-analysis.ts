export type BrakingPerformance = {
    cornerId: number;
    brakingStartPct : number;
    brakingEndPct : number;
}

export type AccelPerformance = {
    cornerId: number;
    accelStartPct: number;
    fullAccelPct: number;
}

export type SteeringPerformance = {
    cornerId: number;
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