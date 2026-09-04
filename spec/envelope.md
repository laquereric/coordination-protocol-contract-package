# Envelope formats

Never raise across the boundary. Every CPCP response is an envelope; every
failure is data (`ok: false` plus a reason), never an exception, a dropped
connection, or a bare status.

Sources: `gems/rails-cpcp/lib/rails_cpcp/envelope.rb`,
`request_body.rb`, `dispatcher.rb`; bus/vault/persist controllers;
`runtimes/mind-pod/mind/mind_seam.py`.

## Request

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "note.list",
  "params": {},
  "operationId": "mind-reading-a1b2c3d4e5f60718"
}
```

* `jsonrpc` is always `"2.0"`. `id` echoes back verbatim on every
  response, including refusals (it may be `null` when no id was parsed).
* `method` names the operation (`<domain>.<verb>` by convention).
* `params` is an object (JSON-LD `@context` lives here on LD profile
  methods). Missing params default to `{}`; non-object params are
  `unparseable_json`.
* `operationId` names intent before performing it (see
  `idempotency.md`). PUSH methods require it.

Body parse outcomes, in order: empty body → `empty_body`; unparseable or
non-object → `unparseable_json`. These are distinct reasons and must not
collapse into `unknown_operation`.

## Success

```json
{
  "jsonrpc": "2.0",
  "@context": {"@vocab": "https://w3id.org/laquereric/cpcp/ns#", "id": "@id", "type": "@type"},
  "id": 1,
  "ok": true,
  "result": { "...": "..." }
}
```

Collections return `result: {"@graph": [...]}`. `@context` carries the
`@vocab` plus `id`/`type`/`operationId` mappings on LD-profile methods.

## Refusal: nested form

```json
{
  "jsonrpc": "2.0",
  "@context": { "...": "..." },
  "id": 1,
  "ok": false,
  "error": { "reason": "unknown_operation", "because": "no CPCP operation \"nope\"" }
}
```

The reason lives under `error`. Clients must read `error.reason`, not a
top-level `reason` that is not there.

## Refusal: flat form (hand-rolled seams)

```json
{
  "ok": false,
  "reason": "unknown_store",
  "because": { "store": "vault" },
  "jsonrpc": "2.0",
  "id": 1
}
```

Both shapes are stable; they are not unified (flattening the nested
envelope would break its consumers). A client MUST handle both
locations. See `spec/refusals.md` for the reason taxonomy and
`spec/http-mapping.md` for which HTTP status each class arrives with.

## Restoration (optional, all-or-nothing)

A refusal may carry `cpcp.restoration` with exactly four members —
`state_reached`, `inconsistency`, `restore_when`, `restore_action`.
Any blank member drops the whole object. See `spec/refusals.md`.
