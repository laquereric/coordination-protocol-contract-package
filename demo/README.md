# Demo: PushNote and PullNote CIDs, executable

Two CID documents plus a stub seam that implements them, so the contract
is runnable with nothing installed beyond Python 3:

* `pull-note.cid.json` — read notes by reference (costs nothing).
* `push-note.cid.json` — write a typed, closed-shape Effect named by an
  `operationId` (repeats return the first receipt).
* `server.py` — in-memory stub (`note.list`, `note.create`,
  `/up`, `/_cpcp/cid.json`). State evaporates with the process.
* `run-demo.sh` — boots the stub, pulls, pushes twice under one
  operation id (second call replays), pulls again. All green means the
  loop in `../languages/` works end to end.

```bash
./run-demo.sh
```

Every other language under `../languages/` speaks the same seam: point
`CPCP_URL` at the running stub (it prints nothing; default the examples
at `http://127.0.0.1:18080/_cpcp` or export the variable).
