# coordination-protocol-contract-package — CPCP

**CPCP is coordination-protocol-contract-package.**

> The affordance a deterministic entity grants a non-deterministic entity.

A conventional system is deterministic: one writer, one shape, one journal. An
agent is not — it proposes, it can be wrong, it retries. CPCP is the seam where
the first grants access to the second, on terms, packaged so the grant can be
versioned and deployed.

That sentence is not a slogan. The rules below follow from it: a deterministic
system that lets a non-deterministic one in must be able to say afterwards
**what was done and on whose word**.

## CPCP is not authentication and not authorization

CPCP is a **semantic data compatibility and effect guardrail** system. It answers
whether a message means what its contract says it means, whether the effect it
asks for is one the seam admits, and whether what happened can be read back
afterwards. It runs **alongside** conventional authentication and authorization,
not instead of them, and it replaces neither.

**None of the CPCP machinery comes into play until those systems have granted
permission to perform the actions described in a CPCP `package.json`.** Identity
is established first, and the right to perform the operation is granted first.
Only then does CPCP ask its own questions: is this payload the shape the contract
declares, does this PUSH name its intent, does the response carry what the
operation promised, and is there a journal entry saying it happened. A caller who
has not been authenticated and authorized never reaches a shape check, because
there is nothing here that would stop them.

The division is worth stating plainly because a guardrail is easy to mistake for
a gate. A shape refusing a malformed Effect is not an access decision. A closed
vocabulary is not a permission. An `operationId` makes a retry the same write
rather than a second one; it does not say who may write. Read the other way, a
system that treated a conforming payload as an authorized one would have
misplaced its security boundary — CPCP would be answering a question it was never
given the evidence to answer.

## The two faces of a grant

- **PULL — read access.** A party reads grounded **Context** across
  JSON-RPC-LD, following **CID** (Cyborg Interface Descriptor) `@id`
  references. A read costs nothing and promises nothing.
- **PUSH — write access.** A party writes a typed, closed-shape **Effect**,
  again linked by CID `@id` references. A write carries an `operationId` — the
  actor's word for what it is doing. Authentication travels out of band
  (Bearer credentials the deployment issues); it is not a wire field.

One grant, two faces, different obligations. PULL and PUSH are the mechanism;
read access and write access are what they mean. Data direction, stated
once: PULL means FRONT reads from BACK; PUSH means FRONT publishes to
BACK. (HTTP requests travel caller-to-seam in both cases; the arrows
above are data flow, not transport.)

## What a CPCP is

A versioned Git repo that packages one profile as a runnable pod:

- a **CID** (JSON-LD `@context` + operation manifest + closed SHACL shapes);
- **language examples** that push and pull through the seam;
- an **executable demo** (stub seam plus a runner driving the examples).

The package is the point. A grant that cannot be versioned and deployed is a
convention, and conventions drift. Pod artifacts (OCI images, generated
bindings) live in profile repositories when they exist; this repo holds the
contract. The reference demo — PushNote/PullNote CIDs, stub seam, and
push/pull clients in eight languages — lives next door, in its own repo:

**[cpcp_demo](https://github.com/laquereric/cpcp_demo)**

## Repo format

Every CPCP package repo follows the canonical layout. Machine readers
start at `.cpcp/package.json`; humans start at `README.md`.

```text
.cpcp/package.json            index: kind, version, contract rev, registry
                              by SHA, unscoped seams, gates
.cpcp/<scope>/package.json    one per scope the repo SERVES: its definition,
                              seams, measured exposure, invariants
demo/                         CIDs (*.cid.json), stub seam (server), matrix
                              runner, shape check, canonical shapes
languages/<lang>/             README plus examples/{push,pull} clients
```

Full rules, field tables and a worked example: [repo format](spec/repo-format.md).
A repo that serves no seam carries the index alone.

This repo (the contract home) carries `spec/`, `ontology/`,
and `PROVENANCE.json` instead of a demo of its own: the demo lives in
`cpcp_demo` so the contract never depends on example code, and the
registries live in `cpcp_registry`.

## Standing on

CPCP is layered on the base protocol
([json-rpc-ld](https://github.com/laquereric/json-rpc-ld)). Base owns
the **shapes**; CPCP is the **transport of the grant** and the packaging of it.
Do not restate the base here — depend on it.

This repo is the **standard**. Each CPCP lives in **its own Git repo**.
Naming, versioning, and the method/seam registries live in
[cpcp_registry](https://github.com/laquereric/cpcp_registry).

## Registry

Lives in [cpcp_registry](https://github.com/laquereric/cpcp_registry):
profile entries (only public, stable repos — no dead links), the method
registry, and the seam registry. The demo CIDs live in
[cpcp_demo](https://github.com/laquereric/cpcp_demo) and are the runnable
reference, not registry entries anywhere.

## Extracted contracts

`spec/` holds the wire formats and protocol rules extracted from the
magentic-stack pod that runs this contract in production: envelopes,
HTTP mapping, idempotency, refusal taxonomy, method conventions, layer
authority, operation identity, scopes, plus background positioning.
One-way extraction; the monorepo follows this repo pinned.

## Implementations

Clients live in [cpcp_demo](https://github.com/laquereric/cpcp_demo)
(`languages/`, eight languages) — PULL and PUSH examples against any
`/_cpcp` endpoint:

| Language | Transport | Notes |
|---|---|---|
| Python | `urllib`, stdlib only | reference behavior |
| Ruby | `net/http`, stdlib only | reads bodies on every status |
| JavaScript | `fetch` | mirrors the reference |
| TypeScript | erasable syntax, plain `node` runs it | same contract, typed |
| Go | `net/http`, stdlib only | |
| Java | `java.net.http`, single-file run | stdlib has no JSON parser: full body prints, `ok` scanned |
| C | POSIX sockets, no dependencies | minimal HTTP/JSON; plain `http://` only |
| C++ | POSIX sockets, `std::string` | same limits as C |

Read access is pull, write access is push; refusals are typed envelopes
rather than exceptions, and PUSH carries an `operationId`.

## Namespaces

Three roots, each authoritative for its layer — terms, operations, and
message envelopes are separate concerns, never one vocabulary:

| Root | Owns | Example |
|---|---|---|
| `https://w3id.org/cpcp/ns#` | payload terms (`@vocab`) | `cpcp:Note` |
| `https://w3id.org/cpcp/osi8/...` | operation identity | `.../persist#path.set` |
| JSON-RPC-LD (`json-rpc-ld` repo) | message structure, `@context` mechanics, SHACL validation | `jsonrpc`, `id`, `@context` |

W3C/RDF core namespaces (`rdf:`, `rdfs:`, `owl:`, `xsd:`) are
foundational identifiers, not dependencies. No other external namespace
appears in this tree.

## Ontology

`ontology/cpcp-base.ttl` — the foundation vocabulary: `CID`, `Profile`,
`Operation` (+ PULL/PUSH), the three ledgers, records, and `Pod`.

Apache-2.0.
