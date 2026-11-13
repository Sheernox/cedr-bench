import type { Clock } from "./types.ts";
interface Timer { at: number; id: number; callback: () => void; cancelled: boolean }
/** Explicit advancement makes backoff and shutdown tests deterministic. */
export class ManualClock implements Clock {
  private time = 0;
  private next = 0;
  private timers: Timer[] = [];
  now(): number { return this.time; }
  schedule(delay: number, callback: () => void): () => void {
    if (!Number.isFinite(delay) || delay < 0) throw new RangeError("invalid delay");
    const timer = { at: this.time + delay, id: ++this.next, callback, cancelled: false };
    this.timers.push(timer);
    return () => { timer.cancelled = true; };
  }
  advance(ms: number): void {
    if (!Number.isFinite(ms) || ms < 0) throw new RangeError("invalid advance");
    const end = this.time + ms;
    let budget = 10000;
    while (true) {
      this.timers.sort((a,b) => a.at-b.at || a.id-b.id);
      const timer = this.timers.find(t => !t.cancelled && t.at <= end);
      if (!timer) break;
      if (--budget === 0) throw new Error("clock callback loop");
      timer.cancelled = true;
      this.time = timer.at;
      timer.callback();
    }
    this.time = end;
    this.timers = this.timers.filter(t => !t.cancelled);
  }
  pending(): number { return this.timers.filter(t => !t.cancelled).length; }
}
