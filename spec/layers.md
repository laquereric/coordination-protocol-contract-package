# Layer authority

Four layers, each authoritative for its own matters and forbidden from
deciding the others'. An adapter may translate only what it names: a
refusal rendered as both 403 and envelope error must declare that
translation; a method IRI mapped to a wire method must not imply the
IRI itself is an endpoint.

Source: row-105 review, expressed in `seam_authority.json`.

| Layer | Authoritative for | Must not decide |
|---|---|---|
| **HTTP binding** | Routing to an origin, method semantics, status, headers, auth challenges, content negotiation, caching, conditionals, intermediaries, transport observability | Method meaning, result/error vocabulary, domain authorization, RDF/SHACL semantics |
| **JSON-RPC-LD / CPCP profile** | Envelope, versioning, dispatch, params structure, correlation, result/error shape, JSON-LD context and profile terms | Status meanings, cacheability, auth challenge syntax, resource lifecycle, RESTfulness |
| **REST resource binding** | URI/resource identity, uniform-interface use, safe/idempotent expectations, representations, links, conditionals, lifecycle where claimed | Procedure names, envelope conformance, vocabulary meaning, authorization beyond HTTP-visible signaling |
| **W3ID/RDF vocabulary** | Durable identity and meaning of shapes, properties, classes, operations; term versioning and governance | Dispatch, endpoint location, auth, status, cache policy, proof of conformance |

Every live seam declares its bindings (`registry/seams.json` in cpcp_registry).
CPCP's own seams speak `http` + `cpcp`; none claims `rest` (the vault
REST surface was retired) — resource-oriented bindings are declared
only where actually exposed.
