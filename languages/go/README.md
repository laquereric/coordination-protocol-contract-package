# Go examples

Stdlib only (`net/http`, `encoding/json`, `crypto/rand`). No modules needed
for `go run`.

* `pull/pull.go` — read access. `CPCP_URL=... go run pull.go [method] [params-json]`
* `push/push.go` — write access. `CPCP_URL=... go run push.go [method] [params-json] [operation-id]`
  (**writes to the backend** — point at your own pod).

The body is decoded on every status: a non-200 still carries the envelope.
Transport failures return `{ok: false, reason: unreachable}` — never
mistake those for a refusal.
