import type { Document } from "./document.ts";
import { encodeDocument } from "./document.ts";
import { stable } from "./json-value.ts";
import { encodeCsv } from "./csv.ts";
/** Human projections are intentionally distinct from lossless workspace exports. */
export type Format = "json" | "csv" | "markdown" | "text";
export function exportDocuments(documents: readonly Document[],format: Format): string {
  if (format === "json") return stable(documents.map(encodeDocument))+"\n";
  if (format === "csv") return encodeCsv([
    ["ID","Title","Text","Tags","Archived"],
    ...documents.map(document => [document.id,document.title,document.text,document.tags.join(";"),String(document.archived)]),
  ]);
  if (format === "markdown") return documents.map(document => "# "+document.title+"\n\n"+document.text).join("\n\n")+"\n";
  return documents.map(document => document.title+"\n"+document.text).join("\n\n")+"\n";
}
export function countWords(text: string): number {
  return text.trim() ? text.trim().split(/\s+/u).length : 0;
}
export function describe(document: Document): {characters: number; words: number; lines: number; bytes: number} {
  return {characters:[...document.text].length,words:countWords(document.text),
    lines:document.text.split("\n").length,bytes:Buffer.byteLength(document.text,"utf8")};
}
