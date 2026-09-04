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

## The two faces of a grant

- **PULL — read access.** A party reads grounded **Context** across
  JSON-RPC-LD, following **CID** (Cyborg Interface Descriptor) `@id`
  references. A read costs nothing and promises nothing.
- **PUSH — write access.** A party writes a typed, closed-shape **Effect**,
  again linked by CID `@id` references. A write carries an `operationId` — the
  actor's word for what it is doing — and an account.

One grant, two faces, different obligations. PULL and PUSH are the mechanism;
read access and write access are what they mean.

## What a CPCP is

A versioned Git repo that packages one profile as a runnable pod:

- a **CID** (JSON-LD `@context` + operation manifest + closed SHACL shapes);
- a **FRONT** OCI image and a **BACK** OCI image (build examples);
- **Python** and **Go** bindings generated from the CID;
- a demo of CID linkage across JSON-RPC-LD — PULL (FRONT→BACK) and PUSH
  (BACK→FRONT).

The package is the point. A grant that cannot be versioned and deployed is a
convention, and conventions drift.

## Standing on

CPCP is layered on the OSI Level 8 base protocol
([json-rpc-ld](https://github.com/laquereric/json-rpc-ld) /
[osi-level-8](https://github.com/laquereric/osi-level-8)). Base and profiles own
the **shapes**; CPCP is the **transport of the grant** and the packaging of it.
Do not restate the base here — depend on it.

This repo is the **standard + registry**. Each CPCP lives in **its own Git repo**.

## Naming & versioning

| Form | Meaning |
|---|---|
| `JSON-RPC-LD-PS1` | the standard (this repo) |
| `JSON-RPC-LD-PS1-P{N}` | the CPCP repo for Profile N (its own Git repo) |
| `JSON-RPC-LD-PS1-P{N}.{VV}` | a **labeled SHA** (a Git tag) pinning a specific commit of that CPCP repo |

These identifiers are unchanged by the rename. `PS1` remains the standard's
name; `CPCP` names what a package of it is.

## Registry

See `registry.json`. Current CPCPs:

- **JSON-RPC-LD-PS1-P1** — Profile 1 (the Cyborg Channel): data sync, three ledgers.
  https://github.com/laquereric/JSON-RPC-LD-PS1-P1
- **JSON-RPC-LD-PS1-P2** — Profile 2 (reference-passing for agents).
  https://github.com/laquereric/JSON-RPC-LD-PS1-P2

Profile specs (moved from osi-level-8) live inside their CPCP repos; the
osi-level-8 repo holds the **Base** and Profile 3 (SwitchYard / market routing).

## Extracted contracts

`spec/` holds the wire formats and protocol rules extracted from the
magentic-stack pod that runs this contract in production: envelopes,
HTTP mapping, idempotency, refusal taxonomy, method conventions, layer
authority, operation identity, plus background positioning.
`registry/` holds the extracted method and seam registries with
provenance. One-way extraction; the monorepo follows this repo pinned.

## Implementations

- **rails-cpcp** — a mountable Rails engine that projects Rails resources as a
  CPCP surface at `/_cpcp`. Read access is `direction: :pull`, write access is
  `direction: :push`; refusals are typed envelopes rather than exceptions, and
  PUSH requires an `operationId`.

## Ontology

`ontology/cpcp-base.ttl` — the foundation vocabulary: `CID`, `Profile`,
`Operation` (+ PULL/PUSH), the three ledgers, records, and `Pod`.

Apache-2.0.
