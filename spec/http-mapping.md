# HTTP mapping (dual-signal)

CPCP keeps HTTP 200 only for an intentionally completed RPC method whose
result is a **domain decision**. Endpoint failures use HTTP error
statuses. JSON-RPC 2.0 is transport-agnostic and prescribes no HTTP
mapping; the mapping is CPCP policy. The body stays a never-raise
envelope in every case. Status describes the transport/outcome of the
exchange. A client MUST inspect both channels: never infer an
application reason from status alone.

Source: GAP109 (contract freeze). Row 49 KEEP BOTH.

## Mapping (POST `/_cpcp/rpc`)

| class | HTTP | layer | retry |
|---|---|---|---|
| grounding (`grounding_refused`) | 200 | domain | no |
| admission (`authorization_denied`) | 200 | **owner** (never a wire value) | no |
| parse (`empty_body`, `unparseable_json`) | 400 | http_request | no |
| unauthenticated | 401 | http_auth | no |
| forbidden | 403 | http_auth | no |
| not-found HTTP target | 404 | http_request | no |
| request-document SHACL | 422 | http_request | no (no live producer) |
| `outbox_not_installed` / `outbox_schema_check_failed` / unexpected | 500 | infrastructure | no |
| GRAPH invalid upstream | 502 | infrastructure | no |
| `graph_unreachable` / `sqlite_busy` | 503 | infrastructure | conditional |
| GRAPH timeout | 504 | infrastructure | no |
| `idempotency_not_durable` | 503 | infrastructure | no |

Grounding is HTTP 200: the method ran and decided. 422 is reserved for a
well-formed request whose request *document* fails SHACL before dispatch
(no live producer); it must not relabel `grounding_refused`.

`failure_layer` (`domain` | `http_auth` | `http_request` |
`infrastructure`) rides on `error` next to `reason`/`because` under
`dual-v1`. Admission's layer is the sentinel `owner` until filled — the
mapper must not guess.

## Rules

* 503 is not a general retry signal. `Retry-After` only with a known
  window **and** safe replay (idempotency key present, or idempotent
  method). A non-idempotent POST without a durable key is never retried
  on 503. `retryable` is not a wire field in v1.
* 404 refusals are `Cache-Control: no-store`. POST is not cacheable
  without explicit freshness metadata.
* 401 carries `WWW-Authenticate: Bearer`. The envelope may repeat the
  signal; it must not replace the header.
* `GET /_cpcp/up` and `GET /_cpcp/cid.json` stay 200. They are not RPC
  method results.

## Profiles and rollout

* Default profile: `legacy-all-200` (today).
* Flag: `CPCP_HTTP_STATUS_PROFILE=dual-v1`; header
  `CPCP-HTTP-Status-Profile: dual-v1`.
* Enable method by method, reads/idempotent first, only after clients
  read error bodies (a client that raises on non-200 without reading
  the body breaks the first time a method flips — fix the client, not
  the refusal signal).
