import { test } from "node:test";
import assert from "node:assert/strict";
import { Workspace } from "../src/workspace.ts";
import { History } from "../src/history.ts";
import { Tabs } from "../src/tabs.ts";
import { createDocument, editDocument, encodeDocument, decodeDocument } from "../src/document.ts";
import { isJson, parse, stable } from "../src/json-value.ts";
import { search } from "../src/search.ts";
import { LineMap } from "../src/line-map.ts";
import { apply, invert, replaceAll } from "../src/patch.ts";
import { defaults, decodeSettings, encodeSettings, remember } from "../src/settings.ts";
import { encodeCsv, decodeCsv } from "../src/csv.ts";
import { describe, exportDocuments } from "../src/export.ts";
import { Moments, Counters } from "../src/metrics.ts";
import { encode, decode, replay } from "../src/journal.ts";

test("workspace edits have independent history and owned views", () => {
  const workspace = new Workspace();
  workspace.add("b");
  workspace.add("a");
  workspace.edit("a",{text:"one",tags:["work"]},"Type");
  const view = workspace.get("a");
  view.tags.push("borrowed");
  assert.deepEqual(workspace.get("a").tags,["work"]);
  assert.equal(workspace.undo("a")?.text,"");
  assert.equal(workspace.redo("a")?.text,"one");
  assert.deepEqual(workspace.list().map(d => d.id),["a","b"]);
  workspace.edit("b",{archived:true});
  assert.deepEqual(workspace.list().map(d => d.id),["a"]);
});

test("workspace imports validate before making changes", () => {
  const workspace = new Workspace();
  workspace.add("a","original");
  const raw = workspace.export();
  const restored = new Workspace();
  restored.import(raw);
  assert.equal(restored.export(),raw);
  const document = encodeDocument(createDocument("b"));
  assert.throws(() => restored.import(stable({version:1,documents:[document,document]})));
  assert.equal(restored.export(),raw);
  restored.edit("a",{title:"changed"});
  restored.import(raw);
  assert.equal(restored.get("a").title,"changed");
  restored.import(raw,true);
  assert.equal(restored.get("a").title,"original");
});

test("history trims old entries and forks after undo", () => {
  const history = new History(2);
  let document = createDocument("a");
  for (const text of ["one","two","three"]) {
    const next = editDocument(document,{text});
    history.push(document,next,text);
    document = next;
  }
  assert.equal(history.size(),2);
  document = history.undo(document)!;
  assert.equal(document.text,"two");
  const fork = editDocument(document,{text:"fork"});
  history.push(document,fork,"fork");
  assert.equal(history.redo(fork),undefined);
  assert.deepEqual(history.labels(),{undo:"fork",redo:null});
});

test("tabs close to a neighbor and retain selection through moves", () => {
  const tabs = new Tabs();
  tabs.open("a"); tabs.open("b"); tabs.open("c");
  tabs.select("b"); tabs.move("b",0);
  assert.deepEqual(tabs.all(),["b","a","c"]);
  assert.equal(tabs.active(),"b");
  assert.equal(tabs.close("b"),"a");
  assert.equal(tabs.next(-1),"c");
  const view = tabs.all();view.push("other");
  assert.deepEqual(tabs.all(),["a","c"]);
  assert.throws(() => tabs.restore(["a","a"],"a"));
  assert.throws(() => tabs.select("missing"));
});

test("JSON boundaries reject cycles and nonfinite numbers", () => {
  const cycle: unknown[] = [];cycle.push(cycle);
  assert.equal(isJson(cycle),false);
  assert.equal(isJson(new Date()),false);
  assert.equal(isJson(Number.NaN),false);
  assert.equal(stable({b:2,a:["é",false,null]}),'{"a":["é",false,null],"b":2}');
  assert.deepEqual(parse('{"a":[]}'),{a:[]});
  assert.throws(() => decodeDocument({id:"",title:"",text:"",tags:[],revision:0,archived:false}));
});

