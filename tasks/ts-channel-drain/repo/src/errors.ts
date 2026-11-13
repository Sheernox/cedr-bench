/** Public lifecycle errors are distinguishable from sink failures. */
export class ClosedError extends Error {
  constructor() { super("writer is closing"); this.name = "ClosedError"; }
}
export class CancelledError extends Error {
  constructor() { super("save cancelled"); this.name = "CancelledError"; }
}
