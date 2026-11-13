// Plain-text receipts for email and the till printer.

import type { Quote } from "./checkout.ts";
import { formatCents } from "./money.ts";

const WIDTH = 40;

function row(left: string, right: string): string {
  const room = WIDTH - right.length - 1;
  const label = left.length > room ? left.slice(0, room - 1) + "~" : left;
  return label.padEnd(WIDTH - right.length) + right;
}

/** Render a quote as a fixed-width receipt. */
export function formatReceipt(q: Quote): string {
  const out: string[] = [];
  for (const line of q.lines) {
    if (line.quantity === 0) continue;
    out.push(row(`${line.quantity} x ${line.name}`, formatCents(line.amountCents)));
    if (line.promotion) {
      out.push(`  promotion: ${line.promotion}`);
    }
  }
  out.push("-".repeat(WIDTH));
  out.push(row("Subtotal", formatCents(q.subtotalCents)));
  if (q.coupons.length > 0) {
    out.push(row(`Coupons (${q.coupons.join(", ")})`, "-" + formatCents(q.discountCents)));
  }
  out.push(row("Total", formatCents(q.totalCents)));
  return out.join("\n") + "\n";
}
