# vsock

**JSON-RPC 2.0 envelope. JSON-LD payloads. vsock transport, one microVM to its host.**

This is the binding of CPCP for a workload in a microVM (an MVI,
`laquereric/iq` `Development/UseCase/UC_Mvi`). The **frame and the
payloads are the same documents** as [`../a2a/internet/`](../a2a/internet/README.md)
and [`../a2a/intrapod/`](../a2a/intrapod/README.md). Only the road
changes: a VM has no network interface, and vsock (or, on Apple's
Virtualization framework, a Unix socket the host relays into the VM) is
the only road out. A Context or Effect valid on the other bindings is
valid here, and the reverse.

*Decided 2026-10-22: vsock is a binding of its own, and its scope is
`pod_internal_*`.*

---

## 1. Same envelope, different road

| | Internet | Intrapod | vsock (this file) |
|---|---|---|---|
| Frame | JSON-RPC 2.0 | JSON-RPC 2.0 | JSON-RPC 2.0, one request per line, one envelope back |
| Payload | JSON-LD | identical | identical |
| Transport | HTTPS | NATS request-reply | vsock stream to the host (CID 2), or a Unix socket the host relays |
| Auth on the wire | `Authorization: Bearer` header | the same Bearer in a NATS header | the same Bearer in the frame's `authorization` member: there are no headers |
| HTTP status | yes | no | no: refusals are envelopes only |
| Published | yes | no | **never** |

---

## 2. Its scope is `pod_internal_*`

A microVM is not on a pod network, but it is the same case in every way
that matters to [scopes](../spec/scopes.md): the road is never
published, nothing outside the runtime's host can reach it, and the
caller holds a credential the runtime issued at boot. So:

* A workload's calls to its host are `pod_internal_dependencies`. The
  producer is `vsock://host:<port>/_cpcp`.
* A FRONT's calls to the BACK beside it in its pod are
  `pod_internal_dependencies` too, named `vsock://pod/<name>/_cpcp`. The
  two VMs never reach each other: the runtime's relay is in the middle of
  every call ([scopes](../spec/scopes.md), MVI pods).
* What the runtime serves the workload, and what a BACK serves its FRONT
  through the relay, are `pod_internal_services`.
* Nothing on vsock is ever `services`. A workload that should be reached
  from beyond its host is a BACK published by the runtime on another
  binding, never through this one.

---

## 3. The roads

Each road goes one way and is opened only where the workload's role needs
it. What the backend actually opened is the runtime's to measure and
state in its deployment record's `exposure` (repo-format rule 4).

| vsock port | Direction | Plane | Who has it |
|---|---|---|---|
| 7000 | guest → host | the `sandbox` seam | every workload |
| 7001 | host → guest | the `guest.*` control plane (`not_a_seam`, decided) | every workload's agent |
| 7002 | host → guest | a BACK's own seam | a BACK in a pod |
| 7003 | guest → host | the pod relay, to the BACK | a FRONT in a pod |

Where the VMM relays Unix sockets instead (Apple's Virtualization framework
through Containerization), the same planes are files in the guest:
`/run/mvi/sandbox.sock`, `/run/mvi/agent.sock`, `/run/mvi-serve/serve.sock`,
`/run/mvi/pod.sock`. The frames are the same bytes.

---

## 4. Rules this road keeps

* **No other road.** The VM has no network interface. libkrun's implicit
  vsock (TSI), which would hand the guest the host's network, is off.
  Raw networking or a raw mount is an `unscoped_seams` entry with a
  `because`, and it voids the guarantees below.
* **No streams, no callbacks.** Async work is polled, as on every
  binding ([methods](../spec/methods.md)). One connection may carry
  several requests in turn; none carries a subscription.
* **The Bearer is issued at boot and never in the image.** The runtime
  hands it to the process when it starts it. A caller without it is
  `unauthenticated` before CPCP runs.
* **A peer that does not answer is `vsock_unreachable`**, raised at the
  caller as an envelope, like `nats_unreachable` on intrapod. A caller
  sets a timeout: a road that takes the call and never answers is
  unreachable, not a reason to wait out the run.
* **The PUSH intent travels.** A PUSH's `operationId` is the same id on
  every binding. Where the host sends a workload's Effect onward over
  HTTP (`sandbox.egress.send`), it goes as `Idempotency-Key`.

---

## 5. Refusals

The seam reasons are reused as they are; the MVI runtime's and guest
agent's own are in [refusals](../spec/refusals.md), under Bindings, MVI.
