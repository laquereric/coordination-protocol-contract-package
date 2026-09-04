# JavaScript examples

Node `fetch` (mirrors the pod's switch UI client). No installs.

* `pull/pull.mjs` — read access. `CPCP_URL=... node pull.mjs [method] [params-json]`
  (default: `note.list`). Prints `{status, envelope}`; exit 0 on `ok: true`.
* `push/push.mjs` — write access. `CPCP_URL=... node push.mjs [method] [params-json] [operation-id]`
  (default: `note.create`, random `operationId`). **Writes to the backend** —
  point at your own pod.

`fetch` rejects on network failure, never on HTTP errors — a non-200
status still carries the envelope, which is always read.
