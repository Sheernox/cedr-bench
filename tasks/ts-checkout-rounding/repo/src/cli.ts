// Offline command adapter. Domain modules determine pricing and persistence.
import { readFileSync } from "node:fs";
import { quote } from "./checkout.ts";
import { formatReceipt } from "./receipt.ts";
import { reprice, readOrder, saveOrder } from "./orders.ts";
import { historicalReceipt, History } from "./history.ts";
import { upgradeOrders, inspectOrders } from "./imports.ts";
import { productCsv, orderCsv, orderHtml } from "./reports.ts";

export class CommandError extends Error {}
export interface Options {
  command: string;
  file: string;
  compact: boolean;
}

const COMMANDS = new Set([
  "quote",
  "receipt",
  "reprice",
  "decode",
  "upgrade",
  "inspect",
  "historical-receipt",
  "history-csv",
  "history-html",
  "products-csv",
]);

export function options(argv: readonly string[]): Options {
  const args = [...argv];
  const compact = args.includes("--compact");
  const positional = args.filter((arg) => arg !== "--compact");
  if (positional.length < 1 || positional.length > 2) {
    throw new CommandError("usage: cli.ts <command> [file] [--compact]");
  }
  const [command, file = "-"] = positional;
  if (!COMMANDS.has(command)) {
    throw new CommandError("unknown command: " + command);
  }
  return { command, file, compact };
}

export function execute(command: string, input: string): unknown {
  if (command === "products-csv") return productCsv();
  if (command === "inspect") return inspectOrders(input);
  if (command === "upgrade") return upgradeOrders(input);
  if (command === "history-csv") return orderCsv(History.restore(input));
  if (command === "history-html") return orderHtml(History.restore(input));
  let document: unknown;
  try {
    document = JSON.parse(input);
  } catch {
    throw new CommandError("input is not a JSON document");
  }
  switch (command) {
    case "quote": {
      const basket = readOrder(document);
      return quote(basket.cart, basket.couponCodes);
    }
    case "receipt": {
      const basket = readOrder(document);
      return formatReceipt(quote(basket.cart, basket.couponCodes));
    }
    case "reprice":
      return reprice(document);
    case "decode": {
      const basket = readOrder(document);
      return saveOrder(basket.cart, basket.couponCodes);
    }
    case "historical-receipt":
      return historicalReceipt(document);
    default:
      throw new CommandError("unsupported command: " + command);
  }
}

export function render(value: unknown, compact: boolean): string {
  if (typeof value === "string") return value;
  return JSON.stringify(value, null, compact ? undefined : 2) + "\n";
}

export function main(argv: readonly string[]): number {
  try {
    const opts = options(argv);
    const input = opts.command === "products-csv" ? "" : readFileSync(opts.file === "-" ? 0 : opts.file, "utf8");
    const result = execute(opts.command, input);
    process.stdout.write(render(result, opts.compact));
    return 0;
  } catch (error) {
    if (!(error instanceof Error)) throw error;
    process.stderr.write("cannot complete order command: " + error.message + "\n");
    return 2;
  }
}

if (import.meta.main) process.exitCode = main(process.argv.slice(2));