test("field filters and phrase search do not mutate documents", () => {
  const a = editDocument(createDocument("a","Alpha Beta"),{tags:["work"],text:"one"});
  const b = createDocument("b","Gamma");
  assert.deepEqual(search([a,b],'title:"alpha beta" -tags:home').map(d => d.id),["a"]);
  const found = search([a,b],"WORK");
  found[0].tags.push("borrowed");
  assert.deepEqual(a.tags,["work"]);
  assert.throws(() => search([a],'"unterminated'));
});

test("line offsets round trip at every UTF-16 position", () => {
  const text = "one\r\n😀 two\nlast\n";
  const map = new LineMap(text);
  for (let offset=0;offset<=text.length;offset++) assert.equal(map.offset(map.position(offset)),offset);
  assert.equal(map.lines(),4);
  assert.equal(map.line(0),"one");
  assert.equal(map.line(3),"");
  assert.throws(() => map.position(-1));
  assert.throws(() => map.offset({line:0,column:100}));
});

test("text patches invert without coordinate drift", () => {
  const text = "alpha beta alpha";
  const edits = replaceAll(text,"alpha","X");
  assert.equal(apply(text,edits),"X beta X");
  assert.equal(apply(apply(text,edits),invert(text,edits)),text);
  assert.throws(() => apply(text,[{start:1,end:5,text:""},{start:4,end:8,text:""}]));
  assert.throws(() => replaceAll(text,"","bad"));
});

test("CSV quotes and embedded newlines round trip", () => {
  const rows = [["a,b",'say "hi"',"line\r\nnext",""],["plain","é","x","tail"]];
  assert.deepEqual(decodeCsv(encodeCsv(rows)),rows);
  assert.throws(() => decodeCsv('"unterminated'));
  assert.throws(() => decodeCsv('"closed"extra'));
});

test("settings preserve explicit false and bound recent history", () => {
  const preferences = {...defaults(),wrap:false,autosave:false,recent:["a","b"]};
  assert.deepEqual(decodeSettings(encodeSettings(preferences)),preferences);
  assert.deepEqual(remember(preferences,"b",2).recent,["b","a"]);
  assert.deepEqual(remember(preferences,"c",2).recent,["c","a"]);
  assert.throws(() => decodeSettings('{"tabSize":0}'));
  assert.throws(() => decodeSettings('{"theme":"unknown"}'));
});

test("journal rejects a truncated tail and keeps newer generations", () => {
  const one = {key:"a",value:"one",generation:1};
  const two = {key:"a",value:"two",generation:2};
  assert.deepEqual(decode(encode(one)),one);
  assert.deepEqual(replay(encode(two)+encode(one)).get("a"),two);
  assert.throws(() => replay(encode(one).trimEnd()));
  assert.throws(() => decode('{"kind":"save","key":"a","value":"x","generation":0}'));
});

test("document projections count code points and UTF-8 separately", () => {
  const document = editDocument(createDocument("a","Title"),{text:"😀 hi\n"});
  assert.deepEqual(describe(document),{characters:5,words:2,lines:2,bytes:8});
  assert.match(exportDocuments([document],"markdown"),/^# Title/u);
  assert.equal(JSON.parse(exportDocuments([document],"json"))[0].text,document.text);
});

test("streaming metrics retain moments and deterministic counters", () => {
  const moments = new Moments();
  [1,2,3].forEach(value => moments.add(value));
  assert.deepEqual(moments.snapshot(),{count:3,mean:2,variance:2/3,min:1,max:3});
  assert.throws(() => moments.add(Infinity));
  const a = new Counters();const b = new Counters();
  a.add("saved",2);b.add("saved");b.add("failed",0);a.merge(b);
  assert.deepEqual(a.snapshot(),{failed:0,saved:3});
  moments.reset();assert.equal(moments.snapshot().count,0);
});
