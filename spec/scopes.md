# Scopes

Every CPCP seam is reachable at exactly one scope. Scope decides who may
call, over what network, with what credential — the method contract is
identical at every scope, but exposure is not. A method reachable at two
scopes (e.g. BACK's seam inside the pod and on the host) is the same
method under two exposure rules, never two methods.

## The three scopes

### `public_cpcp` — exposed to public, like the demo

* No credentials, no real data, no published ports beyond loopback on
  the operator's own machine. The reference surface is the demo stub
  plus the language examples pointed at it.
* Anything public must be replay-safe to observe: reads only, or writes
  against evaporating demo state. A public endpoint that admits a real
  write is a defect, not a demo.
* Auth: none. Refusals still apply (unknown methods refuse everywhere).

### `pod_internal_cpcp` — exposed to coordinate containers

* Pod-network traffic between containers: BACK, BACKJOB, vault, bus,
  persist, MIND's seam, switch data plane, graph. Ports unpublished
  (`expose`, never `ports:`).
* Callers allowlisted per seam (`*_CALLERS`), Bearer tokens, fail-closed
  boot on empty allowlists. A container without its caller token does
  not start; a caller without the operation does not pass.
* Refusal to an unauthenticated or unallowlisted caller is 401/403 plus
  envelope — designed behavior, not an error path.

### `pod_external_cpcp` — exposed within the ecosystem

* Host-published loopback surfaces for operators, editors, and browsers:
  FRONT page, host BACK (`/_cpcp` for editor shells and curl), config UI.
  Reachable from the host, never from the open internet.
* Operator surfaces keep read-back asymmetry where it matters
  (config-admin writes secrets it can never read back).
* No direct domain writes except through CPCP admission — publishing a
  port never widens what the seam admits.

## Method-to-scope map

| Seam | Methods | Scopes |
|---|---|---|
| back | `note.*`, journal/session/graph operations | pod_internal (pod BACK) + pod_external (host BACK) |
| vault | `vault.secret.put/list/get` | pod_internal (config, switch callers) |
| bus | `bus.projection.latest` | pod_internal (no production caller yet) |
| persist | `persist.path.set/get` | pod_internal (config-admin caller) |
| mind | `mind.reading.latest`, `mind.cognition.request`, `mind.up` | pod_internal (conformance, debug) |
| switch data | `/v1/*` completions | pod_internal (MIND only; browsers rejected) |
| switch UI | `/api/*` sources/refresh/verify/test | pod_internal (config-admin display; host port retired) |
| demo stub | `note.list`, `note.create` | public (evaporating state only) |

Adding a scope to a seam is a contract change: update this table, the
seam's gate, and the demo matrix runner — never just the compose file.
