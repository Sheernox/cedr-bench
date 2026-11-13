import { test } from "node:test";
import assert from "node:assert/strict";
import { Writer, ManualClock, MemorySink, Session } from "../src/index.ts";

test("independent saves", async () => {
  const sink = new MemorySink();
  const writer = new Writer(sink.save,{concurrency:2,maxAttempts:2,retryMs:10,clock:new ManualClock()});
  await Promise.all([writer.submit("a","one"),writer.submit("b","two")]);
  assert.equal(sink.read("a"),"one");
  await writer.close();
});

test("saved indicator",async () => {
  const sink = new MemorySink();
  const session = new Session(new Writer(sink.save,{concurrency:1,maxAttempts:1,retryMs:1,clock:new ManualClock()}));
  const pending = session.edit("a","text");
  assert.equal(session.dirty("a"),true);
  await pending;
  assert.equal(session.dirty("a"),false);
});
