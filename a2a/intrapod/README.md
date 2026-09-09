# A2A / intrapod

**JSON-RPC 2.0 envelope. JSON-LD payloads. NATS transport.**

This is the pod-internal A2A binding of CPCP. The **frame and the
payloads are the same documents** as [`../internet/`](../internet/README.md).
Only the road changes. OSI L8 §10: HTTP and NATS MUST preserve identical
Level 8 semantics. A Context or Effect that is valid on the internet
binding is valid here, and the reverse.

What this file adds is the design that was paid for by putting NATS in
magentic-stack: *what* the broker is, *what it is not*, and the rules
that keep in-pod HTTP from becoming a silent second path.

---

## 1. Same envelope, different road

| | Internet ([../internet](../internet/README.md)) | Intrapod (this file) |
|---|---|---|
| Frame | JSON-RPC 2.0 | JSON-RPC 2.0 |
| Payload | JSON-LD Message / Task / Context / Effect | identical |
| Methods | `agent/card`, `message/send`, `tasks/get` | identical |
| Transport | HTTPS, `POST` of the frame | NATS request-reply on `a2a.<agent>.rpc` |
| Discovery | `GET /.well-known/agent-card.json` | `agent/card` on that subject |
| Auth on the wire | `Authorization: Bearer` HTTP header | the **same** Bearer in a **NATS header** |
| Preferred transport on the Card | `HTTP` | `NATS` |
| Process bind | published host port | HTTP, if the process still listens, binds **loopback** |

There is no second schema. An implementation that emits
`{ "cpcp": { "jsonrpc": "2.0", "method": "note.list" } }` on NATS and
JSON-LD on HTTP has already broken transport equivalence.

---

## 2. Decisions discovered implementing NATS in magentic-stack

These are not optional colour. Each one was a real fork in a running
pod (mind-pod, 2026-09-08). The intrapod binding records them so the
next implementation does not re-litigate them as packaging taste.

### 2.1 NATS is a container. A2A is not.

`nats-server` is a third-party binary (Go), digest-pinned, unpublished,
JetStream store on a named volume. It is the same *class* as oxigraph:
unforked, we ship no source into it, language-rule exemption by
**condition** (third-party, digest-pinned, no build, no bind-mount of
our tree) — not by the name `nats`.

A2A has no such binary. There is no `a2a-server` image. Agent2Agent is
an envelope. Adding a Rails `ROLE=a2a` would be another HTTP process
on the docker network, which is the surface this binding exists to
close. **Do not spend a container slot on A2A.**

In magentic-stack the twelfth running container is `nats`. The slot
that had been reserved for `ROLE=project-graph` was spent on the
broker; projection stays embedded in BACK. LOG (a decided unbuilt
role) is unrelated.

### 2.2 NATS is not BUS

`ROLE=bus` is a Rails CPCP seam plus an async sqlite projection of
metadata derived from BACK's journal. It is not an event store (Rails
Event Store was declined because it would have been a *second* log
beside the admission journal).

NATS is Level 7 transport. BUS may later *publish* as a NATS client.
BUS must never *be* the broker. Folding `nats-server` into the BUS
container would mix a Go process with a Rails projector, invert the
rule that a domain call completes with BUS the projection down, and
put JetStream durability in the same crash domain as `bus.sqlite3`.

JetStream is a **fourth kind of state** (transport durability), beside
application state (BACK), metadata (BUS), and inference state (MIND).
Sequence numbers MUST NOT replace `operationId`. Broker dedup MUST NOT
replace the application-level intent id.

### 2.3 HTTP is not a fallback

`MM_NATS_URL` empty → the process is allowed to speak the internet
binding (tests, host curl against a published BACK).

`MM_NATS_URL` set → NATS only. A silent broker, a missing client
library, or a timeout is `nats_unreachable`. The client MUST NOT open
HTTP to the peer. Dual-bind as a *landing sequence* (serve both while
clients move) is not a *runtime rule* ("NATS failed, so HTTP"). The
second reading re-opens the docker-network HTTP surface the bind
exists to close.

Host-published HTTP (operator UI, extract FRONT, extract BACK for
curl) is a **different surface**, not a backup path for in-pod calls.
SPARQL and the LLM data plane stay HTTP because they are not CPCP and
not A2A.

### 2.4 Loopback is the HTTP bind, not omitted `expose`

Omitting Compose `expose: 3000` does not hide a server that listens on
`0.0.0.0:3000`. Sibling containers can still dial the container IP.
In-pod CPCP/A2A roles therefore bind HTTP to `127.0.0.1`. Only
host-published operator surfaces opt into `HTTP_BIND=0.0.0.0`. The
entrypoint default is loopback; all-interfaces is explicit.

