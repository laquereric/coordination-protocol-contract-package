# webmcpld — WebMCP, grounded

**A compatible superset of WebMCP.** Same registration call, same tool
descriptors, same declarative forms. webmcpld adds what a browser tool
does not carry today: a **durable identity** for the capability, a
**closed shape** for what it accepts and returns, a **direction**
(read or write), and a **result that is a grounded JSON-LD node**
rather than a paragraph of text.

WebMCP names a tool by a page-local string. Two shops both call it
`search`, and neither name means anything a day later or a tab over.
[`spec/identity.md`](../spec/identity.md) already names this as one of
the three ways systems identify the "same" capability — Hydra by
operation IRI, **WebMCP by tool name**, JSON-RPC by method. CPCP fixes a
canonical IRI and maps the three explicitly. webmcpld is that mapping,
performed in a tab.

CPCP remains the grant (PULL Context / PUSH Effect). A2A
([`../a2a/`](../a2a/README.md)) is how one agent addresses another;
webmcpld is how an agent addresses a **page**. Third road, same grant.

webmcpld is not authentication and not authorization — a page's tools
run under the session the browser already has, and none of the machinery
below decides who may call. It is a semantic and effect guardrail, as
the root [README](../README.md) says of CPCP generally.

---

## 1. The superset law

Three rules. Everything in this document is a consequence of them.

**1. Erasure.** Delete every webmcpld addition from a page and what
remains is a conforming WebMCP page that still registers its tools and
still executes them. Nothing webmcpld adds is load-bearing for an agent
that does not know it exists.

**2. Ignorable slots.** Every addition sits in a slot where the format
it borrows *already requires unknown members to be ignored*: unknown
JSON Schema keywords, an extra item in a `content` array, an extra
attribute on an element, an extra `<link>`, an extra well-known
document. No existing member changes meaning.

**3. Satisfiable inside WebMCP.** Every obligation webmcpld imposes is
met with output WebMCP already permits. An obligation that required
WebMCP-illegal output would not be a superset; it would be a fork.

Erasure runs both ways, and the second direction is the one that
constrains the design hardest: a **plain WebMCP agent must be able to
call a webmcpld tool and get a useful answer**. That is why nothing
below is ever a new *required* input, and why the grounded result is
never the first thing in the array. See §5.

| WebMCP surface | webmcpld adds | a WebMCP-only agent sees |
|---|---|---|
| `name`, `description` | a capability IRI beside them | the same two strings |
| `inputSchema` | an `x-webmcpld` keyword | a schema it validates against unchanged |
| `execute` result | one more `text` content item | a second, legible text block |
| the page | a linked CID | a `<link rel>` it does not know |
| `<form toolname>` | a `toolid` attribute | an attribute it ignores |
| an error | a resolved result, not a rejection | a result flagged `isError` |

---

## 2. The baseline being extended

