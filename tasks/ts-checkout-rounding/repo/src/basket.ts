// The cart editor retains duplicate lines so receipt display matches user input.
import type { CartLine } from "./checkout.ts";
import { lookup } from "./catalog.ts";
import { readOrder, saveOrder } from "./orders.ts";
import type { SavedOrder } from "./orders.ts";

export class Basket {
  private lines: CartLine[] = [];
  private codes: string[] = [];

  static restore(value: unknown): Basket {
    const decoded = readOrder(value);
    const basket = new Basket();
    basket.lines = decoded.cart;
    basket.codes = decoded.couponCodes;
    return basket;
  }

  add(sku: string, quantity: number): number {
    lookup(sku);
    this.validateQuantity(quantity);
    this.lines.push({ sku, quantity });
    return this.lines.length - 1;
  }

  setQuantity(index: number, quantity: number): void {
    this.validateIndex(index);
    this.validateQuantity(quantity);
    this.lines[index] = { ...this.lines[index], quantity };
  }

  remove(index: number): CartLine {
    this.validateIndex(index);
    return { ...this.lines.splice(index, 1)[0] };
  }

  move(from: number, to: number): void {
    this.validateIndex(from);
    this.validateIndex(to);
    const [line] = this.lines.splice(from, 1);
    this.lines.splice(to, 0, line);
  }

  coupons(codes: readonly string[]): void {
    this.codes = [...codes];
  }

  clear(): void {
    this.lines = [];
    this.codes = [];
  }

  document(): SavedOrder {
    return saveOrder(this.lines, this.codes);
  }

  quantities(): Map<string, number> {
    const result = new Map<string, number>();
    for (const line of this.lines) result.set(line.sku, (result.get(line.sku) ?? 0) + line.quantity);
    return result;
  }

  private validateIndex(index: number): void {
    if (!Number.isInteger(index) || index < 0 || index >= this.lines.length) throw new RangeError("cart line index out of range");
  }

  private validateQuantity(quantity: number): void {
    if (!Number.isSafeInteger(quantity) || quantity < 0) throw new RangeError("invalid cart quantity");
  }
}
