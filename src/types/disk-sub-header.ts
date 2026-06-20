export interface DiskSubHeader {
  readonly sessionStartDate: Date;
  readonly startTime: number;
  readonly endTime: number;
  readonly lapCount: number;
  readonly recordCount: number;
}
