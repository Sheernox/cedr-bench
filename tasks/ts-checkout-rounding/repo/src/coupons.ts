// Coupon codes and how to read the codes a customer typed.

export type Coupon =
  | { code: string; kind: "percent"; percent: number }
  | { code: string; kind: "fixed"; cents: number };

export class UnknownCouponError extends Error {
  constructor(code: string) {
    super(`unknown coupon: ${code}`);
    this.name = "UnknownCouponError";
  }
}

const COUPONS: Coupon[] = [
  { code: "SAVE10", kind: "percent", percent: 10 },
  { code: "SAVE15", kind: "percent", percent: 15 },
  { code: "LOYAL3", kind: "percent", percent: 3 },
  { code: "TAKE5", kind: "fixed", cents: 500 },
  { code: "TAKE12", kind: "fixed", cents: 1250 },
  { code: "WELCOME", kind: "fixed", cents: 799 },
];

const BY_CODE = new Map(COUPONS.map((coupon) => [coupon.code, coupon]));

/**
 * Turn typed codes into coupons, in the order they were typed.
 * Codes are matched case-insensitively; a repeated code counts once.
 */
export function parseCoupons(codes: readonly string[]): Coupon[] {
  const seen = new Set<string>();
  const coupons: Coupon[] = [];
  for (const raw of codes) {
    const code = raw.trim().toUpperCase();
    if (seen.has(code)) {
      continue;
    }
    const coupon = BY_CODE.get(code);
    if (!coupon) {
      throw new UnknownCouponError(raw);
    }
    seen.add(code);
    coupons.push(coupon);
  }
  return coupons;
}
