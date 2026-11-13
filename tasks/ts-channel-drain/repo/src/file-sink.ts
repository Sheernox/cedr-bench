import { mkdir, writeFile, rename, unlink } from "node:fs/promises";
import { join } from "node:path";
import { createHash, randomUUID } from "node:crypto";
import type { Sink } from "./types.ts";
/** Atomic per-key files; the writer provides ordering across calls. */
export function fileSink(root: string): Sink {
  return async (write) => {
    await mkdir(root,{recursive:true});
    const name = createHash("sha256").update(write.key).digest("hex") + ".json";
    const temporary = join(root,".save-"+randomUUID());
    try {
      await writeFile(temporary,JSON.stringify(write)+"\n",{flag:"wx"});
      await rename(temporary,join(root,name));
    } catch (error) {
      await unlink(temporary).catch((cleanup: unknown) => {
        if (!(cleanup instanceof Error && "code" in cleanup && cleanup.code === "ENOENT")) throw cleanup;
      });
      throw error;
    }
  };
}
