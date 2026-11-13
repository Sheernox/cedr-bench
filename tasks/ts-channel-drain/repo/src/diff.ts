import type { Document } from "./document.ts";
import { copyDocument, sameContent } from "./document.ts";
/** Workspace comparisons operate on snapshots and never borrow mutable tags. */
export type Change =
  | {kind: "added"; id: string; after: Document}
  | {kind: "removed"; id: string; before: Document}
  | {kind: "changed"; id: string; before: Document; after: Document};
function index(documents: readonly Document[]): Map<string,Document> {
  const result = new Map<string,Document>();
  for (const document of documents) {
    if (result.has(document.id)) throw new Error("duplicate document in snapshot");
    result.set(document.id,document);
  }
  return result;
}
export function compare(before: readonly Document[],after: readonly Document[]): Change[] {
  const old = index(before);
  const next = index(after);
  const ids = [...new Set([...old.keys(),...next.keys()])].sort();
  const changes: Change[] = [];
  for (const id of ids) {
    const left = old.get(id);
    const right = next.get(id);
    if (!left && right) changes.push({kind:"added",id,after:copyDocument(right)});
    else if (left && !right) changes.push({kind:"removed",id,before:copyDocument(left)});
    else if (left && right && !sameContent(left,right)) {
      changes.push({kind:"changed",id,before:copyDocument(left),after:copyDocument(right)});
    }
  }
  return changes;
}
export function applyChanges(documents: readonly Document[],changes: readonly Change[]): Document[] {
  const result = index(documents.map(copyDocument));
  for (const change of changes) {
    const current = result.get(change.id);
    if (change.kind === "added") {
      if (current) throw new Error("added document already exists");
      result.set(change.id,copyDocument(change.after));
    } else {
      if (!current || !sameContent(current,change.before)) throw new Error("snapshot changed since diff");
      if (change.kind === "removed") result.delete(change.id);
      else result.set(change.id,copyDocument(change.after));
    }
  }
  return [...result.values()].sort((a,b) => a.id < b.id ? -1 : a.id > b.id ? 1 : 0);
}
export function reverseChanges(changes: readonly Change[]): Change[] {
  return [...changes].reverse().map(change => {
    if (change.kind === "added") return {kind:"removed",id:change.id,before:copyDocument(change.after)};
    if (change.kind === "removed") return {kind:"added",id:change.id,after:copyDocument(change.before)};
    return {kind:"changed",id:change.id,before:copyDocument(change.after),after:copyDocument(change.before)};
  });
}
export function summary(changes: readonly Change[]): Record<Change["kind"],number> {
  const result = {added:0,removed:0,changed:0};
  for (const change of changes) result[change.kind]++;
  return result;
}
