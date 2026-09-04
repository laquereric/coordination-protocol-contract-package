# Background: Hydra, WebMCP, JSON-RPC-LD

Positioning, after the cross-reference analysis (Manus): the three
sources are composable, not competing. None of them, by itself, defines
the security, authorization, consent, or trust model for safe agent
execution — the integration layer must.

* **Hydra** describes hypermedia-driven HTTP APIs: resources, typed
  links, collections, operations, API documentation. Use it when the
  problem is discoverability and resource navigation. It is a
  description vocabulary, not an execution engine, and not a W3C
  standard.
* **WebMCP** exposes a loaded page's JavaScript capabilities as agent
  tools through a browser-side bridge. Use it when the capability is
  inherently page-local or user-mediated. The early library is not the
  W3C WebMCP standard; production designs must distinguish them.
* **JSON-RPC-LD** (profiled here as CPCP) gives RPC payloads explicit
  Linked Data semantics plus SHACL validation. Use it when method calls
  need portable meaning and validation.

Composed: Hydra describes the resource graph, WebMCP presents selected
capabilities to an agent in the browser, JSON-RPC-LD carries and
validates the semantic method calls — with canonical operation identity
(`spec/identity.md`) spanning all three so no single layer's naming
becomes the only source of meaning.
