// Data transfer utilities never open paths or choose storage destinations.
export class TransportError extends Error {}
export type Row = Record<string, unknown>;

export function readJsonLines(text: string): Row[] {
  const result: Row[] = [];
  for (const [index, line] of text.split(/\r?\n/).entries()) {
    if (!line.trim()) continue;
    let row: unknown;
    try { row = JSON.parse(line); }
    catch { throw new TransportError(`invalid JSON on line ${index + 1}`); }
    if (row === null || typeof row !== "object" || Array.isArray(row)) throw new TransportError(`expected object on line ${index + 1}`);
    result.push(row as Row);
  }
  return result;
}

export function jsonLines(rows: readonly Row[]): string {
  return rows.map((row) => JSON.stringify(row) + "\n").join("");
}

export function csvCell(value: unknown): string {
  const text = value === null || value === undefined ? "" : String(value);
  return /[",\r\n]/.test(text) ? '"' + text.replaceAll('"', '""') + '"' : text;
}

export function csv(rows: readonly Row[], fields: readonly string[]): string {
  return [fields.map(csvCell).join(","), ...rows.map((row) => fields.map((f) => csvCell(row[f])).join(","))].join("\n") + "\n";
}

export function htmlEscape(text: string): string {
  return text.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#39;");
}

export function htmlTable(rows: readonly Row[], fields: readonly string[], caption: string): string {
  const head = fields.map((f) => '<th scope="col">' + htmlEscape(f) + "</th>").join("");
  const body = rows.map((row) => "<tr>" + fields.map((f) => "<td>" + htmlEscape(String(row[f] ?? "")) + "</td>").join("") + "</tr>").join("");
  return "<table><caption>" + htmlEscape(caption) + "</caption><thead><tr>" + head + "</tr></thead><tbody>" + body + "</tbody></table>";
}

export function page(rows: readonly Row[], offset: number, limit: number): Row[] {
  if (!Number.isSafeInteger(offset) || offset < 0 || !Number.isSafeInteger(limit) || limit < 0) throw new TransportError("invalid page bounds");
  return structuredClone(rows.slice(offset, offset + limit));
}

export function project(rows: readonly Row[], fields: readonly string[]): Row[] {
  return rows.map((row) => Object.fromEntries(fields.filter((f) => Object.hasOwn(row, f)).map((f) => [f, structuredClone(row[f])])));
}

export function histogram(rows: readonly Row[], field: string): { label: string; count: number }[] {
  const counts = new Map<string, number>();
  for (const row of rows) {
    const label = String(row[field] ?? "");
    counts.set(label, (counts.get(label) ?? 0) + 1);
  }
  return [...counts].sort(([a], [b]) => a.localeCompare(b)).map(([label, count]) => ({ label, count }));
}
