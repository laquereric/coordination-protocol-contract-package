# Refusal taxonomy

Every reason below arrives as data in a never-raise envelope
(`spec/envelope.md`). Seam reasons carry the HTTP class from
`spec/http-mapping.md`; **binding** reasons ride whatever carrier their
road provides, and name it in [Bindings](#bindings). Reasons are stable
strings: renaming one is a breaking contract change (gated where
consumed).

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

---

## Bindings

Everything above is decided by a **seam**: the method ran, or would have,
and the answer is a CPCP envelope over `POST /_cpcp/rpc`. The reasons
below are decided by the **road** — before or around the seam, on a call
that never reaches the dispatcher. There is no method result to put them
in, so each one names the carrier its binding actually has.

`failure_layer` (`domain` | `http_auth` | `http_request` |
`infrastructure`) rides beside `reason` here as everywhere. The HTTP
column is the status of the *exchange*, and is blank where there is no
HTTP exchange to have one. A blank is not an unmapped row; it is a road
without HTTP on it.

### A2A, both roads — [`a2a/`](../a2a/README.md)

| reason | meaning | carrier | layer | HTTP |
|---|---|---|---|---|
| `a2a_unknown_method` | no such A2A JSON-RPC method | JSON-RPC `error` | http_request | 200 |
| `a2a_unsupported_part` | no JSON-LD grant Part in the message | Task `status.state: rejected` | http_request | 200 |
| `a2a_json_not_jsonld` | a Part carried the retired nested JSON-RPC under `data.cpcp`, or a `method` object with no `@context` | Task `status.state: rejected` | http_request | 200 |

200 is not an oversight. The frame was delivered and answered; the
refusal is *in* the frame. Mapping these to 4xx would leave a client
reading status alone unable to tell a rejected Part from an unreachable
host — and the binding already requires both channels to be read
(`a2a/internet/README.md` §7).

A2A rejects the Part **before** the dispatcher runs, so an `a2a_*` reason
and a CPCP reason never appear on the same call. A refused *grant* is
still a completed A2A delivery: `failed`, not `rejected`.

### Intrapod, NATS only — [`a2a/intrapod/`](../a2a/intrapod/README.md)

| reason | meaning | carrier | layer | HTTP |
|---|---|---|---|---|
| `nats_unreachable` | broker silent, client library missing, or request-reply timed out | CPCP envelope at the caller | infrastructure | — |

Raised by the **caller**, not by a seam, and the only reason here that
names a road rather than a message. With `MM_NATS_URL` set there is no
HTTP fallback, so an unreachable broker ends the call — and it ends it as
an envelope, not as an exception across the boundary. A client that
retries the peer over HTTP has reopened the surface the bind exists to
close.

### webmcpld, in a tab — [`webmcpld/`](../webmcpld/README.md)

| reason | meaning | carrier | layer | HTTP |
|---|---|---|---|---|
| `user_declined` | the human in the tab refused the confirmation the page asked for | tool result, `isError: true` | domain | — |
| `origin_not_exposed` | the calling origin is not in this tool's `exposedTo` | tool result, `isError: true` | http_auth | — |
| `page_state_changed` | the tool was unregistered, or the document navigated, between discovery and execution | tool result, `isError: true` | http_request | — |

No HTTP status: the call is in-process, page to agent, with no exchange
to describe. The carrier is a **resolved** tool result — `isError: true`
carrying `ok: false` — because a refusal that rejects the promise is an
exception across the boundary wearing a different coat.

`user_declined` is `domain` on purpose: in a tab the human is the domain
authority, and a decline is a decision the page made, not a failure it
suffered. `origin_not_exposed` is `http_auth` because the browser decides
it, not the page — the page never sees the call.

`page_state_changed` is the one the surface makes inevitable rather than
possible: WebMCP tools appear and vanish with page state, so an agent
holding a handle from a second ago is holding a claim about a document
that has moved on.

`operation_id_required` does not arise in this binding. The page is a
party to the call and mints the id when the caller omits one
(`webmcpld/README.md` §4) — the reason stays in the taxonomy for the
seam, where the caller is the only party who could have named the intent.

### MVI, a workload in a microVM, on [`vsock/`](../vsock/README.md) — proposed

*The reasons are proposed; the binding, its scope and each reason's
`failure_layer` are decided.* Raised by the MVI runtime that boots a workload
from its OCI image (`laquereric/iq`, `Development/UseCase/UC_Mvi`), and by
the guest agent inside the VM. The workload reaches its host only over
vsock: the `sandbox` seam (cpcp_registry `registry/seams.json`) on one
port, the `guest.*` control plane (`not_a_seam`) on another. vsock is
a binding of its own ([`vsock/`](../vsock/README.md)), and its scope is
`pod_internal_*` (decided 2026-10-22). Each reason's `failure_layer`
in the table below is decided too (2026-10-22): `infrastructure` for
what the runtime, its host, a registry, a kernel or a VM could not do;
`http_request` for what the request itself was (a manifest, an image, a
source, an envelope that is not one); `domain` for the guest's process
state. The MVI runtime's tests hold its code to this table (laquereric/iq
UC_Mvi `features/layers.feature`).

