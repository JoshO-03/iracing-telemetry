export const getValue = (
  buffer: Buffer,
  start: number,
  type: "int8" | "int32" | "float" | "double" | "bit" = "int32"
): number => {
  switch (type) {
    case "int8":
      return buffer.subarray(start, start + 1).readInt8();

    case "int32":
      return buffer.subarray(start, start + 4).readInt32LE();

    case "float":
      return buffer.subarray(start, start + 4).readFloatLE();

    case "double":
      return buffer.subarray(start, start + 8).readDoubleLE();

    case "bit":
      return buffer.subarray(start, start + 4).readUInt32LE();
  }
};

export const getString = (buffer: Buffer, start: number, length: number): string => {
  return buffer
    .subarray(start, start + length)
    .toString("ascii")
    .replace(/\0/g, "");
};