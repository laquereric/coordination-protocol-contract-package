# Demo: PushNote and PullNote CIDs, executable

Two CID documents plus a stub seam that implements them, so the contract
is runnable with nothing installed beyond toolchains:

* `pull-note.cid.json` — read notes by reference (costs nothing).
* `push-note.cid.json` — write a typed, closed-shape Effect named by an
  `operationId` (repeats return the first receipt).
* `shapes/note-shape.ttl` — the single canonical shape both CIDs embed;
  `check-shapes.py` fails on divergence (`SHAPES.json` records the digest).
* `server.py` — in-memory stub (`note.list`, `note.create`,
  `/up`, `/_cpcp/up`, `/_cpcp/cid.json`). State evaporates with the process.
* `run-demo.sh` — shape check, then every language present on the
  machine (pull, push, replay, pull). Missing toolchains SKIP loudly;
  any real failure fails the run.

```bash
./run-demo.sh
```
