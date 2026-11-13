/** Streaming latency statistics do not retain individual save timings. */
export class Moments {
  private count = 0;
  private mean = 0;
  private m2 = 0;
  private minimum: number | null = null;
  private maximum: number | null = null;
  add(value: number): void {
    if (!Number.isFinite(value)) throw new RangeError("nonfinite sample");
    this.count++;
    const delta = value-this.mean;
    this.mean += delta/this.count;
    this.m2 += delta*(value-this.mean);
    this.minimum = this.minimum === null ? value : Math.min(this.minimum,value);
    this.maximum = this.maximum === null ? value : Math.max(this.maximum,value);
  }
  snapshot(): {count: number; mean: number; variance: number; min: number | null; max: number | null} {
    return {count:this.count,mean:this.mean,variance:this.count ? this.m2/this.count : 0,
      min:this.minimum,max:this.maximum};
  }
  reset(): void {
    this.count = 0;
    this.mean = 0;
    this.m2 = 0;
    this.minimum = null;
    this.maximum = null;
  }
}
export class Counters {
  private values = new Map<string,number>();
  add(key: string,amount = 1): void {
    if (!Number.isSafeInteger(amount)) throw new RangeError("counter amount must be integer");
    this.values.set(key,(this.values.get(key) ?? 0)+amount);
  }
  get(key: string): number {
    return this.values.get(key) ?? 0;
  }
  snapshot(): Record<string,number> {
    return Object.fromEntries([...this.values].sort(([a],[b]) => a < b ? -1 : a > b ? 1 : 0));
  }
  merge(other: Counters): void {
    for (const [key,value] of Object.entries(other.snapshot())) this.add(key,value);
  }
  reset(): void {
    this.values.clear();
  }
}
