import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, readFile, writeFile, readdir, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { wrap, unwrap, writeRecovery, readRecovery, listRecovery, newestRecovery, pruneRecovery } from "../src/recovery.ts";
import { createDocument, editDocument } from "../src/document.ts";
import { compare, applyChanges, reverseChanges, summary } from "../src/diff.ts";
import { Controller } from "../src/controller.ts";
import { Writer } from "../src/writer.ts";
import { MemorySink } from "../src/memory-sink.ts";
import { fileSink } from "../src/file-sink.ts";
import { ManualClock } from "../src/manual-clock.ts";

test("recovery checksums reject content mutation", () => {
  const payload = {a:[1,false,null],title:"é"};
  const envelope = wrap(payload,3);
  assert.deepEqual(unwrap(JSON.stringify(envelope)),envelope);
  payload.a.push(2);
  assert.deepEqual(envelope.payload,{a:[1,false,null],title:"é"});
  const broken = {...envelope,payload:{other:true}};
  assert.throws(() => unwrap(JSON.stringify(broken)));
  assert.throws(() => wrap({},-1));
  assert.throws(() => unwrap('{"version":2}'));
});

test("recovery chooses a valid older bundle and prunes oldest", async () => {
  const root = await mkdtemp(join(tmpdir(),"recovery-test-"));
  try {
    assert.deepEqual(await listRecovery(root),[]);
    const one = await writeRecovery(root,{text:"one"},1);
    const two = await writeRecovery(root,{text:"two"},2);
    const three = await writeRecovery(root,{text:"three"},3);
    assert.deepEqual((await readRecovery(root,one)).payload,{text:"one"});
    await writeFile(join(root,three),"broken");
    assert.equal((await newestRecovery(root))?.sequence,2);
    assert.deepEqual(await pruneRecovery(root,2),[one]);
    assert.deepEqual(await listRecovery(root),[two,three]);
    await assert.rejects(readRecovery(root,"../outside"));
    await assert.rejects(pruneRecovery(root,0));
  } finally {
    await rm(root,{recursive:true,force:true});
  }
});

test("workspace diffs apply and reverse without borrowed tags", () => {
  const a = createDocument("a","Old");
  const b = createDocument("b","Removed");
  const next = editDocument(a,{title:"New",tags:["work"]});
  const c = createDocument("c","Added");
  const changes = compare([a,b],[next,c]);
  assert.deepEqual(summary(changes),{added:1,removed:1,changed:1});
  assert.deepEqual(applyChanges([a,b],changes),[next,c]);
  assert.deepEqual(applyChanges([next,c],reverseChanges(changes)),[a,b]);
  const applied = applyChanges([a,b],changes);
  applied[0].tags.push("borrowed");
  assert.deepEqual(next.tags,["work"]);
  assert.throws(() => compare([a,a],[]));
  assert.throws(() => applyChanges([editDocument(a,{title:"Changed elsewhere"}),b],changes));
});

test("controller persists document JSON and preserves undo", async () => {
  const sink = new MemorySink();
  const controller = new Controller(new Writer(sink.save,{
    concurrency:2,maxAttempts:1,retryMs:1,clock:new ManualClock(),
  }));
  let changes = 0;
  const unsubscribe = controller.subscribe(() => { changes++; });
  controller.open("a","Title");
  await controller.edit("a","one");
  assert.equal(controller.status("a").dirty,false);
  assert.equal(JSON.parse(sink.read("a")!).text,"one");
  await controller.rename("a","Renamed");
  assert.equal(controller.status("a").title,"Renamed");
  assert.equal(await controller.undo("a"),true);
  assert.equal(controller.status("a").title,"Title");
  assert.equal(await controller.redo("a"),true);
  await controller.archive("a");
  assert.deepEqual(controller.tabs.all(),[]);
  assert.equal(controller.status("a").saving,false);
  assert(changes > 0);
  unsubscribe();
  await controller.close();
});

test("atomic file adapter preserves unrelated records", async () => {
  const root = await mkdtemp(join(tmpdir(),"sink-test-"));
  try {
    const save = fileSink(root);
    await save({key:"../a",value:"one",generation:1});
    await save({key:"b",value:"two",generation:1});
    const names = await readdir(root);
    assert.equal(names.length,2);
    assert(names.every(name => /^[a-f0-9]{64}\.json$/u.test(name)));
    const records = await Promise.all(names.map(async name => JSON.parse(await readFile(join(root,name),"utf8"))));
    assert.deepEqual(new Set(records.map(row => row.value)),new Set(["one","two"]));
    await save({key:"b",value:"new",generation:2});
    assert.equal((await readdir(root)).length,2);
  } finally {
    await rm(root,{recursive:true,force:true});
  }
});

test("manual clock ordering and cancellation do not depend on sleeps", () => {
  const clock = new ManualClock();
  const events: string[] = [];
  clock.schedule(5,() => { events.push("first");clock.schedule(0,() => events.push("nested")); });
  const cancel = clock.schedule(3,() => events.push("cancelled"));
  clock.schedule(5,() => events.push("second"));
  cancel();
  clock.advance(4);
  assert.deepEqual(events,[]);
  clock.advance(1);
  assert.deepEqual(events,["first","second","nested"]);
  assert.equal(clock.pending(),0);
  assert.equal(clock.now(),5);
});
