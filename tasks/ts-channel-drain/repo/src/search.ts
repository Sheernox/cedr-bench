import type { Document } from "./document.ts";
/** Tokenized text search supports quoted phrases without executing expressions. */
export interface Term { text: string; excluded: boolean; field: "title" | "text" | "tags" | null }
export function tokenize(raw: string): Term[] {
  const words: string[] = [];
  let current = "";
  let quoted = false;
  let escape = false;
  for (const character of raw) {
    if (escape) { current += character; escape = false; continue; }
    if (character === "\\" && quoted) { escape = true; continue; }
    if (character === '"') { quoted = !quoted; continue; }
    if (/\s/u.test(character) && !quoted) {
      if (current) words.push(current);
      current = "";
    } else current += character;
  }
  if (quoted || escape) throw new Error("unterminated quoted filter");
  if (current) words.push(current);
  return words.map(word => {
    const excluded = word.startsWith("-");
    const value = excluded ? word.slice(1) : word;
    const colon = value.indexOf(":");
    if (colon < 0) return {text:value,excluded,field:null};
    const field = value.slice(0,colon);
    if (field !== "title" && field !== "text" && field !== "tags") throw new Error("unknown filter field");
    if (!value.slice(colon+1)) throw new Error("empty filter value");
    return {text:value.slice(colon+1),excluded,field};
  });
}
export function matches(document: Document,terms: readonly Term[]): boolean {
  return terms.every(term => {
    const values = term.field === "tags" ? document.tags : term.field ? [document[term.field]] :
      [document.title,document.text,...document.tags];
    const found = values.some(value => value.toLocaleLowerCase("en-US").includes(term.text.toLocaleLowerCase("en-US")));
    return found !== term.excluded;
  });
}
export function search(documents: readonly Document[],raw: string): Document[] {
  const terms = tokenize(raw);
  return documents.filter(document => matches(document,terms)).map(document => ({...document,tags:[...document.tags]}));
}
