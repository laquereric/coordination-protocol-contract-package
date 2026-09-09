# A2A / internet

**JSON-RPC 2.0 envelope. JSON-LD payloads. HTTP(+TLS) transport.**

This is the host- and internet-facing A2A binding of CPCP. It is the
official Agent2Agent JSON-RPC-over-HTTP shape, constrained so every
payload that crosses the agent boundary is a **grounded JSON-LD node**,
not a nested JSON-RPC document and not a bare JSON object.

The intrapod binding — same envelope, NATS instead of HTTP — is
[`../intrapod/`](../intrapod/README.md). Level 8 semantics MUST be
identical across the two (OSI L8 §10: transport equivalence). Only
discovery, addressing, and the HTTP dual-signal differ.

CPCP remains the grant (PULL Context / PUSH Effect). A2A is how one
agent addresses another. A2A is not a second admission log, not
authentication, and not authorization.

---

## 1. Two envelopes, one payload language

| Layer | Format | Owns |
|---|---|---|
| **Frame** | JSON-RPC 2.0 | `jsonrpc`, `id`, `method`, `params` / `result` / `error` |
| **Payload** | JSON-LD 1.1 | Message, Task, Part, Agent Card, and the CPCP Context or Effect inside a Part |

The frame is **not** JSON-LD. Compacting `jsonrpc` into an IRI would
break every JSON-RPC 2.0 parser. The payloads *inside* `params` and
`result` **are** JSON-LD: they carry `@context`, `@id`/`id`, and
`@type`/`type`.

**Forbidden on the wire (this binding):** stuffing a second JSON-RPC
object under `Part.data.cpcp` as `{ "jsonrpc": "2.0", "method": "note.list", ... }`.
That nest was an implementation accident. The CPCP grant lives as a
JSON-LD node of type `cpcp:Context` (PULL) or `cpcp:Effect` (PUSH).
The adapter that calls a JSON-RPC dispatcher is local to an
implementation; it is not the internet document.

---

## 2. JSON-RPC methods

PascalCase aliases from the A2A proto are accepted as the same method.

| JSON-RPC `method` | Alias | Result payload (JSON-LD) |
|---|---|---|
| `agent/card` | `GetAgentCard` | Agent Card |
| `message/send` | `SendMessage` | Task |
| `tasks/get` | `GetTask` | Task |

Unknown methods: JSON-RPC error `a2a_unknown_method`. Never raise.

`id` on the frame echoes on every response, including refusals. It is
correlation for this RPC, not `operationId` and not the Task id.

---

## 3. Contexts

Payloads MUST include `@context`. Implementations MAY compact with these
terms; they MUST expand to the IRIs.

```json
{
  "@context": {
    "@vocab": "https://w3id.org/cpcp/osi8/a2a#",
    "cpcp": "https://w3id.org/cpcp/ns#",
    "id": "@id",
    "type": "@type",
    "operationId": "https://w3id.org/json-rpc-ld/ns#operationId",
    "messageId": "https://w3id.org/cpcp/osi8/a2a#messageId",
    "mediaType": "https://w3id.org/cpcp/osi8/a2a#mediaType",
    "parts": "https://w3id.org/cpcp/osi8/a2a#parts",
    "role": "https://w3id.org/cpcp/osi8/a2a#role"
  }
}
```

SHACL for Context and Effect lives in the profile CID, not here
([identity.md](../../spec/identity.md)). This document names the
envelope those shapes plug into.

---

## 4. Message / Part / CPCP node

`params.message` is a JSON-LD node `type: Message`. Each Part that
carries a grant is a `DataPart` whose `data` **is** the CPCP node
(media type `application/ld+json`).

