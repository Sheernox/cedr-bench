// Running promotions: a percentage off every line of one SKU.

export interface Promotion {
  id: string;
  sku: string;
  percent: number;
}

const PROMOTIONS: Promotion[] = [
  { id: "spring-sencha", sku: "TEA-SENCHA", percent: 15 },
  { id: "matcha-week", sku: "TEA-MATCHA", percent: 12 },
  { id: "matcha-members", sku: "TEA-MATCHA", percent: 7 },
  { id: "cast-iron-clearance", sku: "POT-CAST", percent: 33 },
  { id: "tin-bundle", sku: "TIN-SMALL", percent: 5 },
];

/** The promotion that applies to a SKU: the largest percentage, or none. */
export function bestPromotion(sku: string): Promotion | undefined {
  let best: Promotion | undefined;
  for (const promotion of PROMOTIONS) {
    if (promotion.sku === sku && (!best || promotion.percent > best.percent)) {
      best = promotion;
    }
  }
  return best;
}

/** A line's amount after its promotion, in cents. */
export function applyPromotion(lineCents: number, promotion: Promotion | undefined): number {
  if (!promotion) {
    return lineCents;
  }
  // Keep line amounts in whole cents so the receipt lines add up.
  return Math.round((lineCents * (100 - promotion.percent)) / 100);
}
