import { compileLaps } from "./lapCompiler";
import { compileSession } from "./sessionCompiler";
import { Session } from "../types/session";
import { IBTParseResult } from "../parser/parseIBT";

export const getSession = (result: IBTParseResult, sessionData: string): Session => {
    const laps = compileLaps(result);
    return compileSession(laps, sessionData);
};