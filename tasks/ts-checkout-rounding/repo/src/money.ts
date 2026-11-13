// Helpers for amounts in cents.

/** Format whole cents as a decimal string, e.g. 123456 -> "1,234.56". */
export function formatCents(cents: number): string {
  const sign = cents < 0 ? "-" : "";
  const abs = Math.abs(cents);
  const whole = Math.trunc(abs / 100);
  const frac = String(abs % 100).padStart(2, "0");
  return `${sign}${whole.toLocaleString("en-US")}.${frac}`;
}

/** Parse "12.34" or "12" into cents. Throws on anything else. */
export function parseCents(text: string): number {
  const match = /^(-?)(\d+)(?:\.(\d{1,2}))?$/.exec(text.trim());
  if (!match) {
    throw new Error(`not an amount: ${JSON.stringify(text)}`);
  }
  const cents = Number(match[2]) * 100 + Number((match[3] ?? "0").padEnd(2, "0"));
  return match[1] ? -cents : cents;
}

/**
 * Round to the nearest integer, ties to even (banker's rounding).
 *
 * Only exact for values that are exactly representable; callers that need
 * exact ties should keep amounts as integers as long as they can.
 */
export function roundHalfEven(value: number): number {
  const floor = Math.floor(value);
  const diff = value - floor;
  if (diff < 0.5) return floor;
  if (diff > 0.5) return floor + 1;
  return floor % 2 === 0 ? floor : floor + 1;
}
