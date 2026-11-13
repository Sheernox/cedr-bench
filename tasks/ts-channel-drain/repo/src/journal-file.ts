import { appendFile, readFile, writeFile, rename, mkdir, unlink } from "node:fs/promises";
import { dirname } from "node:path";
import { randomUUID } from "node:crypto";
import { encode, replay } from "./journal.ts";
import type { Sink, Write } from "./types.ts";
/** Append-only adapter serializes physical frames independently of logical keys. */
export class JournalFile {
  private path: string;
  private tail: Promise<void> = Promise.resolve();
  private stopped = false;
  constructor(path: string) {
    this.path = path;
  }
  private serial<T>(operation: () => Promise<T>): Promise<T> {
    const result = this.tail.then(operation);
    this.tail = result.then(() => {},() => {});
    return result;
  }
  readonly save: Sink = (write) => {
    if (this.stopped) return Promise.reject(new Error("journal is closed"));
    const frame = encode({...write});
    return this.serial(async () => {
      await mkdir(dirname(this.path),{recursive:true});
      await appendFile(this.path,frame,"utf8");
    });
  };
  async records(): Promise<Map<string,Write>> {
    return this.serial(async () => {
      try {
        return replay(await readFile(this.path,"utf8"));
      } catch (error) {
        if (error instanceof Error && "code" in error && error.code === "ENOENT") return new Map();
        throw error;
      }
    });
  }
  async compact(): Promise<number> {
    if (this.stopped) throw new Error("journal is closed");
    return this.serial(async () => {
      let raw: string;
      try {
        raw = await readFile(this.path,"utf8");
      } catch (error) {
        if (error instanceof Error && "code" in error && error.code === "ENOENT") return 0;
        throw error;
      }
      const records = replay(raw);
      const rows = [...records.values()].sort((a,b) => a.key < b.key ? -1 : a.key > b.key ? 1 : 0);
      const temporary = this.path+"."+randomUUID()+".pending";
      try {
        await writeFile(temporary,rows.map(encode).join(""),{flag:"wx"});
        await rename(temporary,this.path);
      } catch (error) {
        await unlink(temporary).catch((failure: unknown) => {
          if (!(failure instanceof Error && "code" in failure && failure.code === "ENOENT")) throw failure;
        });
        throw error;
      }
      return rows.length;
    });
  }
  async close(): Promise<void> {
    this.stopped = true;
    await this.tail;
  }
}
