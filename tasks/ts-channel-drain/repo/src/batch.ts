import { deferred } from "./deferred.ts";
import type { Deferred } from "./deferred.ts";
import type { Receipt, Write } from "./types.ts";
/** A queued payload owns every caller superseded before it starts. */
export interface Batch {
  write: Write;
  waiters: Deferred<Receipt>[];
  attempt: number;
}
export function batch(write: Write): Batch {
  return { write, waiters: [], attempt: 0 };
}
