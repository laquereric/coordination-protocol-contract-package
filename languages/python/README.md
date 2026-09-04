# Python examples

Stdlib only (`urllib`, `json`, `uuid`). No installs.

* `pull/pull.py` — read access. `CPCP_URL=... python3 pull.py [method] [params-json]`
  (default: `note.list`). Prints `{status, envelope}`; exit 0 on `ok: true`.
* `push/push.py` — write access. `CPCP_URL=... python3 push.py [method] [params-json] [operation-id]`
  (default: `note.create`, random `operationId`). **Writes to the backend** —
  point at your own pod.

Both files never raise across the boundary: refusals, unreachable hosts,
and unparseable bodies all return `{ok: false, reason, because}`. A
non-200 status still carries the envelope — read the error body.
