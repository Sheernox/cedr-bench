import { copyDocument, createDocument, editDocument, decodeDocument, encodeDocument } from "./document.ts";
import type { Document } from "./document.ts";
import { History } from "./history.ts";
import { object, parse, stable } from "./json-value.ts";
/** Editor state keeps undo separate from storage acknowledgments. */
export class Workspace {
  private documents = new Map<string,Document>();
  private histories = new Map<string,History>();
  add(id: string,title?: string): Document {
    if (this.documents.has(id)) throw new Error("duplicate document");
    const document = createDocument(id,title);
    this.documents.set(id,document);
    this.histories.set(id,new History());
    return copyDocument(document);
  }
  get(id: string): Document {
    const document = this.documents.get(id);
    if (!document) throw new Error("unknown document: "+id);
    return copyDocument(document);
  }
  list(includeArchived = false): Document[] {
    return [...this.documents.values()].filter(document => includeArchived || !document.archived)
      .sort((a,b) => a.id < b.id ? -1 : a.id > b.id ? 1 : 0).map(copyDocument);
  }
  edit(id: string,change: Partial<Pick<Document,"title"|"text"|"tags"|"archived">>,label = "Edit"): Document {
    const before = this.get(id);
    const after = editDocument(before,change);
    this.histories.get(id)?.push(before,after,label);
    this.documents.set(id,after);
    return copyDocument(after);
  }
  undo(id: string): Document | undefined {
    const result = this.histories.get(id)?.undo(this.get(id));
    if (result) this.documents.set(id,result);
    return result && copyDocument(result);
  }
  redo(id: string): Document | undefined {
    const result = this.histories.get(id)?.redo(this.get(id));
    if (result) this.documents.set(id,result);
    return result && copyDocument(result);
  }
  remove(id: string): void {
    this.documents.delete(id);
    this.histories.delete(id);
  }
  export(): string {
    return stable({version:1,documents:this.list(true).map(encodeDocument)}) + "\n";
  }
  import(raw: string,overwrite = false): void {
    const value = object(parse(raw));
    if (value.version !== 1 || !Array.isArray(value.documents)) throw new Error("unsupported workspace");
    const documents = value.documents.map(decodeDocument);
    const seen = new Set<string>();
    for (const document of documents) {
      if (seen.has(document.id)) throw new Error("duplicate imported document");
      seen.add(document.id);
    }
    for (const document of documents) {
      if (overwrite || !this.documents.has(document.id)) {
        this.documents.set(document.id,document);
        this.histories.set(document.id,new History());
      }
    }
  }
}
