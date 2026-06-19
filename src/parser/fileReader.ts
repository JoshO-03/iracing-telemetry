import { readSync } from "fs";

export const fileToBuffer =  (
  file: number,
  start: number,
  length: number
): Buffer => {
  const buffer = Buffer.alloc(length);
  const bufferLength = readSync(file, buffer, 0, length, start);

  if (bufferLength === 0) {
    throw new Error("End of file reached");
  }

  return buffer;
};