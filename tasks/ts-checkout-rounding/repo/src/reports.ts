// Reports retain the receipt's accepted price and never recalculate an order.
import { History } from "./history.ts";
import { csv, htmlTable } from "./transport.ts";
import { formatCents } from "./money.ts";
import { allProducts } from "./catalog.ts";
import { bestPromotion } from "./promotions.ts";
import { select } from "./filters.ts";
import type { Filter } from "./filters.ts";

export function orderRows(history: History): Record<string, unknown>[] {
  return history.list().map((entry) => ({ id: entry.id, createdAt: entry.createdAt,
    totalCents: entry.quote.totalCents, subtotalCents: entry.quote.subtotalCents,
    discountCents: entry.quote.discountCents, lines: entry.quote.lines.length }));
}

export function orderCsv(history: History): string {
  return csv(orderRows(history), ["id", "createdAt", "subtotalCents", "discountCents", "totalCents"]);
}

export function orderHtml(history: History): string {
  const rows = orderRows(history).map((row) => ({ ...row,
    subtotal: formatCents(Number(row.subtotalCents)), discount: formatCents(Number(row.discountCents)), total: formatCents(Number(row.totalCents)) }));
  return htmlTable(rows, ["id", "createdAt", "subtotal", "discount", "total"], "Accepted orders");
}

export function productRows(): Record<string, unknown>[] {
  return allProducts().map((product) => ({ ...product, promotion: bestPromotion(product.sku)?.id ?? null }));
}

export function productCsv(): string {
  return csv(productRows(), ["sku", "name", "unitCents", "promotion"]);
}

export function bySku(history: History): Record<string, unknown>[] {
  const totals = new Map<string, { units: number; displayCents: number }>();
  for (const entry of history.list()) {
    for (const line of entry.quote.lines) {
      const row = totals.get(line.sku) ?? { units: 0, displayCents: 0 };
      row.units += line.quantity;
      row.displayCents += line.amountCents;
      totals.set(line.sku, row);
    }
  }
  return [...totals].sort(([a], [b]) => a.localeCompare(b)).map(([sku, totals]) => ({ sku, ...totals }));
}

export function couponUses(history: History): Record<string, unknown>[] {
  const counts = new Map<string, number>();
  for (const entry of history.list()) {
    for (const code of new Set(entry.quote.coupons)) counts.set(code, (counts.get(code) ?? 0) + 1);
  }
  return [...counts].sort(([a], [b]) => a.localeCompare(b)).map(([code, uses]) => ({ code, uses }));
}

export function filteredOrders(history: History, filter: Filter): Record<string, unknown>[] {
  return select(orderRows(history), filter);
}

export function dailyTotals(history: History): Record<string, unknown>[] {
  const totals = new Map<string, { orders: number; cents: number }>();
  for (const entry of history.list()) {
    const date = new Date(entry.createdAt).toISOString().slice(0, 10);
    const row = totals.get(date) ?? { orders: 0, cents: 0 };
    row.orders++;
    row.cents += entry.quote.totalCents;
    totals.set(date, row);
  }
  return [...totals].sort(([a], [b]) => a.localeCompare(b)).map(([date, row]) => ({ date, ...row }));
}
