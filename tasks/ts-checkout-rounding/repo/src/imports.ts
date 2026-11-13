// Imported files are decoded before applying them to an operator's active cart.
import { readJsonLines, TransportError } from "./transport.ts";
import { readOrder, saveOrder } from "./orders.ts";
import type { Basket as BasketValue, SavedOrder } from "./orders.ts";

export interface ImportResult { index: number; basket: BasketValue | null; error: string | null; }

export function inspectOrders(text: string): ImportResult[] {
  return readJsonLines(text).map((document, index) => {
    try { return { index, basket: readOrder(document), error: null }; }
    catch (error) {
      if (!(error instanceof Error)) throw error;
      return { index, basket: null, error: error.message };
    }
  });
}

export function upgradeOrders(text: string): SavedOrder[] {
  return readJsonLines(text).map((document, index) => {
    try {
      const basket = readOrder(document);
      return saveOrder(basket.cart, basket.couponCodes);
    } catch (error) {
      if (!(error instanceof Error)) throw error;
      throw new TransportError(`order ${index + 1}: ${error.message}`);
    }
  });
}

export function concatenate(baskets: readonly BasketValue[]): BasketValue {
  return { cart: baskets.flatMap((b) => b.cart.map((line) => ({ ...line }))), couponCodes: baskets.flatMap((b) => [...b.couponCodes]) };
}

export function splitBySku(basket: BasketValue): SavedOrder[] {
  const groups = new Map<string, BasketValue>();
  for (const line of basket.cart) {
    let group = groups.get(line.sku);
    if (!group) {
      group = { cart: [], couponCodes: [...basket.couponCodes] };
      groups.set(line.sku, group);
    }
    group.cart.push({ ...line });
  }
  return [...groups].sort(([a], [b]) => a.localeCompare(b)).map(([, group]) => saveOrder(group.cart, group.couponCodes));
}

export function units(basket: BasketValue): number {
  return basket.cart.reduce((sum, line) => sum + line.quantity, 0);
}

export function empty(basket: BasketValue): boolean {
  return basket.cart.every((line) => line.quantity === 0);
}
