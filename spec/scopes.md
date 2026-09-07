# Scopes

A scope answers two questions at once: **which way the call runs, and how
far**. Both are named, so neither has to be inferred.

| | **calls** (outbound) | **serves** (inbound) |
|---|---|---|
| **beyond the pod** | `dependency` | `services` |
| **within the pod** | `pod_internal_dependencies` | `pod_internal_services` |

The method contract is identical at every scope; reach is not. A seam
served both inside the pod and beyond it appears in **two** manifests —
one seam under two rules, never two seams (repo-format rule 1). A repo
that only calls carries only calling manifests; a repo that only serves
carries only serving ones.

Direction decides the field: a calling scope carries `depends_on`, a
serving scope carries `seams`. They are not interchangeable — a repo does
not serve what it depends on.

Being inside the pod does not make a caller a server. A container that
calls `vault.secret.get` beside it is a `pod_internal_dependencies` entry
even though the seam it calls is a `pod_internal_services` entry of
whoever serves it — the same seam, seen from its two ends.

## The four scopes

### `dependency` — a CID this repo calls, served elsewhere

* Entries are **not seams of this repo**. They name a producer, the CID
  that describes it, and the operations this repo actually calls. The
  producer is somebody else's `services` scope.
* Declare an operation here whether or not it is built yet. A dependency
  on an unpublished operation is a real dependency and the most useful
  one to write down — `status` records which, and `because` says how it
  was determined.
* No exposure block: exposure is the producer's property to measure and
  state, not this repo's to assert.

### `pod_internal_dependencies` — a seam this repo calls beside it

* Entries are **not seams of this repo**, same as `dependency`. What
  differs is reach: the producer is a container on the same pod network,
  not a host somewhere else.
* This is the side that holds the caller token. A container without its
  token does not start, so an undeclared pod-internal dependency is a
  boot failure waiting for a deploy — which is the argument for writing
  it down rather than leaving it to the compose file.
* No exposure block: the producer measures its own.

### `pod_internal_services` — served to containers beside this one

* Pod-network traffic between containers: BACK, BACKJOB, vault, bus,
  persist, MIND's seam, switch data plane, graph. Ports unpublished
  (`expose`, never `ports:`).
* Callers allowlisted per seam (`*_CALLERS`), Bearer tokens, fail-closed
  boot on empty allowlists. A container without its caller token does
  not start; a caller without the operation does not pass.
* Refusal to an unauthenticated or unallowlisted caller is 401/403 plus
  envelope — designed behavior, not an error path.
* An `exposure` block here proves the *negative* — that these ports are
  not published — and rule 4 wants that measured like any other.

### `services` — served to callers beyond this pod

* Everything this repo serves that something outside its pod can reach:
  host-published loopback for operators, editors and browsers (FRONT
  page, host BACK, config UI), and anything served to the open internet.
* **How far it actually reaches is measured, not assumed.** Loopback and
  internet-facing are both `services`; which one a surface is belongs in
  its `exposure` block with evidence naming the file it was read from
  (repo-format rule 4). A published port never widens what the seam
  admits.
* Operator surfaces keep read-back asymmetry where it matters
  (config-admin writes secrets it can never read back).

### Where "public" went

`public` was a scope until it was two claims wearing one name: *this repo
serves it* and *the open internet can reach it*. The first is
`services`. The second is exposure, which rule 4 already requires to be
measured — and measuring it is what caught four ports asserting loopback
while bound to `0.0.0.0`. A scope name cannot be measured; an exposure
block can.

Public still carries its own obligations wherever a `services` surface is
internet-reachable: no credentials, no real data, replay-safe to observe.
A public endpoint that admits a real write is a defect, not a demo.

## Method-to-scope map

| Seam | Methods | Scopes |
|---|---|---|
| back | `note.*`, journal/session/graph operations | pod_internal_services (pod BACK) + services (host BACK) |
| vault | `vault.secret.put/list/get` | pod_internal_services (config, switch callers) |
| bus | `bus.projection.latest` | pod_internal_services (no production caller yet) |
| persist | `persist.path.set/get` | pod_internal_services (config-admin caller) |
| mind | `mind.reading.latest`, `mind.cognition.request`, `mind.up` | pod_internal_services (conformance, debug) |
| switch data | `/v1/*` completions | pod_internal_services (MIND only; browsers rejected) |
| switch UI | `/api/*` sources/refresh/verify/test | pod_internal_services (config-admin display; host port retired) |
| demo stub | `note.list`, `note.create` | services (internet-reachable; evaporating state only) |

Adding a scope to a seam is a contract change: update this table, the
seam's gate, and the demo matrix runner — never just the compose file.

Adding a `dependency` is a contract change on the **caller's** side only.
It records what this repo has come to rely on; it obliges the producer
to nothing it has not already published.