The WebMCP surface this binding targets, as of the current
[explainer](https://github.com/webmachinelearning/webmcp):

| Surface | Shape |
|---|---|
| register | `modelContext.registerTool(tool, { signal, exposedTo })` |
| discover | `modelContext.getTools({ fromOrigins })`, `toolchange` event |
| invoke | `modelContext.executeTool(tool, args, { signal })` |
| tool | `{ name, description, inputSchema, execute }` |
| result | `{ content: [{ type: "text", text }] }` |
| declarative | `<form toolname tooldescription toolautosubmit>`, `toolparamdescription` on controls |
| declarative result | `SubmitEvent#respondWith()`, or the first `<script type="application/ld+json">` on the target page |
| exposure | same-origin plus the UA's own agent by default; `exposedTo` widens it |

**The object is whichever one the UA exposes.** This document writes
`modelContext`; bind it to `document.modelContext` or
`navigator.modelContext`, whichever is present. The spelling has moved
and may move again (note [1]). webmcpld never names the global in a
document it ships — that is what feature detection is for, and a binding
that hard-codes a churning name breaks on a rename that changed nothing.

---

## 3. Four carriers

The engineering constraint that decides all four: **a tool descriptor is
converted to a WebIDL dictionary, and unknown members are dropped**
(note [2]). Identity written at the top level of the descriptor does not
survive the trip to the agent. So webmcpld carries linked data only
where the JSON is relayed verbatim.

| # | Carrier | Survives because | Erases to |
|---|---|---|---|
| 1 | `x-webmcpld` inside `inputSchema` | JSON Schema requires unknown keywords to be ignored, and the schema object is relayed whole | a schema with one fewer keyword |
| 2 | the CID, linked and well-known | a `<link rel>` and a URL nobody fetches | nothing |
| 3 | one `application/ld+json` text item in `content`, never first | it is a legal text item | one fewer text block |
| 4 | `toolid` on a form; the target page's first `<script type="application/ld+json">` | unknown attributes are ignored, and WebMCP **already** reads that script as the cross-document response | a form, and a response |

Carrier 4 is not an extension at all. WebMCP says the first
`application/ld+json` script on the target page *is* the tool's
response, and says nothing about what that document must contain.
webmcpld says: a CPCP envelope ([`spec/envelope.md`](../spec/envelope.md)).
It fills a hole rather than cutting one.

### Carrier 1 — the tool node

```js
modelContext.registerTool({
  name: "add-to-cart",
  description: "Add a product to the shopping cart",
  inputSchema: {
    type: "object",
    properties: {
      sku:      { type: "string", description: "Product SKU" },
      quantity: { type: "integer", minimum: 1, default: 1 },
      operationId: {
        type: "string",
        description: "Caller's name for this write; a retry carrying the same value is the same write"
      }
    },
    required: ["sku"],

    "x-webmcpld": {
      "@context": "https://w3id.org/cpcp/osi8/webmcpld/context.jsonld",
      "@id":   "https://w3id.org/cpcp/osi8/shop#cart.add",
      "@type": ["webmcpld:Tool", "cpcp:Push"],
      "cid":   "https://shop.example/.well-known/webmcpld/cid.json",
      "inputShape":  "https://shop.example/shapes/cart.ttl#CartAddShape",
      "outputShape": "https://shop.example/shapes/cart.ttl#CartAddResultShape"
    }
  },
  async execute({ sku, quantity = 1, operationId }) { /* … */ }
});
```

`x-webmcpld` members:

| Member | When | Meaning |
|---|---|---|
| `@id` | always | the capability IRI — absolute, `https://w3id.org/cpcp/osi8/<seam>#<Method>` ([identity](../spec/identity.md)) |
| `@type` | always | `webmcpld:Tool` plus **exactly one** of `cpcp:Pull`, `cpcp:Push` |
| `cid` | always | absolute URL of the CID that declares this `@id` |
| `inputShape` | when shapes exist | SHACL node shape for the arguments |
| `outputShape` | when shapes exist | SHACL node shape for `result` |
| `@context` | optional | a context IRI; the members above compact without it |

The IRIs are **intent until they resolve**. W3ID redirects are
unpublished ([identity](../spec/identity.md)) — an `@id` is a durable
name a reader can compare, not a promise of a fetch.

---

## 4. Two faces in a tab

A read costs nothing and promises nothing. A write carries the actor's
word for what it is doing.

| `@type` | is | carries |
|---|---|---|
| `cpcp:Pull` | read access — the agent reads grounded Context out of the page | no `operationId` |
| `cpcp:Push` | write access — the agent writes a typed Effect | an `operationId`, minted by the caller or by the page |

A tool typed `cpcp:Pull` that mutates is a false claim. Nothing here
detects it; the claim is the point, and a false one is still one
somebody can check.

### `operationId` is declared, never required

At the HTTP seam, PUSH without an `operationId` is refused
(`operation_id_required`, [refusals](../spec/refusals.md)) — the caller
is the only party who can name the intent, so there is nobody else to
ask.

**In a tab there is somebody else.** The page is a party to the call,
not just its target, and it can mint on the caller's behalf. So a `Push`
tool:

* **declares** `operationId` as a string property in `inputSchema`;
* **does not** list it in `required`;
* **mints** one when the caller omits it, and **MUST** return the value
  it used in the grounded result (§5).

Requiring it would break erasure in the direction that matters most: a
plain WebMCP agent, which knows nothing of `operationId`, would fail
every write on the page. Declaring it optional means an LD-aware agent
gets real retry identity, a plain agent gets a working call, and both
get an answer that says which id the write landed under.

`operation_id_required` therefore does not arise in this binding. That
is a deliberate divergence from the seam, and it is the only one.

---

## 5. Results, and refusals that do not raise

Every webmcpld result is a CPCP envelope. Every failure is data.

The grounded node rides as a `text` content item whose text is an
`application/ld+json` document. **It is never the first item.** A plain
agent that reads `content[0].text` and stops must still get the sentence
written for it.

```js
return {
  content: [
    { type: "text", text: "Added 2 × SKU-118 to your cart. Subtotal $47.98." },
    { type: "text", text: JSON.stringify({
        "@context": { "@vocab": "https://w3id.org/cpcp/ns#",
                      "id": "@id", "type": "@type",
                      "operationId": "https://w3id.org/json-rpc-ld/ns#operationId" },
        "type": "cpcp:Result",
        "ok": true,
        "operationId": "cart-add-a1b2c3d4e5f60718",
        "result": { "type": "CartLine", "sku": "SKU-118", "quantity": 2 }
      }) }
  ]
};
```

A refusal **resolves**. It does not reject.

```js
return {
  isError: true,
  content: [
    { type: "text", text: "That SKU is not stocked in your region." },
    { type: "text", text: JSON.stringify({
        "@context": { "@vocab": "https://w3id.org/cpcp/ns#" },
        "type": "cpcp:Result",
        "ok": false,
        "error": { "reason": "grounding_refused",
                   "because": "sku SKU-118 fails CartAddShape: region not served" }
      }) }
  ]
};
```

Reject the promise only when there is no answer at all — the signal
aborted, the page went away. A dropped page is infrastructure, not a
CPCP reason.

Reasons come from [`spec/refusals.md`](../spec/refusals.md):
`unknown_operation`, `missing_params`, `grounding_refused`,
`authorization_denied` all carry over unchanged. Three have no HTTP
analogue and are **proposed additions scoped to this binding** — they
are named here, not yet in the taxonomy:

| reason | meaning |
|---|---|
| `user_declined` | the human in the tab refused the confirmation the page asked for |
| `origin_not_exposed` | the calling origin is not in this tool's `exposedTo` |
| `page_state_changed` | the tool was unregistered, or the document navigated, between discovery and execution |

`page_state_changed` is the one WebMCP's own `toolchange` event makes
inevitable: tools appear and vanish with page state, and an agent
holding a handle from a second ago is holding a claim about a page that
has moved on.

---

## 6. Exposure is a scope, and it is measured

WebMCP's origin model is a CPCP scope in different words
([scopes](../spec/scopes.md), [repo format](../spec/repo-format.md) rule 4).

| CPCP scope | webmcpld reach | evidence |
|---|---|---|
| `pod_internal_services` | same-origin documents and the UA's built-in agent | the **absence** of `exposedTo` |
| `services` | the origins listed in `exposedTo`, and any granted `allow="tools"` | the `exposedTo` array as registered; the Permissions-Policy header **as served** |

Rule 4 applies with full force: exposure is read off what is served, not
off what the source intended. A header a deployment does not actually
send is not evidence, and `exposedTo` in a code path that never runs is
not a reach.

One tool reachable both ways is one tool in two scopes — rule 1, not two
tools.

---

## 7. The CID

The page's contract, served as one document, linked from the head and
resolvable at a well-known path:

```html
<link rel="webmcpld-cid" href="/.well-known/webmcpld/cid.json">
```

```json
{
  "@context": "https://w3id.org/cpcp/osi8/webmcpld/context.jsonld",
  "@id": "https://shop.example/.well-known/webmcpld/cid.json",
  "type": "webmcpld:CID",
  "version": 1,
  "instance": "https://shop.example/",
  "shapes": "https://shop.example/shapes/cart.ttl",
  "tools": [
    { "name": "search-products",
      "@id": "https://w3id.org/cpcp/osi8/shop#product.search",
      "@type": ["webmcpld:Tool", "cpcp:Pull"],
      "inputShape": "…#ProductSearchShape",
      "outputShape": "…#ProductListShape" },

    { "name": "add-to-cart",
      "@id": "https://w3id.org/cpcp/osi8/shop#cart.add",
      "@type": ["webmcpld:Tool", "cpcp:Push"],
      "inputShape": "…#CartAddShape",
      "outputShape": "…#CartAddResultShape",
      "autosubmit": false }
  ],
  "reasons": ["grounding_refused", "missing_params", "user_declined",
              "origin_not_exposed", "page_state_changed"]
}
```

The CID is the specification. This README explains; it does not specify
— and prose that restates a CID is a second source of truth that will
drift from the first ([repo format](../spec/repo-format.md), Optional).

Every `@id` a page registers in `x-webmcpld` MUST appear in the CID it
names. A tool that grounds itself against a document that does not know
it is grounding itself against nothing.

---

## 8. Declarative binding

WebMCP's form path needs one attribute and one rule.

```html
<form toolname="search-cars"
      tooldescription="Perform a car make/model search"
      toolid="https://w3id.org/cpcp/osi8/cars#vehicle.search"
      action="/search">
  <input type="text" name="make"
         toolparamdescription="The vehicle's make (i.e., BMW, Ford)" required>
  <input type="text" name="model"
         toolparamdescription="The vehicle's model (i.e., 330i, F-150)" required>
  <button type="submit">Search</button>
</form>
```

`toolid` is the capability IRI. Direction, shapes and reasons come from
the CID entry it resolves to — a form carries one attribute, not a
manifest.

**The response document is a CPCP envelope.** WebMCP already reads the
first `<script type="application/ld+json">` on the target page as the
tool's response; on `/search`, that script is:

```html
<script type="application/ld+json">
{ "@context": { "@vocab": "https://w3id.org/cpcp/ns#", "id": "@id", "type": "@type" },
  "type": "cpcp:Result", "ok": true,
  "result": { "@graph": [ { "type": "Vehicle", "make": "BMW", "model": "330i" } ] } }
</script>
```

Collections return `result: {"@graph": [...]}`, as at the seam.

**`toolautosubmit` on a `cpcp:Push` form is a claim that a write needs
no human confirmation.** webmcpld does not forbid it and does not
silently allow it: the tool's CID entry MUST carry `"autosubmit": true`
and a `because`. Anything other than the safe default needs a reason
somebody can read — the same rule the format applies to an unbuilt
dependency.

---

## 9. Conformance is per tool

A page may serve conforming and plain tools side by side; the plain ones
are not violations, they are ungrounded. What a checker decides:

| # | Check |
|---|---|
| 1 | every webmcpld tool's `inputSchema` carries `x-webmcpld` with an absolute `@id` |
| 2 | that `@id` appears in the CID the tool names, and the CID resolves |
| 3 | `@type` carries exactly one of `cpcp:Pull`, `cpcp:Push` |
| 4 | every `cpcp:Push` declares `operationId` in `properties` and **omits** it from `required` |
| 5 | every result carries an `application/ld+json` text item, and it is **not** `content[0]` |
| 6 | every `cpcp:Push` result carries the `operationId` the write landed under |
| 7 | a refusal resolves with `isError` and `ok: false`; it never rejects |
| 8 | `toolautosubmit` on a Push tool has `autosubmit: true` **and** a `because` in the CID |
| 9 | **erasure**: strip every addition above and the page still registers its tools and still executes them |

Check 9 is the one that keeps this a superset. The other eight can all
pass on a page that has quietly stopped being WebMCP.

Shapes are not checked here. A consumer validates against the profile's
SHACL; this document states the envelope those shapes plug into
([identity](../spec/identity.md)).

---

## 10. Namespaces

| Root | Owns |
|---|---|
| `https://w3id.org/cpcp/osi8/webmcpld#` | binding terms: `Tool`, `CID`, the carrier keys |
| `https://w3id.org/cpcp/osi8/<seam>#<Method>` | capability identity ([identity](../spec/identity.md)) |
| `https://w3id.org/cpcp/ns#` | payload terms (`cpcp:Pull`, `cpcp:Push`, `cpcp:Result`) |
| WebMCP's own names — `name`, `inputSchema`, `content`, `toolname` | untouched, and not IRIs |

**`webmcpld.online` is deployment, not identity.** It serves the
reference page, the live CID, and the conformance checker. No term is
minted under it and no `@id` points at it. Domains change hands;
identity must not. This is the same separation the root README draws
between the three namespace roots and the repos that happen to host
things.

Nothing here reaches the reference instance yet. Stated as
[kinds](../spec/kinds.md) rule 10 would have it: `liveness: advisory`,
because nothing is deployed at `webmcpld.online` — recorded so an
outage cannot read as a passing check, and so a reader is not told a
seam exists where none does.

---

## 11. What webmcpld is not

| | |
|---|---|
| a replacement for WebMCP | it is WebMCP, plus four ignorable slots |
| a replacement for MCP | server-side MCP still owns backend operations; a product uses both |
| authentication or authorization | the page runs under the session the browser already has; §1 of the root README applies unchanged |
| a crawler surface | grounded results are for the agent that called the tool, not for indexing |
| a second schema.org | site-level descriptive markup describes a page; a CID declares an interface |
| a way to run tools with no UI present | WebMCP puts that out of scope, and a superset cannot add what the base excludes |

---

## Notes

**[1] The surface has been moving.** `provideContext()` existed in
earlier drafts and was removed in March 2026; the object has been
spelled both `navigator.modelContext` and `document.modelContext`.
Implementations landed through 2026 — Chrome behind
`chrome://flags/#enable-webmcp-testing`, later an origin trial; Edge
shipping native support. This is why §2 binds by feature detection and
why every carrier in §3 lives in a slot the *format* protects rather
than one a *spelling* does. A binding that survives a rename is the only
kind worth writing against a spec at this stage.

**[2] Why identity is not on the descriptor.** Members of a WebIDL
dictionary that the browser does not know are dropped in conversion, so
an `@id` written beside `name` never reaches the agent. `inputSchema` is
different: it is relayed as JSON, and JSON Schema requires unknown
keywords to be ignored rather than rejected. The rule generalises —
**carry linked data where the JSON survives**, never where a dictionary
sits between the page and the reader.
