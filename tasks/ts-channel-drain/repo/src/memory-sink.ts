import type { Sink, Write } from "./types.ts";
/** In-memory sink used by offline examples and command adapters. */
export class MemorySink {
  readonly records = new Map<string,Write>();
  readonly history: Write[] = [];
  readonly save: Sink = async (write) => {
    const copy = {...write};
    this.history.push(copy);
    this.records.set(write.key,copy);
  };
  read(key: string): string | undefined { return this.records.get(key)?.value; }
}
