import { Header } from "../types/header";
import { VarHeader } from "../types/var-header";
import { getString, getValue } from "./valueReader";

const VAR_HEADER_SIZE = 144;


export const readVarHeader = (buffer: Buffer, header: Header): VarHeader[] => {
  const numberOfVariables = header.numVars;

  return Array.from(Array(numberOfVariables).keys()).map((index: number) => {
    const start = index * VAR_HEADER_SIZE;

    return {
      type: getValue(buffer, start),
      offset: getValue(buffer, start + 4),
      count: getValue(buffer, start + 8),
      countAsTime: getValue(buffer, start + 12, "int8"),
      name: getString(buffer, start + 16, 32),
      description: getString(buffer, start + 16 + 32, 64),
      unit: getString(buffer, start + 16 + 32 + 64, 32),
    };
  });
};