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
calls a secret-store method beside it is a `pod_internal_dependencies`
entry even though that same method is a `pod_internal_services` entry of
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
* This is the side that holds the caller credential. Where a deployment
  boots fail-closed on a missing one, an undeclared pod-internal
  dependency is a boot failure waiting for a deploy — which is the
  argument for writing it down rather than leaving it to a compose file.
* No exposure block: the producer measures its own.

### `pod_internal_services` — served to containers beside this one

* Pod-network traffic between containers, with ports unpublished
  (`expose`, never `ports:`).
* Callers allowlisted per seam, with credentials the deployment issues
  out of band. A caller without the operation does not pass; where boot
  is fail-closed, a container without its credential does not start.
* Refusal to an unauthenticated or unallowlisted caller is 401/403 plus
  envelope — designed behavior, not an error path.
* An `exposure` block here proves the *negative* — that these ports are
  not published — and rule 4 wants that measured like any other claim.

### `services` — served to callers beyond this pod

* Everything this repo serves that something outside its pod can reach:
  host-published surfaces for operators and browsers, and anything
  served to the open internet.
* **How far it actually reaches is measured, not assumed.** Loopback and
  internet-facing are both `services`; which one a surface is belongs in
  its `exposure` block with evidence naming the file it was read from
  (repo-format rule 4). A published port never widens what the seam
  admits.
* Where a surface is internet-reachable it carries obligations a loopback
  one does not: no credentials, no real data, replay-safe to observe. An
  internet-facing endpoint that admits a real write is a defect unless
  the credential story for it is stated.
* An operator surface may keep read-back asymmetry — a writer that can
  never read back what it wrote — where the deployment calls for it.

## Changing a scope

Adding a scope to a seam is a contract change: update the seam's gate
and whatever runs its conformance matrix, never just the compose file.

Adding a `dependency` is a contract change on the **caller's** side only.
It records what this repo has come to rely on; it obliges the producer
to nothing it has not already published.

---

## Notes

Scope names are contract; the deployments below are illustration. CPCP is
not any one of them, and nothing in the definitions above should be read
as naming a particular seam, role or container.

**[1] A worked method-to-scope map.**
[magentic-stack](https://github.com/laquereric/magentic-stack) runs this
contract in production and maps its own seams like this. It is an example
of the shape, not part of the specification — another deployment's map
would name entirely different seams and be equally correct.

| Seam | Methods | Scopes |
|---|---|---|
| back | `note.*`, journal/session/graph operations | pod_internal_services (pod BACK) + services (host BACK) |
| vault | `vault.secret.put/list/get` | pod_internal_services |
| bus | `bus.projection.latest` | pod_internal_services |
| persist | `persist.path.set/get` | pod_internal_services |
| mind | `mind.reading.latest`, `mind.cognition.request`, `mind.up` | pod_internal_services |
| switch data | `/v1/*` completions | pod_internal_services |
| switch UI | `/api/*` sources/refresh/verify/test | pod_internal_services |

`back` appearing twice is rule 1: one seam, two reaches.

**[2] Why exposure is measured rather than declared.**
In magentic-stack on 2026-09-05, four published ports bound `0.0.0.0`
while both scope manifests said "host loopback, never the open internet".
In magentic-market-ai-site on 2026-09-07, two more did the same. Nothing
was wrong with either sentence; it just was not what the files did. Both
repos now hold it with a checker.
