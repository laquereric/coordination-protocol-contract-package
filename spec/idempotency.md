# Idempotency

A PUSH names its intent before performing it; asking twice with the
same name must not perform it twice.

Sources: PROVENANCE.json entry E3 (idempotency store, dispatcher rules).

## Rules

* PUSH methods require `operationId` (top-level or in params). Missing:
  `operation_id_required`. PUSH without an id is not admitted.
* A repeated `operationId` returns the FIRST result (replay), not a
  second execution. The method handler does not run again.
* The receipt MUST outlive the process that issued it. An in-memory
  store empties on container recreate and the same id writes again —
  content addressed by digest stays uncorrupted, but the id reads like
  a guarantee it is not making. Production stores are durable (sqlite
  or equivalent); memory stores are explicitly not durable and say so.
* A receipt lives as long as the effect it records. A PUSH's receipt is
  kept for as long as the records that PUSH wrote can be read, and is
  removed only with them, in the same transaction. A receipt retired
  while its effect remains lets the same `operationId` execute again
  over a state that already holds it, which is the double write the key
  exists to prevent. A seam whose records are append-only therefore
  keeps its receipts for ever; that is not a leak but the rule. Store
  receipts so that this is cheap: appended one per PUSH, never a file
  rewritten whole. A channel's receipt is its log entry (below), the
  same rule.
* A store that cannot be read yields "not cached": the effect proceeds.
  At worst a retry duplicates, which the digest makes visible. Refusing
  the write instead would let a broken cache take the seam down. A
  store that cannot be read reports `idempotency_not_durable` /
  `idempotency_store_unavailable`; neither fails the call.
* PULL methods carry no idempotency key and need none.
* A channel's inbound frame (proposed, [`spec/channels.md`](channels.md))
  is named by its position: its `operationId` is `channel:<log IRI>:<seq>`,
  derived and never sent. The same payload at a held `seq` is a replay; a
  different one is refused (`seq_taken`). The log entry is the receipt,
  so it lives as long as the log. On a log with several writers a frame
  is named by its lane's position, `channel:<log IRI>:<lane>:<n>`.