The `sandbox` seam's own refusals are the seam reasons above, reused
as they are: `empty_body`, `unparseable_json`, `unknown_operation`,
`operation_id_required`, `missing_params`, `grounding_refused`,
`unauthenticated`, `idempotency_not_durable`, `domain_write_refused`
(the record store refused the receipt), `server_error`. They carry no HTTP
status, since the seam is not published over HTTP.

Egress (`sandbox.fetch`, `sandbox.egress.send`) reuses
`authorization_denied` at `domain` for a target under no producer the
workload's `dependency` manifest declares (another scheme, host or port,
a path outside the producer's, a `..` segment, credentials in the URL):
the admission is refused and nothing is sent. A producer's own answer,
a 4xx or 5xx included, is the method's result, not a refusal. One seam
reason is proposed for it:

| reason | meaning | raised by | carrier | layer | HTTP |
|---|---|---|---|---|---|
| `mvi_producer_unreachable` | the declared producer did not answer (refused, unresolvable, or silent past the seam's timeout); a send that got no answer leaves no receipt, so its `operationId` is still free | the `sandbox` seam | CPCP envelope on vsock | infrastructure | — |

The reasons below are decided by the runtime before or around a boot,
or by the guest agent, and never reach the seam's dispatcher:

| reason | meaning | raised by | carrier | layer | HTTP |
|---|---|---|---|---|---|
| `mvi_manifest_nonconformant` | the image's `.cpcp/` grant fails `check-repo-format.py` or the MVI rules, or the image is not shaped as an MVI | runtime, at pull | CPCP envelope at the runtime's caller | http_request | — |
| `mvi_port_not_declared` | an `ExposedPorts` entry matches no served seam's `exposure` | runtime, at pull | same | http_request | — |
| `mvi_signature_invalid` | a part the boot would use has no signature by a trusted key, or the tag moved between verification and fetch | runtime, before boot | same | infrastructure | — |
| `mvi_source_unpinned` | the workload is no revision (outside git, uncommitted changes, no origin), so its provenance would name a rev that is not it | builder | same | http_request | — |
| `mvi_blob_digest_mismatch` | a fetched blob or manifest does not hash to its digest | runtime | same | infrastructure | — |
| `mvi_pin_unresolved` | a kernel or agent pin names a digest the registry does not hold | runtime | same | infrastructure | — |
| `mvi_rootfs_verity_mismatch` | the disk's dm-verity tree does not give the signed root hash | runtime, on the host before boot; and, where the guest kernel has dm-verity (arm64 on both backends, UC_Mvi slice 20), the guest agent at `guest.up` when the verity device it opened with the signed root hash cannot be mounted. A block changed after the host's check is refused by the guest's kernel to whatever reads it (EIO to a read, SIGBUS to a mapped page) | same | infrastructure | — |
| `mvi_rootfs_unbuildable` | the rootfs could not be flattened, formatted or given its verity tree | builder | same | infrastructure | — |
| `mvi_envelope_loosened` | the operator's resource envelope goes past the image's `dev.mvi.resources` (more vCPUs, memory above the ceiling, a longer wall clock, a device the image does not list) or names a knob the image does not bound; the image's envelope may be tightened, never loosened | runtime, before anything is fetched to boot | same | http_request | — |
| `mvi_isolation_unavailable` | the host cannot meet the image's `isolation.min` (no hypervisor, no backend) | runtime, preflight | same | infrastructure | — |
| `mvi_arch_unavailable` | no platform, disk or kernel for the host's architecture | runtime, preflight | same | infrastructure | — |
| `mvi_boot_failed` | the VMM did not boot the disk | runtime | same | infrastructure | — |
| `registry_refused` | the OCI registry refused or did not answer a push or pull | runtime or builder | same | infrastructure | — |
| `vsock_unreachable` | the peer did not answer on vsock | caller (like `nats_unreachable`) | same | infrastructure | — |
| `guest_protocol_mismatch` | the guest agent speaks another `guest.*` protocol version | runtime, at `guest.up` | same | infrastructure | — |
| `guest_process_exists` | `guest.process.start` after the one process this boot allows | guest agent | `guest.*` envelope on vsock | domain | — |
| `guest_no_process` | `guest.process.signal` with no process running: none started, or it already exited | guest agent | same | domain | — |
| `guest_spawn_failed` | the entrypoint has no command, or it would not exec | guest agent | same | infrastructure | — |

In a pod of microVMs (UC_Mvi slice 16), the runtime's relay between a
FRONT and its BACK refuses with the seam reasons as they are:
`empty_body`, `unparseable_json`, `unauthenticated` (not the FRONT's
relay credential), `unknown_operation` (a method the pod did not
admit), and `vsock_unreachable` when the BACK does not answer. A pod
whose FRONT calls what its BACK does not serve is
`mvi_manifest_nonconformant`, before either boots.

`mvi_*` reasons are envelopes from the runtime to whoever asked it to
pull or boot, so a refused boot is data the operator reads, not a
crashed runtime. `guest_*` reasons are envelopes on the `guest.*` plane
between the runtime and the agent; the workload never sees them.
