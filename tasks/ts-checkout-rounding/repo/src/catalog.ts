// The product catalog. Prices are whole cents.

export interface Product {
  sku: string;
  name: string;
  unitCents: number;
}

export class UnknownSkuError extends Error {
  constructor(sku: string) {
    super(`unknown SKU: ${sku}`);
    this.name = "UnknownSkuError";
  }
}

const PRODUCTS: Product[] = [
  { sku: "TEA-EARL", name: "Earl Grey, 100 g", unitCents: 899 },
  { sku: "TEA-SENCHA", name: "Sencha, 100 g", unitCents: 1349 },
  { sku: "TEA-RUIBOS", name: "Rooibos, 100 g", unitCents: 725 },
  { sku: "TEA-MATCHA", name: "Matcha, 30 g", unitCents: 2195 },
  { sku: "CUP-STONE", name: "Stoneware cup", unitCents: 1450 },
  { sku: "POT-GLASS", name: "Glass teapot, 1 l", unitCents: 3999 },
  { sku: "POT-CAST", name: "Cast iron teapot", unitCents: 7485 },
  { sku: "STRAINER", name: "Mesh strainer", unitCents: 395 },
  { sku: "TIN-SMALL", name: "Storage tin, small", unitCents: 611 },
  { sku: "TIN-LARGE", name: "Storage tin, large", unitCents: 1033 },
  { sku: "GIFT-BOX", name: "Gift box", unitCents: 4567 },
  { sku: "SAMPLER", name: "Tasting sampler", unitCents: 1999 },
];

const BY_SKU = new Map(PRODUCTS.map((product) => [product.sku, product]));

export function lookup(sku: string): Product {
  const product = BY_SKU.get(sku);
  if (!product) {
    throw new UnknownSkuError(sku);
  }
  return product;
}

export function allProducts(): readonly Product[] {
  return PRODUCTS;
}
