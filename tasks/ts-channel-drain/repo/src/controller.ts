import { Workspace } from "./workspace.ts";
import { Tabs } from "./tabs.ts";
import { Session } from "./session.ts";
import { encodeDocument } from "./document.ts";
import type { Document } from "./document.ts";
import type { Writer } from "./writer.ts";
import { stable } from "./json-value.ts";
export interface Status {
  id: string;
  title: string;
  dirty: boolean;
  saving: boolean;
  error: string | null;
}
/** Framework-independent controller lets editor frontends share save semantics. */
export class Controller {
  readonly workspace = new Workspace();
  readonly tabs = new Tabs();
  private session: Session;
  private pending = new Map<string,number>();
  private errors = new Map<string,string>();
  private listeners = new Set<() => void>();
  constructor(writer: Writer) {
    this.session = new Session(writer);
  }
  subscribe(listener: () => void): () => void {
    this.listeners.add(listener);
    return () => { this.listeners.delete(listener); };
  }
  private changed(): void {
    for (const listener of [...this.listeners]) listener();
  }
  open(id: string,title = "Untitled"): Document {
    if (!this.workspace.list(true).some(document => document.id === id)) this.workspace.add(id,title);
    this.tabs.open(id);
    this.changed();
    return this.workspace.get(id);
  }
  async edit(id: string,text: string,signal?: AbortSignal): Promise<void> {
    const document = this.workspace.edit(id,{text},"Type");
    await this.persist(document,signal);
  }
  async rename(id: string,title: string): Promise<void> {
    const document = this.workspace.edit(id,{title},"Rename");
    await this.persist(document);
  }
  async archive(id: string): Promise<void> {
    const document = this.workspace.edit(id,{archived:true},"Archive");
    await this.persist(document);
    this.tabs.close(id);
    this.changed();
  }
  async undo(id: string): Promise<boolean> {
    const document = this.workspace.undo(id);
    if (!document) return false;
    await this.persist(document);
    return true;
  }
  async redo(id: string): Promise<boolean> {
    const document = this.workspace.redo(id);
    if (!document) return false;
    await this.persist(document);
    return true;
  }
  private async persist(document: Document,signal?: AbortSignal): Promise<void> {
    this.pending.set(document.id,(this.pending.get(document.id) ?? 0)+1);
    this.errors.delete(document.id);
    this.changed();
    try {
      await this.session.edit(document.id,stable(encodeDocument(document)),signal);
    } catch (error) {
      this.errors.set(document.id,error instanceof Error ? error.message : "save failed");
      throw error;
    } finally {
      const remaining = (this.pending.get(document.id) ?? 1)-1;
      if (remaining) this.pending.set(document.id,remaining);
      else this.pending.delete(document.id);
      this.changed();
    }
  }
  status(id: string): Status {
    const document = this.workspace.get(id);
    return {id,title:document.title,dirty:this.session.dirty(id),saving:this.pending.has(id),
      error:this.errors.get(id) ?? null};
  }
  async close(): Promise<void> {
    await this.session.close();
    this.listeners.clear();
  }
}
