// Parcel estimates are separate from merchandise pricing and finance receipts.
export interface ParcelLine { sku: string; quantity: number; grams: number; fragile: boolean; }
export interface Parcel { lines: ParcelLine[]; grams: number; fragile: boolean; }
export class ShippingError extends Error {}

export function pack(lines: readonly ParcelLine[], capacityGrams: number): Parcel[] {
  if (!Number.isSafeInteger(capacityGrams) || capacityGrams <= 0) throw new ShippingError("invalid parcel capacity");
  const result: Parcel[] = [];
  let current: Parcel = { lines: [], grams: 0, fragile: false };
  for (const line of lines) {
    if (!Number.isSafeInteger(line.quantity) || line.quantity < 0 || !Number.isSafeInteger(line.grams) || line.grams <= 0 || typeof line.fragile !== "boolean") throw new ShippingError("invalid parcel line");
    if (line.grams > capacityGrams) throw new ShippingError("item exceeds parcel capacity");
    let remaining = line.quantity;
    while (remaining > 0) {
      const available = Math.floor((capacityGrams - current.grams) / line.grams);
      if (!available) {
        result.push(current);
        current = { lines: [], grams: 0, fragile: false };
        continue;
      }
      const count = Math.min(available, remaining);
      current.lines.push({ ...line, quantity: count });
      current.grams += count * line.grams;
      current.fragile ||= line.fragile;
      remaining -= count;
    }
  }
  if (current.lines.length) result.push(current);
  return result;
}

export interface RateBand { maxGrams: number; cents: number; }
export interface ShippingProfile { id: string; bands: RateBand[]; fragileCents: number; }

export function validateProfile(profile: ShippingProfile): ShippingProfile {
  if (!profile.id || !profile.bands.length || !Number.isSafeInteger(profile.fragileCents) || profile.fragileCents < 0) throw new ShippingError("invalid shipping profile");
  let previous = 0;
  for (const band of profile.bands) {
    if (!Number.isSafeInteger(band.maxGrams) || band.maxGrams <= previous || !Number.isSafeInteger(band.cents) || band.cents < 0) throw new ShippingError("rate bands must be ascending");
    previous = band.maxGrams;
  }
  return structuredClone(profile);
}

export function shippingCents(parcels: readonly Parcel[], profile: ShippingProfile): number {
  validateProfile(profile);
  let total = 0;
  for (const parcel of parcels) {
    const band = profile.bands.find((band) => parcel.grams <= band.maxGrams);
    if (!band) throw new ShippingError("parcel exceeds shipping profile");
    total += band.cents + (parcel.fragile ? profile.fragileCents : 0);
  }
  return total;
}

export class Profiles {
  private values = new Map<string, ShippingProfile>();

  add(profile: ShippingProfile): void {
    const copy = validateProfile(profile);
    if (this.values.has(copy.id)) throw new ShippingError("duplicate profile");
    this.values.set(copy.id, copy);
  }

  get(id: string): ShippingProfile {
    const profile = this.values.get(id);
    if (!profile) throw new ShippingError("unknown shipping profile");
    return structuredClone(profile);
  }

  list(): ShippingProfile[] {
    return [...this.values.values()].sort((a, b) => a.id.localeCompare(b.id)).map((p) => structuredClone(p));
  }

  remove(id: string): void {
    if (!this.values.delete(id)) throw new ShippingError("unknown shipping profile");
  }
}
