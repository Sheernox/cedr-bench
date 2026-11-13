// Historical receipts are immutable snapshots, independently of current prices.
import type { Quote } from "./checkout.ts";
import { formatReceipt } from "./receipt.ts";
export class InvalidHistoryError extends Error {}

function object(value: unknown): Record<string, unknown> {
  if (value === null || typeof value !== "object" || Array.isArray(value)) throw new InvalidHistoryError("expected object");
  return value as Record<string, unknown>;
}
function amount(value: unknown): number {
  if (typeof value !== "number" || !Number.isSafeInteger(value)) throw new InvalidHistoryError("expected whole cents");
  return value;
}
function text(value: unknown): string {
  if (typeof value !== "string") throw new InvalidHistoryError("expected text");
  return value;
}

export function readHistoricalQuote(value: unknown): Quote {
  const source = object(value);
  if (!Array.isArray(source.lines) || !Array.isArray(source.coupons)) throw new InvalidHistoryError("missing lines or coupons");
  const lines = source.lines.map((raw: unknown) => {
    const line = object(raw);
    const quantity = amount(line.quantity);
    if (quantity < 0) throw new InvalidHistoryError("negative quantity");
    if (line.promotion !== null && typeof line.promotion !== "string") throw new InvalidHistoryError("invalid promotion");
    return { sku: text(line.sku), name: text(line.name), quantity,
      unitCents: amount(line.unitCents), amountCents: amount(line.amountCents), promotion: line.promotion };
  });
  const subtotalCents = amount(source.subtotalCents);
  const discountCents = amount(source.discountCents);
  const totalCents = amount(source.totalCents);
  if (lines.reduce((sum, line) => sum + line.amountCents, 0) !== subtotalCents || subtotalCents - discountCents !== totalCents) throw new InvalidHistoryError("receipt does not add up");
  return { lines, coupons: source.coupons.map(text), subtotalCents, discountCents, totalCents };
}

export function historicalReceipt(document: unknown): string {
  return formatReceipt(readHistoricalQuote(object(document).quote));
}

export interface HistoryEntry {
  id: string;
  createdAt: string;
  quote: Quote;
}
export class History {
  private entries = new Map<string, HistoryEntry>();

  add(id: string, createdAt: string, q: Quote): void {
    if (!id || this.entries.has(id)) throw new InvalidHistoryError("duplicate or empty order ID");
    if (!Number.isFinite(Date.parse(createdAt)) || !/(?:Z|[+-][0-9][0-9]:[0-9][0-9])$/.test(createdAt)) throw new InvalidHistoryError("timestamp needs ISO offset");
    this.entries.set(id, { id, createdAt, quote: readHistoricalQuote(q) });
  }

  get(id: string): HistoryEntry | undefined {
    const entry = this.entries.get(id);
    return entry ? structuredClone(entry) : undefined;
  }

  list(): HistoryEntry[] {
    return [...this.entries.values()].sort((a, b) => Date.parse(a.createdAt) - Date.parse(b.createdAt) || a.id.localeCompare(b.id)).map((x) => structuredClone(x));
  }

  export(): string {
    return JSON.stringify(this.list(), null, 2) + "\n";
  }

  static restore(text: string): History {
    const values: unknown = JSON.parse(text);
    if (!Array.isArray(values)) throw new InvalidHistoryError("history must be a list");
    const history = new History();
    for (const value of values) {
      const entry = object(value);
      history.add(textValue(entry.id), textValue(entry.createdAt), readHistoricalQuote(entry.quote));
    }
    return history;
  }
}
function textValue(value: unknown): string { return text(value); }
