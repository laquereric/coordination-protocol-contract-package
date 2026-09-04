# Operation identity

Three systems identify the "same" capability three ways: Hydra by
resource/operation IRI, WebMCP by tool name, JSON-RPC by method name.
CPCP fixes a canonical IRI per business capability and maps it
explicitly, so a tool name or method string is never the only source of
meaning (logging, authorization, auditing, and schema evolution all key
off the canonical form).

## Convention

```
https://w3id.org/cpcp/osi8/<seam>#<Method>
```

Examples: `.../vault#secret.put`, `.../bus#projection.latest`,
`.../persist#path.set`, `.../mind#reading.latest`.

Redirects are UNPUBLISHED: W3ID is durable redirect plus stewardship,
not a magic availability guarantee, and no redirect exists yet. IRIs
are intent until they resolve — recorded as such in
`registry/methods.json`, never implied to dereference.

## JSON-LD contexts

LD-profile payloads carry `@context` mapping terms to IRIs
(`@vocab`, `id`→`@id`, `type`→`@type`, `operationId`). SHACL shapes are
the normative payload contracts, and they live in exactly two places:

* **Production profile CIDs** live in their profile repositories
  (closed, versioned) — not in this repo; duplicating them here would
  drift at two rates.
* **Standalone/reference CIDs** (`demo/push-note.cid.json`,
  `demo/pull-note.cid.json`) carry their shapes inline **because there
  is no profile repository for the demo** — and the single canonical
  copy is `demo/shapes/note-shape.ttl` (versioned, digested in
  `demo/SHAPES.json`), which `demo/check-shapes.py` enforces on every
  demo run. Inline here means portable, not second-sourced.

A consumer validates against the profile's shapes; this repo states the
envelope and reason contracts those shapes plug into.
