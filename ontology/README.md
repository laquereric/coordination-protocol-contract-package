# CPCP base ontology (Data perspective)

CPCP is **coordination-protocol-contract-package**. The vocabulary IRI and every
term below are unchanged by that naming: the letters did not move.

`cpcp-base.ttl` is the **PubSubStandard_1 (JSON-RPC-LD-PS1) foundation vocabulary**:
`CID`, `Profile`, `Operation` (+ `PULL` / `PUSH` directions), the three ledgers
(`CanonicalLedger`, `SyncIntentLedger`, `PrivateLocalLedger`), records
(`CanonicalRecord` → `Note` / `Insight` / `Receipt`, plus `SyncIntent`,
`PrivateLocalArtifact`), and `Pod`.

- **Ontology IRI:** `https://w3id.org/cpcp/ontology/base/1.0.0`
- **Term namespace:** `https://w3id.org/cpcp/ns#` (`cpcp:`)
- **Imports:** `json-rpc-ld` core (`.../json-rpc-ld/ontology/core/1.0.0`)

Import graph: `PS1-PX` profile repos → **CPCP base** → **JSON-RPC-LD core**,
once those repos are public. Each profile repo ships a self-contained
`ontology/ps1-pX.ttl` aggregate that vendors these
base terms (canonical IRIs) so it opens in any OWL editor
with no network. The **CID is the pivot**: it generates the OKF bundle (Human/AI), these
ontologies + SHACL (Data), and the language bindings.
