import type { Clock } from "./types.ts";
/** Production clock. Tests may supply a controlled clock instead. */
export const systemClock: Clock = {
  now: () => Date.now(),
  schedule: (delay, callback) => {
    const timer = setTimeout(callback, delay);
    return () => clearTimeout(timer);
  },
};
