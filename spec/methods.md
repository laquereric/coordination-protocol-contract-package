# Method contract conventions

Source: `registry/methods.json` (extracted copy of the manifested
boundary). Conventions every method follows; the registry states the
per-method facts.

## Identity

* Wire name: `<domain>.<verb>` (`vault.secret.put`, `bus.projection.latest`).
* Operation IRI: `https://w3id.org/cpcp/osi8/<seam>#<Method>` (see
  `spec/identity.md`). Redirects are not yet published; IRIs are intent
  until they resolve.
* Exactly two endpoint roles per method — a producer and named
  consumer(s). No wildcard all-services role. Unbuilt callers are named
  as such (`"none yet"`, `"approved, unbuilt"`), never implied.

## Direction

All calls are caller-to-seam request/response. There are no push
notifications, no subscriptions, no callbacks into callers. Async work
is polled (`projection.latest`), never pushed.

## Params and result

* `params` is always an object; missing defaults to `{}`.
* Results are plain data (hashes, booleans, strings, numbers, arrays,
  null) so Ruby, Python, and JS consume them identically. No result
  monads, no sentinel values, no out-parameters.
* Placement/record methods answer `live_applied: false` with an
  `effective` horizon when recording differs from applying — a reader
  must never mistake a recording for an application.

## Versioning

Breaking classes (method removed/renamed, required params added,
envelope keys removed/renamed, result narrowed): bump the seam's
contract version and serve it on the wire. Additive changes (optional
params, new methods, new columns) do not bump. Participants pin to a
version and refuse a superseded contract.
