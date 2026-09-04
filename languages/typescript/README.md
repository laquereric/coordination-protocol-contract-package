# TypeScript examples

Erasable syntax only (interfaces plus annotations) — plain `node` runs
these with no build step (Node 20+ type stripping). Same contract as the
JavaScript twins.

* `pull/pull.ts` — read access. `CPCP_URL=... node pull.ts [method] [params-json]`
* `push/push.ts` — write access. `CPCP_URL=... node push.ts [method] [params-json] [operation-id]`
  (**writes to the backend** — point at your own pod).

No enums, namespaces, or parameter properties — nothing the stripper
cannot erase. For production builds, compile with `tsc` as usual; the
runtime discipline is unchanged.
