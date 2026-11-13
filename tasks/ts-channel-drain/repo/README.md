# Channel writer

Autosave queues for editors that write several documents to one storage service.
Run `npm test` on Node 26. TypeScript executes directly; no build step or package
installation is needed. The writer lifecycle is specified in docs/writer.md.

The editor Session adapter relies on acknowledgments to show its Saved state.
Storage adapters provide atomic files or in-memory records. The manual clock
is for deterministic backoff tests, not a replacement for promise scheduling.

A minimal storage integration:

```typescript
import { Writer, systemClock, fileSink } from "./src/index.ts";

const writer = new Writer(fileSink("./saves"), {
  concurrency: 3,
  maxAttempts: 3,
  retryMs: 250,
  clock: systemClock,
});

await writer.submit("draft", "First draft");
await writer.flush();
await writer.close();
```

Workspace, History and Tabs manage local editor state. Controller combines them
with Session, while recovery bundles are independent snapshots for explicit
backup and restore. The journal adapter supports append-only storage and
compaction. Its physical frame ordering does not replace the writer's logical
per-document ordering or durable acknowledgment contract.
