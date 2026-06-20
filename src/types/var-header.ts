export interface VarHeader {
  readonly type: number;
  readonly offset: number;
  readonly count: number;
  readonly countAsTime: number;
  readonly name: string;
  readonly description: string;
  readonly unit: string;
}
