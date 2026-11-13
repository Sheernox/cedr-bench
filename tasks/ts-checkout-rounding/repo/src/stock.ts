// Reservations prevent an operator from promising stock twice in offline sessions.
export class StockError extends Error {}
export interface StockRow { sku: string; onHand: number; reserved: number; available: number; }

export class Stock {
  private onHand = new Map<string, number>();
  private holds = new Map<string, Map<string, number>>();

  receive(sku: string, quantity: number): void {
    this.quantity(quantity);
    if (!sku) throw new StockError("SKU required");
    this.onHand.set(sku, (this.onHand.get(sku) ?? 0) + quantity);
  }

  reserve(order: string, lines: readonly { sku: string; quantity: number }[]): void {
    if (!order || this.holds.has(order)) throw new StockError("duplicate reservation");
    const totals = new Map<string, number>();
    for (const line of lines) {
      this.quantity(line.quantity);
      totals.set(line.sku, (totals.get(line.sku) ?? 0) + line.quantity);
    }
    for (const [sku, quantity] of totals) {
      if (quantity > this.available(sku)) throw new StockError("insufficient stock: " + sku);
    }
    this.holds.set(order, totals);
  }

  release(order: string): void {
    if (!this.holds.delete(order)) throw new StockError("unknown reservation");
  }

  ship(order: string): void {
    const hold = this.holds.get(order);
    if (!hold) throw new StockError("unknown reservation");
    for (const [sku, quantity] of hold) this.onHand.set(sku, (this.onHand.get(sku) ?? 0) - quantity);
    this.holds.delete(order);
  }

  available(sku: string): number {
    let reserved = 0;
    for (const hold of this.holds.values()) reserved += hold.get(sku) ?? 0;
    return (this.onHand.get(sku) ?? 0) - reserved;
  }

  rows(): StockRow[] {
    return [...this.onHand].sort(([a], [b]) => a.localeCompare(b)).map(([sku, onHand]) => {
      const available = this.available(sku);
      return { sku, onHand, available, reserved: onHand - available };
    });
  }

  snapshot(): { onHand: [string, number][]; holds: [string, [string, number][]][] } {
    return { onHand: [...this.onHand], holds: [...this.holds].map(([id, hold]) => [id, [...hold]]) };
  }

  private quantity(value: number): void {
    if (!Number.isSafeInteger(value) || value < 0) throw new StockError("quantity must be a nonnegative integer");
  }
}
