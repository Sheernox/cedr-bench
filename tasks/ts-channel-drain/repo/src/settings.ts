import { object, parse, integer, strings, stable } from "./json-value.ts";
/** User preferences do not configure the storage scheduler's correctness. */
export interface Settings {
  tabSize: number;
  wrap: boolean;
  theme: "light" | "dark" | "system";
  recent: string[];
  autosave: boolean;
}
export function defaults(): Settings {
  return {tabSize:2,wrap:true,theme:"system",recent:[],autosave:true};
}
export function decodeSettings(raw: string): Settings {
  const row = object(parse(raw));
  const base = defaults();
  const tabSize = row.tabSize === undefined ? base.tabSize : integer(row.tabSize,"tabSize");
  if (tabSize < 1 || tabSize > 16) throw new Error("tab size out of range");
  const theme = row.theme ?? base.theme;
  if (theme !== "light" && theme !== "dark" && theme !== "system") throw new Error("unknown theme");
  const wrap = row.wrap ?? base.wrap;
  const autosave = row.autosave ?? base.autosave;
  if (typeof wrap !== "boolean" || typeof autosave !== "boolean") throw new Error("invalid boolean preference");
  return {tabSize,theme,wrap,autosave,recent:row.recent === undefined ? [] : strings(row.recent,"recent")};
}
export function encodeSettings(settings: Settings): string {
  return stable({...settings,recent:[...settings.recent]})+"\n";
}
export function remember(settings: Settings,id: string,limit = 10): Settings {
  if (!Number.isInteger(limit) || limit < 0) throw new RangeError("invalid recent limit");
  return {...settings,recent:[id,...settings.recent.filter(value => value !== id)].slice(0,limit)};
}
