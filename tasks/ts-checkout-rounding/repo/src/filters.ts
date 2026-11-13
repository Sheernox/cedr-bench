// Saved report filters are JSON-compatible, validated before reading any rows.
import type { Row } from "./transport.ts";
export type Filter =
  | { all: Filter[] }
  | { any: Filter[] }
  | { not: Filter }
  | { field: string; op: "eq" | "contains" | "range"; value: unknown };
export class FilterError extends Error {}

export function compile(filter: Filter, depth = 0): (row: Row) => boolean {
  if (depth > 20 || filter === null || typeof filter !== "object") throw new FilterError("invalid filter");
  if ("all" in filter) {
    const children = filter.all.map((x) => compile(x, depth + 1));
    return (row) => children.every((test) => test(row));
  }
  if ("any" in filter) {
    const children = filter.any.map((x) => compile(x, depth + 1));
    return (row) => children.some((test) => test(row));
  }
  if ("not" in filter) {
    const child = compile(filter.not, depth + 1);
    return (row) => !child(row);
  }
  const { field, op, value } = structuredClone(filter);
  if (!/^[A-Za-z_][A-Za-z_0-9]*$/.test(field)) throw new FilterError("invalid field");
  if (op === "eq") return (row) => Object.hasOwn(row, field) && row[field] === value;
  if (op === "contains") {
    if (typeof value !== "string") throw new FilterError("contains needs text");
    return (row) => typeof row[field] === "string" && row[field].toLowerCase().includes(value.toLowerCase());
  }
  if (op === "range") {
    if (!Array.isArray(value) || value.length !== 2 || !value.every(Number.isSafeInteger) || value[0] > value[1]) throw new FilterError("invalid range");
    const [lo, hi] = value as [number, number];
    return (row) => typeof row[field] === "number" && row[field] >= lo && row[field] <= hi;
  }
  throw new FilterError("unsupported operation");
}

export function select(rows: readonly Row[], filter: Filter): Row[] {
  return structuredClone(rows.filter(compile(filter)));
}

export interface View { name: string; filter: Filter; pageSize: number; }
export class Views {
  private values = new Map<string, View>();
  add(view: View, replace = false): void {
    compile(view.filter);
    if (!view.name || !Number.isInteger(view.pageSize) || view.pageSize < 1 || view.pageSize > 1000) throw new FilterError("invalid view");
    if (this.values.has(view.name) && !replace) throw new FilterError("duplicate view");
    this.values.set(view.name, structuredClone(view));
  }
  get(name: string): View {
    const view = this.values.get(name);
    if (!view) throw new FilterError("unknown view");
    return structuredClone(view);
  }
  list(): View[] {
    return [...this.values.values()].sort((a, b) => a.name.localeCompare(b.name)).map((v) => structuredClone(v));
  }
  remove(name: string): void {
    if (!this.values.delete(name)) throw new FilterError("unknown view");
  }
}
