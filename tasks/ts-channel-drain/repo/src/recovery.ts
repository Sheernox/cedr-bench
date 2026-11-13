import { createHash } from "node:crypto";
import { mkdir, readFile, writeFile, rename, unlink, readdir } from "node:fs/promises";
import { join, basename } from "node:path";
import { stable, parse, object, string, integer } from "./json-value.ts";
import type { Json } from "./json-value.ts";
/** Recovery bundles are independent of live autosave files. */
export interface Recovery {
  version: 1;
  sequence: number;
  payload: Json;
  checksum: string;
}
export function checksum(payload: Json): string {
  return createHash("sha256").update(stable(payload)).digest("hex");
}
export function wrap(payload: Json,sequence: number): Recovery {
  if (!Number.isSafeInteger(sequence) || sequence < 0) throw new RangeError("invalid recovery sequence");
  return {version:1,sequence,payload:parse(stable(payload)),checksum:checksum(payload)};
}
export function unwrap(raw: string): Recovery {
  const row = object(parse(raw));
  if (row.version !== 1) throw new Error("unsupported recovery format");
  const sequence = integer(row.sequence,"sequence");
  if (sequence < 0 || row.payload === undefined) throw new Error("invalid recovery payload");
  const digest = string(row.checksum,"checksum");
  if (checksum(row.payload) !== digest) throw new Error("recovery checksum mismatch");
  return {version:1,sequence,payload:row.payload,checksum:digest};
}
export async function writeRecovery(root: string,payload: Json,sequence: number): Promise<string> {
  const recovery = wrap(payload,sequence);
  const name = String(sequence).padStart(16,"0")+".recovery.json";
  await mkdir(root,{recursive:true});
  const destination = join(root,name);
  const temporary = destination+".pending";
  try {
    await writeFile(temporary,stable({...recovery})+"\n",{flag:"wx"});
    await rename(temporary,destination);
  } catch (error) {
    await unlink(temporary).catch((failure: unknown) => {
      if (!(failure instanceof Error && "code" in failure && failure.code === "ENOENT")) throw failure;
    });
    throw error;
  }
  return name;
}
export async function readRecovery(root: string,name: string): Promise<Recovery> {
  if (basename(name) !== name || !/^\d{16}\.recovery\.json$/u.test(name)) throw new Error("invalid recovery name");
  return unwrap(await readFile(join(root,name),"utf8"));
}
export async function listRecovery(root: string): Promise<string[]> {
  try {
    return (await readdir(root)).filter(name => /^\d{16}\.recovery\.json$/u.test(name)).sort();
  } catch (error) {
    if (error instanceof Error && "code" in error && error.code === "ENOENT") return [];
    throw error;
  }
}
export async function newestRecovery(root: string): Promise<Recovery | undefined> {
  const names = await listRecovery(root);
  const failures: unknown[] = [];
  for (const name of names.reverse()) {
    try {
      return await readRecovery(root,name);
    } catch (error) {
      failures.push(error);
    }
  }
  if (failures.length) throw new AggregateError(failures,"no valid recovery bundle");
  return undefined;
}
export async function pruneRecovery(root: string,keep: number): Promise<string[]> {
  if (!Number.isInteger(keep) || keep < 1) throw new RangeError("must retain at least one recovery");
  const names = await listRecovery(root);
  const removed = names.slice(0,Math.max(0,names.length-keep));
  for (const name of removed) await unlink(join(root,name));
  return removed;
}