### PULL — Context

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "message/send",
  "params": {
    "message": {
      "@context": {
        "@vocab": "https://w3id.org/cpcp/osi8/a2a#",
        "cpcp": "https://w3id.org/cpcp/ns#",
        "id": "@id",
        "type": "@type"
      },
      "id": "urn:uuid:11111111-1111-1111-1111-111111111111",
      "type": "Message",
      "role": "user",
      "parts": [
        {
          "type": "DataPart",
          "mediaType": "application/ld+json",
          "data": {
            "@context": {
              "@vocab": "https://w3id.org/cpcp/ns#",
              "id": "@id",
              "type": "@type"
            },
            "id": "urn:uuid:22222222-2222-2222-2222-222222222222",
            "type": ["Context", "cpcp:Pull"],
            "method": "note.list",
            "params": {}
          }
        }
      ]
    }
  }
}
```

### PUSH — Effect

Same frame. The Part `data` node is:

```json
{
  "@context": {
    "@vocab": "https://w3id.org/cpcp/ns#",
    "id": "@id",
    "type": "@type",
    "operationId": "https://w3id.org/json-rpc-ld/ns#operationId"
  },
  "id": "urn:uuid:33333333-3333-3333-3333-333333333333",
  "type": ["Effect", "cpcp:Push"],
  "method": "note.create",
  "operationId": "mind-reading-a1b2c3d4e5f60718",
  "params": { "title": "…", "body": "…" }
}
```

PUSH without `operationId` is refused as CPCP `operation_id_required`
after A2A has accepted the Part — A2A does not invent the id.

### What a Part is not

| Shape | Verdict |
|---|---|
| `kind: "text"` / `type: TextPart` with no JSON-LD grant | `rejected` / `a2a_unsupported_part` |
| `data: { "cpcp": { "jsonrpc": "2.0", "method": "…" } }` | `rejected` / `a2a_json_not_jsonld` — the retired nest |
| `data` a JSON object with `method` and **no** `@context` | `rejected` / `a2a_json_not_jsonld` |
| Multiple grant Parts | first JSON-LD Context/Effect wins; the rest are ignored in v1 |

`method` on the JSON-LD node is the CPCP operation name
(`<domain>.<verb>`). Its durable meaning is the capability IRI in
[identity.md](../../spec/identity.md), not the A2A JSON-RPC method.

---

## 5. Task result

`message/send` returns a JSON-LD Task. The CPCP envelope (success or
refusal) comes back as an artifact Part, same media type, same vocab.

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "@context": {
      "@vocab": "https://w3id.org/cpcp/osi8/a2a#",
      "cpcp": "https://w3id.org/cpcp/ns#",
      "id": "@id",
      "type": "@type"
    },
    "id": "urn:uuid:44444444-4444-4444-4444-444444444444",
    "type": "Task",
    "contextId": "urn:uuid:11111111-1111-1111-1111-111111111111",
    "status": { "type": "TaskStatus", "state": "completed" },
    "artifacts": [
      {
        "id": "urn:uuid:44444444-4444-4444-4444-444444444444#artifact",
        "type": "Artifact",
        "parts": [
          {
            "type": "DataPart",
            "mediaType": "application/ld+json",
            "data": {
              "@context": {
                "@vocab": "https://w3id.org/cpcp/ns#",
                "id": "@id",
                "type": "@type"
              },
              "type": ["cpcp:Result"],
              "ok": true,
              "result": {}
            }
          }
        ]
      }
    ]
  }
}
```

| Task `status.state` | When |
|---|---|
| `completed` | CPCP envelope `ok: true` |
| `failed` | CPCP envelope `ok: false` (grounding, admission, handler) |
| `rejected` | no JSON-LD grant Part; A2A never called the dispatcher |

A CPCP refusal is still a **completed A2A delivery of a refused grant**,
except when A2A itself rejected the Part. Do not map `grounding_refused`
to HTTP 4xx here — see [http-mapping.md](../../spec/http-mapping.md).
Clients MUST unwrap the artifact and read the CPCP envelope (both
nested `error.reason` and flat `reason`; [envelope.md](../../spec/envelope.md)).

`tasks/get` returns the same Task node. Task identity is not
`operationId` and is not the JSON-RPC `id`. Implementations MAY keep
Tasks in memory; they MUST NOT treat the Task map as admission truth.

---

## 6. Agent Card (internet discovery)

Internet discovery uses the well-known HTTP resource:

```
GET /.well-known/agent-card.json
```

The document is JSON-LD. `preferredTransport` for this binding is
`HTTP`. `url` is the HTTPS origin of `POST /_cpcp/rpc` or the A2A HTTP
path the deployment publishes. TLS is required on the open internet.

Authentication is out of band (Bearer, as CPCP already does). The Card
advertises the scheme; it does not carry secrets.

---

## 7. HTTP dual-signal

POST of the JSON-RPC frame follows [http-mapping.md](../../spec/http-mapping.md).
Status describes the HTTP exchange. The JSON-RPC `error` / CPCP envelope
describes the grant. Clients MUST inspect both. Never infer an
application reason from status alone.

`GET /.well-known/agent-card.json` is not an RPC method result; it is
200 + the Card, or 404 if the deployment does not speak internet A2A.

---

## 8. Never-raise

Every A2A JSON-RPC response is an envelope. Failures are data. A dropped
connection is infrastructure, not a CPCP reason. Restoration, when
present, is the four-member `cpcp.restoration` object on the CPCP
refusal, not on the A2A Task ([refusals.md](../../spec/refusals.md)).
