// Versioned basket persistence, independent of transport and storage.
import { lookup } from "./catalog.ts";
import { bestPromotion } from "./promotions.ts";
import { parseCoupons } from "./coupons.ts";
import type { CartLine, Quote, QuoteLine } from "./checkout.ts";

export interface Basket { cart: CartLine[]; couponCodes: string[]; }
export interface SavedOrder { version: 2; cart: CartLine[]; couponCodes: string[]; }
export class InvalidOrderError extends Error {}

function object(value: unknown): Record<string, unknown> {
  if (value === null || typeof value !== "object" || Array.isArray(value)) throw new InvalidOrderError("expected order object");
  return value as Record<string, unknown>;
}

export function readOrder(document: unknown): Basket {
  const doc = object(document);
  let cart: CartLine[];
  let couponCodes: string[];
  if (doc.version === 1 && Array.isArray(doc.items) && typeof doc.coupons === "string") {
    cart = doc.items.map((raw: unknown) => {
      const item = object(raw);
      if (typeof item.product !== "string" || typeof item.count !== "string" || !/^\s*\d+\s*$/.test(item.count)) throw new InvalidOrderError("invalid legacy item");
      const quantity = Number(item.count);
      if (!Number.isSafeInteger(quantity)) throw new InvalidOrderError("quantity too large");
      return { sku: item.product, quantity };
    });
    couponCodes = doc.coupons === "" ? [] : doc.coupons.split("|");
  } else if (doc.version === 2 && Array.isArray(doc.cart) && Array.isArray(doc.couponCodes)) {
    cart = doc.cart.map((raw: unknown) => {
      const item = object(raw);
      if (typeof item.sku !== "string" || typeof item.quantity !== "number" || !Number.isSafeInteger(item.quantity) || item.quantity < 0) throw new InvalidOrderError("invalid cart line");
      return { sku: item.sku, quantity: item.quantity };
    });
    if (!doc.couponCodes.every((x: unknown) => typeof x === "string")) throw new InvalidOrderError("invalid coupons");
    couponCodes = [...doc.couponCodes];
  } else throw new InvalidOrderError("unsupported order format");
  return { cart, couponCodes };
}

export function saveOrder(cart: readonly CartLine[], couponCodes: readonly string[] = []): SavedOrder {
  return { version: 2, cart: cart.map((line) => ({ ...line })), couponCodes: [...couponCodes] };
}

/** Current price for a historical basket; receipt snapshots remain untouched. */
export function reprice(document: unknown): Quote {
  const { cart, couponCodes } = readOrder(document);
  const lines: QuoteLine[] = cart.map((item) => {
    const product = lookup(item.sku);
    const promotion = bestPromotion(item.sku);
    return { ...item, name: product.name, unitCents: product.unitCents,
      amountCents: Math.round(product.unitCents * item.quantity * (100 - (promotion?.percent ?? 0)) / 100), promotion: promotion?.id ?? null };
  });
  const coupons = parseCoupons(couponCodes);
  const subtotalCents = lines.reduce((sum, item) => sum + item.amountCents, 0);
  let totalCents = subtotalCents;
  for (const coupon of coupons) {
    totalCents = coupon.kind === "percent" ? totalCents * (100 - coupon.percent) / 100 : Math.max(0, totalCents - coupon.cents);
  }
  return { lines, coupons: coupons.map((c) => c.code), subtotalCents, totalCents, discountCents: subtotalCents - totalCents };
}
