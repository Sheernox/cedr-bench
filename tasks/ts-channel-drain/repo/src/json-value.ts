/** JSON-only state prevents editor exports from depending on object identity. */
export type Json = null | boolean | number | string | Json[] | { [key: string]: Json };
export function isJson(value: unknown, seen = new Set<object>()): value is Json {
  if (value === null || typeof value === "string" || typeof value === "boolean") return true;
  if (typeof value === "number") return Number.isFinite(value);
  if (typeof value !== "object" || seen.has(value)) return false;
  seen.add(value);
  try {
    if (Array.isArray(value)) return value.every(item => isJson(item,seen));
    if (Object.getPrototypeOf(value) !== Object.prototype) return false;
    return Object.values(value).every(item => isJson(item,seen));
  } finally {
    seen.delete(value);
  }
}
export function clone(value: Json): Json {
  if (value === null || typeof value !== "object") return value;
  if (Array.isArray(value)) return value.map(clone);
  return Object.fromEntries(Object.entries(value).map(([key,item]) => [key,clone(item)]));
}
export function stable(value: Json): string {
  if (value === null || typeof value !== "object") return JSON.stringify(value);
  if (Array.isArray(value)) return "[" + value.map(stable).join(",") + "]";
  return "{" + Object.keys(value).sort().map(key => JSON.stringify(key)+":"+stable(value[key])).join(",") + "}";
}
export function parse(raw: string): Json {
  const value: unknown = JSON.parse(raw);
  if (!isJson(value)) throw new ValueError("not JSON state");
  return value;
}
export class ValueError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ValueError";
  }
}
export function object(value: Json): { [key: string]: Json } {
  if (value === null || typeof value !== "object" || Array.isArray(value)) throw new ValueError("expected object");
  return value;
}
export function string(value: Json | undefined, field: string): string {
  if (typeof value !== "string") throw new ValueError(field+": expected string");
  return value;
}
export function integer(value: Json | undefined, field: string): number {
  if (typeof value !== "number" || !Number.isSafeInteger(value)) throw new ValueError(field+": expected integer");
  return value;
}
export function strings(value: Json | undefined, field: string): string[] {
  if (!Array.isArray(value) || !value.every(item => typeof item === "string")) throw new ValueError(field+": expected strings");
  return value;
}
