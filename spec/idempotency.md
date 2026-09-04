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
* A store that cannot be read yields "not cached": the effect proceeds.
  At worst a retry duplicates, which the digest makes visible. Refusing
  the write instead would let a broken cache take the seam down. A
  store that cannot be read reports `idempotency_not_durable` /
  `idempotency_store_unavailable`; neither fails the call.
* PULL methods carry no idempotency key and need none.
