# cyborg-pod-contract-package — PubSubStandard_1 (JSON-RPC-LD-PS1)

**PubSubStandard_1**, canonically **JSON-RPC-LD-PS1**, is a pub/sub delivery standard
layered on the OSI Level 8 base protocol
([json-rpc-ld](https://github.com/laquereric/json-rpc-ld) /
[osi-level-8](https://github.com/laquereric/osi-level-8)). It defines how a grounded
capability surface is **packaged, versioned, and deployed** as a runnable pod — a
**Cyborg Pod Contract Package (CPCP)**.

This repo is the **standard + registry**. Each CPCP lives in **its own Git repo**.

## The two primitives

- **PULL** — a party reads grounded **Context** across JSON-RPC-LD, following **CID**
  (Cyborg Interface Descriptor) `@id` references (FRONT ↔ BACK).
- **PUSH** — a party writes a typed, closed-shape **Effect** across JSON-RPC-LD,
  again linked by CID `@id` references.

## What a CPCP is

A CPCP is a versioned Git repo that packages one profile as a runnable pod:

- a **CID** (JSON-LD `@context` + operation manifest + closed SHACL shapes);
- a **FRONT** OCI image and a **BACK** OCI image (build examples);
- **Python** and **Go** bindings generated from the CID;
- a demo of the **CID linkage** across JSON-RPC-LD — **PULL** (FRONT→BACK) and
  **PUSH** (BACK→FRONT).

## Naming & versioning

| Form | Meaning |
|---|---|
| `JSON-RPC-LD-PS1` | the standard (this repo) |
| `JSON-RPC-LD-PS1-P{N}` | the CPCP repo for Profile N (its own Git repo) |
| `JSON-RPC-LD-PS1-P{N}.{VV}` | a **labeled SHA** (a Git tag) pinning a specific commit of that CPCP repo |

## Registry

See `registry.json`. Current CPCPs:

- **JSON-RPC-LD-PS1-P1** — Profile 1 (the Cyborg Channel): data sync, three ledgers.
  https://github.com/laquereric/JSON-RPC-LD-PS1-P1
- **JSON-RPC-LD-PS1-P2** — Profile 2 (reference-passing for agents).
  https://github.com/laquereric/JSON-RPC-LD-PS1-P2

Profile specs (moved from osi-level-8) now live inside their CPCP repos; the
osi-level-8 repo holds the **Base** and Profile 3 (SwitchYard / market routing).

Apache-2.0.
