# CPCP base ontology (Data perspective)

`cpcp-base.ttl` is the **PubSubStandard_1 (JSON-RPC-LD-PS1) foundation vocabulary**:
`CID`, `Profile`, `Operation` (+ `PULL` / `PUSH` directions), the three ledgers
(`CanonicalLedger`, `SyncIntentLedger`, `PrivateLocalLedger`), records
(`CanonicalRecord` → `Note` / `Insight` / `Receipt`, plus `SyncIntent`,
`PrivateLocalArtifact`), and `Pod`.

- **Ontology IRI:** `https://w3id.org/laquereric/cpcp/ontology/base/1.0.0`
- **Term namespace:** `https://w3id.org/laquereric/cpcp/ns#` (`cpcp:`)
- **Imports:** `json-rpc-ld` core (`.../json-rpc-ld/ontology/core/1.0.0`)

Import graph: `PS1-P1`, `PS1-P2` → **CPCP base** → **JSON-RPC-LD core**. Each PS1-PX
profile repo ships a self-contained `ontology/ps1-pX.ttl` aggregate that vendors these
base terms (canonical IRIs) so it opens in [Protégé](https://protege.stanford.edu/)
with no network. The **CID is the pivot**: it generates the OKF bundle (Human/AI), these
ontologies + SHACL (Data), and the language bindings.
