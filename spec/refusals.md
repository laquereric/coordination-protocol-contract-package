# Refusal taxonomy

Every reason below arrives as data in a never-raise envelope
(`spec/envelope.md`) with the HTTP class from `spec/http-mapping.md`.
Reasons are stable strings: renaming one is a breaking contract change
(gated where consumed).

## Universal (every seam)

| reason | meaning |
|---|---|
| `empty_body` | request body was empty |
| `unparseable_json` | body was not a JSON object |
| `unknown_operation` | no such method (includes the method name in `because`) |

## Admission and grounding (BACK)

| reason | meaning |
|---|---|
| `grounding_refused` | domain payload failed SHACL after the method ran (HTTP 200) |
| `authorization_denied` | admission refused as a completed method result (HTTP 200) |
| `operation_id_required` | PUSH without an `operationId` |
| `missing_params` | required params absent |

## Durability and stores

| reason | meaning |
|---|---|
| `idempotency_not_durable` | store cannot outlive the process; effect proceeds |
| `idempotency_store_unavailable` | store unreadable; treated as not-cached |
| `outbox_not_installed` / `outbox_schema_check_failed` | projection outbox missing or wrong shape |
| `graph_unreachable` | GRAPH store unreachable (with restoration) |
| `sqlite_busy` | writer contention past timeout (first real customer: backjob loop) |
| `domain_write_refused` | ROLE attempted a write outside its declared split (`role`, `model`/`table` in `because`) |

## Vault (`vault.secret.*`)

`vault_callers_missing`, `vault_callers_unparseable`,
`vault_callers_token_missing`, `vault_secret_absent` (404),
plus allowlist `unauthenticated` (401) / `forbidden` (403). Config-admin
can never `get` (read-back asymmetry) — that refusal is by design, not
an error path.

## Persist (`persist.path.*`)

`unknown_store` (with the known list), `unknown_path` (not a closed-set
member), `persist_unauthenticated` (401), `persist_forbidden` (403),
`persist_callers_missing` (500, server misconfig).

## MIND (`mind.*`)

`mind_unauthenticated` (401), `mind_forbidden` (403),
`mind_callers_missing` / `mind_callers_unparseable` /
`mind_callers_token_missing` / `mind_callers_token_collision` /
`mind_callers_unknown_operation` (500s, server misconfig),
`invalid_request` (malformed admission), `mind_queue_full` (429,
bounded FIFO).

## Switch (LLM plane)

`missing_credential` (401, no usable key — same shape whether absent,
unconfigured, or refused upstream: no fallback credential exists),
`unknown_model`, `local_not_configured` (503), `pin_unavailable` (502),
`browser_origin_rejected` (403, data plane is not for browsers),
`invalid_json`, `not_found`, `server_error`, `no_pin`,
`target_required`, `vendor_required`, provider `provider_http` (upstream
status carried inside `because`).

## Shape and catalog

`shape_catalog_empty`, `shape_id_unresolved`. An empty catalog answers `ok:false`, never `ok:true` with an
empty list.
