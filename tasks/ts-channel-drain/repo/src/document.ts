import { object, string, integer, strings } from "./json-value.ts";
import type { Json } from "./json-value.ts";
/** Portable editor documents have a local revision independent of save generations. */
export interface Document {
  id: string;
  title: string;
  text: string;
  tags: string[];
  revision: number;
  archived: boolean;
}
export function decodeDocument(value: Json): Document {
  const row = object(value);
  const id = string(row.id,"id");
  if (!id) throw new Error("document id cannot be empty");
  const revision = integer(row.revision,"revision");
  if (revision < 0) throw new Error("negative revision");
  if (typeof row.archived !== "boolean") throw new Error("archived must be boolean");
  return {
    id,
    title: string(row.title,"title"),
    text: string(row.text,"text"),
    tags: strings(row.tags,"tags"),
    revision,
    archived: row.archived,
  };
}
export function encodeDocument(document: Document): Json {
  return {
    id: document.id,
    title: document.title,
    text: document.text,
    tags: [...document.tags],
    revision: document.revision,
    archived: document.archived,
  };
}
export function copyDocument(document: Document): Document {
  return {...document,tags:[...document.tags]};
}
export function createDocument(id: string,title = "Untitled"): Document {
  return decodeDocument({id,title,text:"",tags:[],revision:0,archived:false});
}
export function editDocument(document: Document,change: Partial<Pick<Document,"title"|"text"|"tags"|"archived">>): Document {
  return decodeDocument(encodeDocument({...document,...change,revision:document.revision+1}));
}
export function sameContent(left: Document,right: Document): boolean {
  return left.title === right.title && left.text === right.text && left.archived === right.archived &&
    left.tags.length === right.tags.length && left.tags.every((tag,i) => tag === right.tags[i]);
}
