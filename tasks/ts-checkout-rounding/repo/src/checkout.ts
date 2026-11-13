// Price an order. See docs/pricing.md for the rules.

import { lookup } from "./catalog.ts";
import { applyPromotion, bestPromotion } from "./promotions.ts";
import { parseCoupons } from "./coupons.ts";

export interface CartLine {
  sku: string;
  quantity: number;
}

export interface QuoteLine {
  sku: string;
  name: string;
  quantity: number;
  unitCents: number;
  amountCents: number;
  promotion: string | null;
}

export interface Quote {
  lines: QuoteLine[];
  coupons: string[];
  subtotalCents: number;
  discountCents: number;
  totalCents: number;
}

export function quote(cart: readonly CartLine[], couponCodes: readonly string[] = []): Quote {
  const lines: QuoteLine[] = cart.map((item) => {
    if (!Number.isInteger(item.quantity) || item.quantity < 0) {
      throw new RangeError(`bad quantity for ${item.sku}: ${item.quantity}`);
    }
    const product = lookup(item.sku);
    const promotion = bestPromotion(item.sku);
    return {
      sku: product.sku,
      name: product.name,
      quantity: item.quantity,
      unitCents: product.unitCents,
      amountCents: applyPromotion(product.unitCents * item.quantity, promotion),
      promotion: promotion ? promotion.id : null,
    };
  });

  const subtotalCents = lines.reduce((sum, line) => sum + line.amountCents, 0);
  const coupons = parseCoupons(couponCodes);

  // Coupons apply in the order the customer entered them (see pricing.md).
  let total = subtotalCents;
  for (const coupon of coupons) {
    if (coupon.kind === "percent") {
      total = (total * (100 - coupon.percent)) / 100;
    } else {
      total = Math.max(0, total - coupon.cents);
    }
  }

  return {
    lines,
    coupons: coupons.map((coupon) => coupon.code),
    subtotalCents,
    discountCents: subtotalCents - total,
    totalCents: total,
  };
}
