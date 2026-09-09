# A2A bindings for CPCP

JSON-RPC 2.0 **frame**. JSON-LD **payloads**. Two roads:

| Binding | Transport | Discovery |
|---|---|---|
| [internet](internet/) | HTTPS | `GET /.well-known/agent-card.json` |
| [intrapod](intrapod/) | NATS `a2a.<agent>.rpc` | `agent/card` on that subject |

Level 8 semantics are identical. A nested JSON-RPC document under
`Part.data.cpcp` is not a payload on either road.
