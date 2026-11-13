/** CSV projection for user exports, with RFC-style doubled quotes. */
export function cell(value: string): string {
  return /[,"\r\n]/u.test(value) ? '"'+value.replaceAll('"','""')+'"' : value;
}
export function encodeCsv(rows: readonly (readonly string[])[]): string {
  return rows.map(row => row.map(cell).join(",")).join("\r\n")+"\r\n";
}
export function decodeCsv(raw: string): string[][] {
  const rows: string[][] = [];
  let row: string[] = [];
  let value = "";
  let quoted = false;
  let closed = false;
  for (let i=0;i<raw.length;i++) {
    const character = raw[i];
    if (quoted) {
      if (character === '"') {
        if (raw[i+1] === '"') { value += '"'; i++; }
        else { quoted = false; closed = true; }
      } else value += character;
      continue;
    }
    if (character === '"' && value === "" && !closed) { quoted = true; continue; }
    if (character === ",") { row.push(value); value = ""; closed = false; continue; }
    if (character === "\r" || character === "\n") {
      if (character === "\r" && raw[i+1] === "\n") i++;
      row.push(value); rows.push(row); row = []; value = ""; closed = false; continue;
    }
    if (closed || character === '"') throw new Error("invalid character after CSV quote");
    value += character;
  }
  if (quoted) throw new Error("unterminated CSV quote");
  if (value || row.length || closed) { row.push(value); rows.push(row); }
  return rows;
}
