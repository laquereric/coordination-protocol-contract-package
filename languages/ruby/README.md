# Ruby examples

Stdlib only (`net/http`, `json`, `uri`, `securerandom`). No bundles.

* `pull/pull.rb` — read access. `CPCP_URL=... ruby pull.rb [method] [params-json]`
  (default: `note.list`). Prints `{status, envelope}`; exit 0 on `ok: true`.
* `push/push.rb` — write access. `CPCP_URL=... ruby push.rb [method] [params-json] [operation-id]`
  (default: `note.create`, random `operationId`). **Writes to the backend** —
  point at your own pod.

`Net::HTTP#request` parses the body on every status. Helpers that raise on
4xx (`Net::HTTP.get`, Faraday `raise_error`) lose the far side's reason —
never use them on this seam.
