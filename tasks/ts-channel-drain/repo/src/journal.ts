import type { Write } from "./types.ts";
/** Portable journal frames; consumers can reject truncated tails. */
export function encode(write: Write): string {
  return JSON.stringify({kind:"save",...write}) + "\n";
}
export function decode(line: string): Write {
  const row: unknown = JSON.parse(line);
  if (typeof row !== "object" || row === null) throw new Error("invalid frame");
  if (!("kind" in row) || row.kind !== "save" || !("key" in row) || typeof row.key !== "string" ||
      !("value" in row) || typeof row.value !== "string" || !("generation" in row) ||
      typeof row.generation !== "number" || !Number.isSafeInteger(row.generation) || row.generation < 1) {
    throw new Error("invalid save frame");
  }
  return {key:row.key,value:row.value,generation:row.generation};
}
export function replay(raw: string): Map<string,Write> {
  const records = new Map<string,Write>();
  if (raw && !raw.endsWith("\n")) throw new Error("truncated journal");
  for (const line of raw.split("\n")) {
    if (!line) continue;
    const row = decode(line);
    const previous = records.get(row.key);
    if (!previous || row.generation >= previous.generation) records.set(row.key,row);
  }
  return records;
}