### 2.5 Authorization stays a header

Vault's contract: Bearer is the `Authorization` header, never a
JSON-RPC param, never a field on the JSON-LD Effect. On NATS the
header is a NATS application header on the request-reply message. The
payload remains the JSON-RPC frame + JSON-LD parts, unchanged.

### 2.6 Subjects are the addresses

```
a2a.<agent>.rpc     A2A JSON-RPC request-reply (this binding)
cpcp.<role>.rpc     CPCP JSON-RPC-LD request-reply (non-agent callers)
```

`<agent>` is the ROLE the process is serving (`back` in v1). There is
no well-known HTTP path in-pod. Discovery is `agent/card` on
`a2a.<agent>.rpc`. The Agent Card's `additionalInterfaces` name the
NATS URL and the subject, never `http://back:3000`.

v1 A2A listener is BACK. MIND is a client. Vault, persist, bus keep
`cpcp.<role>.rpc` — those are grants, not agent conversations.

### 2.7 Never-raise still holds

NATS timeouts and missing libraries degrade to an envelope
(`nats_unreachable`), not an exception across the boundary. Restoration
belongs on the CPCP refusal inside the artifact, not on the NATS
timeout.

---

## 3. Worked request (intrapod)

Identical JSON-LD Part as internet. The road is NATS.

```
NATS request
  subject: a2a.back.rpc
  header:  Authorization: Bearer <token>   # if the seam requires it
  body:
```

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
        "type": "@type",
        "operationId": "https://w3id.org/json-rpc-ld/ns#operationId"
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
              "type": "@type",
              "operationId": "https://w3id.org/json-rpc-ld/ns#operationId"
            },
            "id": "urn:uuid:22222222-2222-2222-2222-222222222222",
            "type": ["Effect", "cpcp:Push"],
            "method": "note.create",
            "operationId": "mind-reading-a1b2c3d4e5f60718",
            "params": { "title": "…", "body": "…" }
          }
        }
      ]
    }
  }
}
```

Reply: JSON-LD Task, CPCP Result or Refusal in
`artifacts[].parts[].data` as `application/ld+json`. See internet §5.

A local dispatcher that still speaks `{ jsonrpc, method, params,
operationId }` is an **implementation adapter** behind the seam. The
adapter MUST NOT be visible on the NATS body.

---

## 4. Agent Card (intrapod)

No `/.well-known/` in-pod. `agent/card` on `a2a.<agent>.rpc` returns:

```json
{
  "@context": {
    "@vocab": "https://w3id.org/cpcp/osi8/a2a#",
    "id": "@id",
    "type": "@type"
  },
  "id": "urn:mm:agent:back",
  "type": "AgentCard",
  "name": "mind-pod-back",
  "preferredTransport": "NATS",
  "additionalInterfaces": [
    {
      "url": "nats://nats:4222",
      "transport": "NATS",
      "protocol": "jsonrpc",
      "subject": "a2a.back.rpc"
    }
  ],
  "capabilities": { "streaming": false, "pushNotifications": false },
  "defaultInputModes": ["application/ld+json"],
  "defaultOutputModes": ["application/ld+json"],
  "skills": [
    {
      "id": "cpcp",
      "name": "CPCP",
      "description": "JSON-LD Context (PULL) and Effect (PUSH) as A2A DataPart"
    }
  ]
}
```

`defaultInputModes` / `defaultOutputModes` are `application/ld+json`.
A Card that advertises `application/json` for the grant Part is
describing the retired nest.

---

## 5. Conformance (intrapod-specific)

An intrapod implementation MUST:

1. Accept and emit the internet JSON-LD Part shape; refuse
   `a2a_json_not_jsonld` for a nested JSON-RPC under `data.cpcp` or a
   `method` object with no `@context`.
2. Subscribe `a2a.<agent>.rpc`; not publish an in-pod HTTP A2A path.
3. Treat `MM_NATS_URL` set as exclusive; never fall back to HTTP.
4. Bind leftover HTTP to loopback unless the process is the
   host-published operator surface.
5. Carry Bearer in NATS headers when the seam requires auth.
6. Keep `operationId` on the Effect node; never substitute a JetStream
   sequence or NATS message id.
7. Keep the admission journal in the domain writer; the Task map is
   not that journal.

Internet-only requirements (TLS, well-known Card, HTTP dual-signal)
do not apply inside the pod.
