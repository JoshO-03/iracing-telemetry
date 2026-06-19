import { VarHeader } from "./types/var-header";
import { getString, getValue } from "./valueReader";

export const getSampleValue = (
  sampleBuffer: Buffer,
  variable: VarHeader
): string | number | boolean => {
  if (variable.type === 0) {
    return getString(sampleBuffer, variable.offset, 1);
  }

  if (variable.type === 1) {
    return getValue(sampleBuffer, variable.offset, "int8") === 1;
  }

  if (variable.type === 2) {
    return getValue(sampleBuffer, variable.offset, "int32");
  }

  if (variable.type === 3) {
    return getValue(sampleBuffer, variable.offset, "bit");
  }

  if (variable.type === 4) {
    return getValue(sampleBuffer, variable.offset, "float");
  }

  if (variable.type === 5) {
    return getValue(sampleBuffer, variable.offset, "double");
  }

  return "";
};