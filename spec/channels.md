# Channels: a stream that is only a cache of a PULL

**Status: proposed.** Not extracted from production; see [Evidence](#evidence).

`spec/methods.md` rules out push notifications and subscriptions, and it is
right to: a write that arrives unasked, or a read nobody can ask for again,
cannot be accounted for afterwards. Some grants still need latency below
what polling can give. Two parties steering one real-time session need each
other's inputs within one tick (33 ms at 30 Hz), and polling at that rate
spends a request on every tick to learn, usually, that nothing changed.

A **channel** is the one stream CPCP admits. It is narrow by construction:
everything it carries could have been read with a PULL, and everything it
accepts is an entry a PUSH could have appended. A channel makes those cheaper
and faster. It never makes them different.

## What may be a channel

A seam MAY offer a channel over a **log**: an append-only, totally ordered
sequence of entries, each with a position `seq` (0, 1, 2, …) that never
changes once assigned. The log must also be readable by PULL from any
cursor, for example `session.inputs.since {cursor}`. A seam offers channels
over nothing else. In particular:

* **Outbound** frames (seam to caller) are entries of the log, in `seq`
  order. A caller that loses a channel MUST be able to fetch the same
  entries by PULL from its last `seq` and reach the same state. Nothing
  arrives on a channel that the PULL would not answer.
* **Inbound** frames (caller to seam) are proposed entries of the log. Each
  one is a PUSH in all but envelope (below). The seam still decides, and its
  decision is readable afterwards by PULL. A verdict is not a frame the
  caller has to have seen.
* A channel carries no other effect. No method is called over it, and
  nothing the log does not hold can be written through it.

So a channel is a cache of a PULL, and its inbound half is a batch of
PUSHes. Truth is the log, and a dropped channel degrades to polling without
losing any of it.

## Opening: one PUSH, one admission

A channel is opened by an ordinary PUSH on the seam, `<domain>.channel.open`.
It has an `operationId` and is admitted and journaled like any other effect:

```json
{"jsonrpc": "2.0", "id": 1, "method": "session.channel.open",
 "operationId": "op-…",
 "params": {"session": "s-…", "from": 1280, "frames": "sha256:8570…", "roads": ["webtransport", "websocket"]}}
```

The result names the road chosen, the ticket that admits the connection, and
when the ticket lapses:

```json
{"ok": true, "result": {"type": "ChannelTicket", "road": "webtransport",
  "url": "https://…/channel/s-…", "ticket": "…", "until": "2026-10-20T19:00:00Z",
  "frames": "sha256:8570…", "from": 1280}}
```

* **Authentication and authorization happen here, once.** The caller's
  credential is checked and the open is admitted for that log alone. A
  connection presenting the ticket is that admission. The seam does not ask
  again per frame, which is what makes the channel fast. A deployment that
  must revoke mid-stream does so by closing the channel; the caller then
  re-opens, and is admitted or refused anew.
* `frames` is the digest of the frame layout the caller speaks
  (`spec/frames.md`). A seam that speaks another layout refuses the open
  (`frame_digest_mismatch`). Typing is agreed here, so it costs nothing
  per frame.
* `from` is the first `seq` the caller wants outbound. Everything before it,
  the caller already has or fetches by PULL.
* The ticket is a bearer for one connection to one log. It is never a
  credential for anything else and never outlives `until`.
* **The open's receipt never keeps the ticket.** The open is a PUSH, so a
  repeated `operationId` replays its first result. A replay answers the
  ticket redacted, and a caller that needs another connection opens again
  under a new `operationId`. A bearer secret written into a durable
  receipt would outlive its purpose, and would be copied wherever the
  receipts are copied.
* A road with no headers of its own carries the ticket where it can. A
  browser cannot set headers on a WebSocket, so the ticket travels in the
  URL's query. It is single-use, so a logged URL cannot be replayed.

## Frames on the wire

Every frame carries its `seq`, then one typed payload (`spec/frames.md`).
The road supplies framing and integrity: a WebTransport stream or datagram,
a QUIC stream, or a WebSocket message. A channel has two lanes, and a road
that has only one carries the first:

| lane | delivery | carries | on loss |
|---|---|---|---|
| **log** | reliable, ordered (a stream) | entries of the log, both directions | the road retransmits; a broken stream is a closed channel |
| **hint** | unreliable, unordered (datagrams) | advisory frames, such as a peer's latest held control, so a receiver can predict | nothing; a hint is never an entry and decides nothing |

A hint MUST NOT change the log or any decision. Only frames on the log lane
are entries.

## Identity and idempotency

An inbound frame's intent is named by its position. Its `operationId` is
derived, never sent: `channel:<log IRI>:<seq>`. Two frames at one `seq` are
one intent:

* the same payload is a replay, and is acknowledged without being applied
  twice;
* a different payload is refused (`seq_taken`), as a different value under
  a held IRI is refused by a record store.

The log entry is its own receipt: it is durable, readable by PULL, and holds
exactly what was accepted. So the receipt-retention question `spec/idempotency.md`
leaves open does not arise for channel frames. A receipt lives as long as
the log does.

## Who may write

Anyone the open admitted may read. Only a caller the seam names as a
writer of the log may propose entries, for example the creator of a session
whose clock that caller owns. Any other ticket is read-only, and a frame
proposed on it closes the channel (`channel_read_only`).

## A log with several writers

Two writers proposing by the log's position would race for every `seq`, and
whoever lost would be refused for no fault of its own. So a log with several
writers gives each one a **lane**:

* **A writer proposes by its lane's position.** Its ticket names the lane
  and where the lane has reached (`lane`: its entries so far). Inbound frames
  carry that position, not the log's. The seam appends each accepted entry to
  the log at the log's next `seq`, and the outbound frame carries that `seq`
  as always. An intent is named `channel:<log IRI>:<lane>:<n>`. Replay,
  `seq_taken` and `seq_gap` hold per lane.
* **The seam stamps the lane.** A writer proposes an entry without naming its
  lane, and the seam records the lane its ticket holds. The entry goes out
  naming it, so readers know whose it is. No writer can write as another.
* **A mark is not an entry.** When the log has a clock, a writer says how far
  it has gone with a mark: every entry it will propose before tick T is
  already on its lane. The mark carries the lane's current position without
  taking one. A mark at a held position for a tick already passed is a
  replay. The seam keeps each lane's mark and appends the clock's advance
  when every lane is through a tick past the last one. The log's clock is
  then the slowest writer's word, and the seam needs no timing policy of its
  own. An advance a writer proposes on its lane is refused
  (`frame_unexpected`): it is the seam's alone.
* **One order.** The log interleaves lanes as their entries arrive, so its
  order is not the order a reader applies them in. Every peer applies one
  tick's entries by lane, then in lane order. That order is part of the
  log's contract, and a replay sorts by it.

A reader may run ahead of the log by predicting the lanes it has not heard
from, and correct itself when the log says otherwise (rollback). That is the
reader's business. The log never holds a prediction, and the seam's advance
is what every reader checks itself against.

## What a verified log asks of its sim

An advance is checked by replay. The host and every writer and reader run
the same sim over the same log and compare hashes, often on different
engines: a host on one runtime and pages in whatever browser each person
uses. The check is only as good as the sim's arithmetic. A step that uses
an operation its language leaves implementation-approximated gives each
engine a game of its own, and the first unequal advance then reads as a
cheat or a desync when it is neither.

So a sim whose log a channel verifies by replay MUST compute its state only
with operations its language defines exactly. In ECMAScript that means:

* integers kept where doubles are exact, or within int32;
* `Math.imul`, and truncating division of int32 values;
* `Math.sqrt` (correctly rounded) used only as a guess that integer
  comparison then corrects.

It MUST NOT use the transcendental functions (`Math.sin`, `exp`, `atan2`,
`hypot`, `pow` and the rest) in a step. Floating point is free outside the
step, in a view, a camera or a prediction's display, because nothing
replays it. A seam SHOULD hold a sim to this by running one corpus of logs
on every engine it expects its peers to use.

## Closing

Either side may close. The closer sends a final `close` frame naming a
reason from the table in `spec/refusals.md` (Channels), and the road ends.
On a WebSocket, the close frame is the road's own: code 1000 for an
ordinary close, otherwise 4000 with the reason as its text. A seam's own
domain reasons for refusing an entry close the channel the same way (for
example, an input stamped before the log's current tick).
A malformed frame closes the channel. A seam never skips a frame it could
not read and carries on, because the log behind it would no longer be the
log the caller thinks it fed.

## Roads

| road | lanes | reach | note |
|---|---|---|---|
| `webtransport` | log + hint | browsers, native | HTTP/3 over QUIC: streams and datagrams on one connection, no head-of-line blocking between them |
| `quic` | log + hint | native peers | the same over a raw QUIC connection; the road's ALPN names the frame digest's version |
| `websocket` | log only | everywhere | TCP head-of-line blocking; fine for spectating and LAN play |

A seam lists the roads it offers in its CID. A caller asks for roads in its
order of preference. A seam offers a road only while it can carry it; a road
that is down is not offered, and a caller that also asked for another gets
that one.

**On a stream road**, the log lane is one bidirectional stream, and a stream
is a byte stream. Each channel message on it is a minimal LEB128 length,
then the message. A stream is not seen by its peer until its opener writes,
and a reader would otherwise never write, so the caller writes a hello
first. On `quic` the hello names the log and the ticket (`<log> <ticket>`).
On `webtransport` the URL names them, and the hello is an empty message.

**A road may be a relay.** A process other than the seam may terminate a
road, provided it decides nothing. It presents the caller's ticket to the
seam's own channel, the seam admits that connection as it admits any, and
the relay carries every log frame byte for byte both ways. The seam is then
still the only one to read, check and append, whatever the road. A relay
may carry the hint lane itself, since hints are never entries: it fans each
one out to the log's other connections, and keeps none. It refuses to serve
a seam whose frame digest differs from its own.

**A hint is one frame.** A hint datagram is exactly one frame of a kind the
layout marks as a hint (`spec/frames.md`), with no position, since it is not
an entry. Anything else is dropped, including a mark or an advance. A hint
is never refused with a close, because the lane is unreliable by design and
dropping is what it does. A hint may name its sender's lane, but nothing
checks that: a hint only changes what a reader predicts, and a wrong one
costs that reader a correction, never the log.

**A hint is worth sending twice.** On one connection a datagram sent with a
stream frame usually travels in the same packet, so a hint sent with its
entry is lost when the entry is, and is no earlier than the entry's resend.
A writer SHOULD hint its held control again later, on a later packet. With
every mark is enough. A repeated hint costs a datagram, and a reader takes
the newest.

**A road that goes away says so.** A seam or relay that stops closes every
channel it carries with `road_closed`, so a caller falls back at once. A road
can still die without a word, and a caller MUST NOT wait on its transport's
idle timeout (tens of seconds on QUIC) to notice. A proposal unanswered for
a bound the caller sets (two seconds, say, against a 33 ms tick) means the
road is lost: the caller closes it and carries on by PULL and PUSH. A relay
SHOULD also advertise a short idle timeout, since the shorter of the two
peers' timeouts governs.

## Evidence

A reference seam, UC_GameSurface in the IQ monorepo, carries a real-time
game: a deterministic integer sim, inputs as the only thing that travels,
host verification by replay. It measured the problem this answers:

* polling `session.inputs.since` at 200 ms reached the host's exact state
  with no mismatches, which is enough for spectating, though not for
  co-play (F1);
* through the box's gate each admission costs about 80 ms, so asking per
  frame bounds play below real time. One admission per channel removes it
  from the frame path, as handing the input log over in batches already does
  (`session.inputs.append`: 37–43× real time against 0.5× asking per tick);
* typed frames compiled from the closed shapes decode and check in about
  120 ns per entry, against about 500 ns for JSON plus a shape check, at
  5 bytes against 59 (`spec/frames.md`).

The WebSocket road is built there to this text, log lane only:

* the open is a gated PUSH answering a one-use ticket, and the receipt
  keeps the ticket redacted;
* the log lane carries input entries and the host's advances, `{tick,
  hash}`, as typed frames (`spec/frames.md`). A writer proposes both. The
  host replays every advance, and its echo, carrying the host's hash, is
  the verdict;
* every refusal in the Channels table closes the channel and is journaled;
* a caller that loses its channel reads the log by PULL and carries on by
  PUSH, and the host ends where the caller does;
* an agent verified on every tick over one channel ran at 153× real time
  in 3 calls, against 25× in 1,623 calls with a PUSH per tick. An advance
  is proposed, replayed by the host, committed and echoed in 0.28 ms at
  p50 (0.39 ms at p95) on loopback, against a 33 ms tick.

The `webtransport` and `quic` roads are built there as a relay to this
text, both lanes:

* a native peer writes the log over QUIC and the host checks every advance.
  A WebSocket reader of the same log sees the same entries. A browser plays
  and spectates over WebTransport, pinning the relay's certificate by hash;
* hints fan out to the log's other connections on either road, a hint that
  is not exactly one frame is dropped, and no hint touches the log;
* the seam's refusals arrive as the road's own close, reason intact, and a
  relay that stops closes everything it carries as `road_closed`. A relay
  killed mid-game is noticed within the caller's bound, and the host still
  ends where the caller does;
* an advance round trip through the relay takes 0.4–0.6 ms at p50 on
  loopback (QUIC, native peer) and 2.3 ms in headless Chromium
  (WebTransport). Through the reference box's own seam, store and gate it
  takes 0.53 ms at p50 and 0.77 ms at p95, after an open costing 361 ms,
  which is the gate's per-admission latency paid once.

A log with several writers is built there for co-play: two seats, a lane
each, and the host's advance appended from the seats' marks:

* each seat runs the sim ahead of the log by prediction and rollback. Over
  240 ticks at 30 Hz both seats ended on the host's hash, and every advance
  each checked agreed (80 of 80), at 0, 50 and 250 ms of injected one-way
  delay. At 250 ms a seat predicted at most 12 ticks ahead and waited
  beyond that;
* a spectator replaying the interleaved log by PULL, in the one order,
  reached the host's hash;
* the lanes refuse as one log does (`seq_taken`, `seq_gap`, replays), a
  writer cannot propose an advance, and a restart rebuilds every lane's
  position from the log;
* two browser windows co-played over WebTransport with hints, and a wrong
  hint cost a correction and left the log untouched;
* under loss, through a lossy road in front of the relay (30 ms each way
  on each hop, so 60 ms at best from seat to seat), hints earned their
  keep:

  | loss each way | no hints, p95 | a hint per input | hinted again with every mark |
  |---|---|---|---|
  | 0% | 67 ms | 67 ms | 67 ms |
  | 10% | 292–325 ms | 214–295 ms | 132–214 ms |

  Each figure is how late the other seat knew an input. With one hint per
  input, when the hint was lost the log was late too (125–196 ms at p50),
  which is the shared packet above. Every lossy game still ended on the
  host's hash;
* a writer whose road died without a word stopped at its prediction window
  within 12 ticks, so the silent loss took only what it had written in that
  window. The two-second bound then held the game for 2.5–2.7 s, until
  the writer re-opened its lane and resent what the ticket said the seam
  lacked. The log held the lane exactly as it was written.

The sims there are held to every engine their peers use (the section
above):

* the same 600 games (about 412,000 ticks played to each game's end) gave
  equal hashes at every 100 ticks on JavaScriptCore (Bun, and Safari's own
  build), V8 (Chrome) and SpiderMonkey (Firefox);
* over the same 20,000 inputs, the three engines' `Math` functions gave
  different bits for 13 of the 15 tried, by 1–2 ulps, on up to 760 of 2,000
  inputs (`tan`). Only `sqrt` agreed everywhere, and `pow` did over the
  inputs tried. A step using any of the 13 would part engines within a
  game;
* Firefox played the 3D sim over WebTransport, and the host, on another
  engine, agreed with every advance.
