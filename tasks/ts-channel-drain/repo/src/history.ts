import { copyDocument, sameContent } from "./document.ts";
import type { Document } from "./document.ts";
interface Step { before: Document; after: Document; label: string }
/** Per-document undo history owns its data and bounds retained text. */
export class History {
  private steps: Step[] = [];
  private position = 0;
  private limit: number;
  constructor(limit = 100) {
    if (!Number.isInteger(limit) || limit < 1) throw new RangeError("invalid history limit");
    this.limit = limit;
  }
  push(before: Document,after: Document,label: string): void {
    if (before.id !== after.id) throw new Error("history cannot cross documents");
    if (sameContent(before,after)) return;
    this.steps.splice(this.position);
    this.steps.push({before:copyDocument(before),after:copyDocument(after),label});
    if (this.steps.length > this.limit) this.steps.shift();
    this.position = this.steps.length;
  }
  undo(current: Document): Document | undefined {
    if (this.position === 0) return undefined;
    const step = this.steps[this.position-1];
    if (step.before.id !== current.id) throw new Error("wrong history owner");
    this.position--;
    return {...copyDocument(step.before),revision:current.revision+1};
  }
  redo(current: Document): Document | undefined {
    if (this.position === this.steps.length) return undefined;
    const step = this.steps[this.position];
    if (step.after.id !== current.id) throw new Error("wrong history owner");
    this.position++;
    return {...copyDocument(step.after),revision:current.revision+1};
  }
  labels(): {undo: string | null; redo: string | null} {
    return {undo:this.position ? this.steps[this.position-1].label : null,
      redo:this.position < this.steps.length ? this.steps[this.position].label : null};
  }
  clear(): void {
    this.steps = [];
    this.position = 0;
  }
  size(): number {
    return this.steps.length;
  }
}
