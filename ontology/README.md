# CPCP base ontology (Data perspective)

CPCP is **coordination-protocol-contract-package**. The vocabulary IRI and every
term below are unchanged by that naming: the letters did not move.

`cpcp-base.ttl` is the **PubSubStandard_1 (JSON-RPC-LD-PS1) foundation vocabulary**:
`CID`, `Profile`, `Operation` (+ `PULL` / `PUSH` directions), the three ledgers
(`CanonicalLedger`, `SyncIntentLedger`, `PrivateLocalLedger`), records
(`CanonicalRecord` → `Note` / `Insight` / `Receipt`, plus `SyncIntent`,
`PrivateLocalArtifact`), and `Pod`.

- **Ontology IRI:** `https://w3id.org/cpcp/ontology/base` — stable, unversioned
- **Version IRI:** `https://w3id.org/cpcp/ontology/base/0.1.2`
- **Term namespaces:** `https://w3id.org/cpcp/ns#` (`cpcp:`),
  `https://w3id.org/cpcp/osi8/a2a#` (`a2a:`),
  `https://w3id.org/cpcp/osi8/webmcpld#` (`webmcpld:`)
- **Imports:** `json-rpc-ld` core (`.../json-rpc-ld/ontology/core/1.0.0`)

## The grant, and what comes back

`cpcp:Grant` with `cpcp:Context` (read) and `cpcp:Effect` (write) disjoint
beneath it, plus `cpcp:Result` and its `ok` / `reason` / `because`.

These are the root README's central sentence, and every binding in this tree
had been typing nodes with them for as long as the bindings have existed —
against a vocabulary that did not define them. Adding a2a is what surfaced it:
a `DataPart`'s payload cannot be typed without a term for what a grant is.

`operationId` is **not** here. It is `jrl:operationId`, owned by `json-rpc-ld`.
Base owns the shapes; do not restate them.

## Versions

The ontology IRI **identifies the ontology**; the versionIRI **names one cut
of it**. Through 1.0.0 they were the same string, and that had two costs: every
term's `rdfs:isDefinedBy` churned on each release, and a consumer dereferencing
an older cut landed on a graph that no longer existed. Terms are now defined by
the stable IRI. Only `owl:versionIRI` and `owl:versionInfo` carry the number.

| Version | |
|---|---|
| `0.1.2` | current — a2a terms, and the grant/result terms adding them surfaced |
| `0.1.1` | the split, plus the webmcpld terms and `cpcp:Pull` / `cpcp:Push` |
| `1.0.0` | the unsplit cut, where the ontology IRI *was* the version |

`owl:priorVersion` names the one immediately behind. The chain is here.

0.1.1 sorts below 1.0.0, and the ordering is recorded in `owl:priorVersion`
rather than smoothed over. The renumbering aligns the ontology with the
package's own tag, and it costs nothing today because no W3ID redirect is
published ([identity](../spec/identity.md)) — an IRI here is a durable name a
reader can compare, not a promise of a fetch. That stops being true the moment
one resolves.

The import of `json-rpc-ld` core stays pinned to that base's versionIRI. A
dependency is pinned, not followed.

## Direction as a type

`cpcp:PULL` and `cpcp:PUSH` are individuals naming the direction **of an
operation**. The wire types a **node** instead — `a2a/` writes
`type: ["Effect", "cpcp:Push"]`, `webmcpld/` writes
`@type: ["webmcpld:Tool", "cpcp:Pull"]` — and that spelling had no term.
`cpcp:Pull` and `cpcp:Push` are now classes for it: the same distinction in
the other position, disjoint, each pointing at its individual by `seeAlso`.

They are deliberately **not** a restriction on `cpcp:hasDirection`. That
property's domain is `cpcp:Operation`, so an a2a Context typed `cpcp:Pull`
would be inferred an Operation — a fact nobody asserted.

## webmcpld terms

The [webmcpld](../webmcpld/README.md) binding — WebMCP as a compatible
superset — carries twelve terms in its own namespace:

- **Term namespace:** `https://w3id.org/cpcp/osi8/webmcpld#` (`webmcpld:`)

| Term | |
|---|---|
| `webmcpld:Tool` ⊑ `cpcp:Operation` | a WebMCP tool with a capability IRI, a direction and a shape — an operation whose seam is a page |
| `webmcpld:CID` ⊑ `cpcp:CID` | one origin's contract, linked from the document and well-known |
| `declaresTool` ⊑ `cpcp:declaresOperation`, `cid` | the two directions of the same binding: what the document declares, what the page claims |
| `instance`, `inputShape`, `outputShape` | the origin described; the SHACL shapes for arguments and result, by reference |
| `toolName` | the page-local WebMCP name — not an identifier, which is the whole reason the `@id` exists |
| `exposedTo` | a secure origin the tool is reachable from; absent is same-origin, and reach is a scope |
| `autosubmit`, `because` | a claim that a write needs no human confirmation, and the reason it is allowed to stand |
| `declaresReason` | a refusal reason from the closed taxonomy this origin can answer with |

Shape terms are `rdfs:Resource` references, not shapes. SHACL lives in the
profile; a second copy here would drift at its own rate. No `sh:` prefix
enters this tree.

## a2a terms

The [a2a](../a2a/README.md) bindings — one agent addressing another, over
HTTPS or over NATS — carry 41 terms:

- **Term namespace:** `https://w3id.org/cpcp/osi8/a2a#` (`a2a:`)

| Term | |
|---|---|
| `Message`, `Part` → `DataPart` / `TextPart` | what is sent; the DataPart is the one carrying a grant |
| `Task`, `TaskStatus`, `TaskState` | what comes back, and how far it got |
| `completed` / `failed` / `rejected` | delivered and ok; delivered and refused; never delivered |
| `Artifact` | where the CPCP Result rides home |
| `AgentCard`, `Interface`, `Skill`, `Capabilities` | discovery |
| `Transport` + `HTTP` / `NATS` | the two roads |
| `data` (`DataPart` → `cpcp:Grant`) | the join between this binding and the grant it carries |

**The JSON-RPC frame is not modelled, and never will be.** Compacting
`jsonrpc` into an IRI would break every JSON-RPC 2.0 parser. These terms cover
the JSON-LD *inside* `params` and `result`; the frame is `json-rpc-ld`'s.

Two collisions are named in the term comments rather than left for a reader to
trip over: `a2a:role` is a conversational role and **not** a CPCP role (FRONT,
BACK, BackJob, GRAPH), and `a2a:pushNotifications` is a transport capability
with nothing to do with `cpcp:PUSH`. One word, two vocabularies, twice.

Import graph: `PS1-PX` profile repos → **CPCP base** → **JSON-RPC-LD core**,
once those repos are public. Each profile repo ships a self-contained
`ontology/ps1-pX.ttl` aggregate that vendors these
base terms (canonical IRIs) so it opens in any OWL editor
with no network. The **CID is the pivot**: it generates the OKF bundle (Human/AI), these
ontologies + SHACL (Data), and the language bindings.
