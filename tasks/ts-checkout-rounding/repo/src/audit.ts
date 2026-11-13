// Receipt hashes detect accidental modifications, and do not replace signatures.
import { createHash } from "node:crypto";
export interface Receipt { index: number; action: string; timestamp: string; details: Record<string, unknown>; previous: string; digest: string; }
export class AuditError extends Error {}

export function canonical(value: unknown): string {
  if (Array.isArray(value)) return "[" + value.map(canonical).join(",") + "]";
  if (value !== null && typeof value === "object") {
    const object = value as Record<string, unknown>;
    return "{" + Object.keys(object).sort().map((key) => JSON.stringify(key) + ":" + canonical(object[key])).join(",") + "}";
  }
  const encoded = JSON.stringify(value);
  if (encoded === undefined || typeof value === "number" && !Number.isFinite(value)) throw new AuditError("not a JSON value");
  return encoded;
}
export function digest(value: unknown): string {
  return createHash("sha256").update(canonical(value)).digest("hex");
}

export class Audit {
  private receipts: Receipt[] = [];
  append(action: string, details: Record<string, unknown>, timestamp: string): Receipt {
    if (!action || !/(?:Z|[+-]\d\d:\d\d)$/.test(timestamp) || !Number.isFinite(Date.parse(timestamp))) throw new AuditError("action and ISO timestamp required");
    const body = { index: this.receipts.length, action, details: structuredClone(details), timestamp, previous: this.receipts.at(-1)?.digest ?? "" };
    const receipt = { ...body, digest: digest(body) };
    this.receipts.push(receipt);
    return structuredClone(receipt);
  }
  export(): Receipt[] { return structuredClone(this.receipts); }
  static restore(rows: readonly Receipt[]): Audit {
    const audit = new Audit();
    for (const row of rows) {
      const generated = audit.append(row.action, row.details, row.timestamp);
      if (canonical(generated) !== canonical(row)) throw new AuditError("invalid audit chain");
    }
    return audit;
  }
  filter(action: string): Receipt[] {
    return structuredClone(this.receipts.filter((row) => row.action === action));
  }
}
