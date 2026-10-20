# Frames: closed shapes compiled to the one layout they admit

**Status: proposed.** Not extracted from production; see [Evidence](#evidence).

A CPCP payload is typed by a closed SHACL shape. On the JSON-RPC-LD envelope
that shape is checked per message, and at a few messages a second the cost
does not matter. A channel (`spec/channels.md`) may carry thousands of entries
a second, where a shape engine per frame is the hot path. The typing does not
have to be given up there. It can be paid for once, ahead of time.

**A closed shape whose every property is required and bounded has exactly one
fixed binary layout.** Two parties that agree on that layout's digest, once,
need no validator per frame: decoding a frame *is* checking it. The codec
cannot produce a value the shape refuses, and it refuses every byte string
that would decode to one.

## Which shapes are frames

A shape is a frame shape when it names a tag:

```turtle
cpcp:InputEntryShape a sh:NodeShape ;
  sh:targetClass cpcp:InputEntry ;
  cpcp:frameTag 0 ;
  sh:closed true ;
  sh:property [ sh:path cpcp:tick ; sh:datatype xsd:integer ; sh:minInclusive 0 ; sh:minCount 1 ; sh:maxCount 1 ] ;
  sh:property [ sh:path cpcp:action ; sh:node cpcp:ThrustActionShape ; sh:minCount 1 ; sh:maxCount 1 ] .
```

`cpcp:frameTag` is 0–255 and unique within a CID. Tags are append-only: a
tag, once published, always names the same frame.

## The layout

| part | encoding |
|---|---|
| frame | `tag:u8`, then the shape's fields |
| field order | `sh:order`, then the property path's IRI |
| `sh:node S` | S's fields, inline. S is closed and every rule here holds for it |
| `sh:in ( … )` | enum: `u8`, the value's index in the list's order (1–256 entries) |
| `xsd:integer`, min and max | `v − min` as `u8` if the span < 2⁸, `u16le` if < 2¹⁶, `u32le` if < 2³² |
| `xsd:integer`, min only | `v − min` as unsigned LEB128, at most 2⁵³ − 1 |
| `xsd:integer`, no bounds | zigzag LEB128 |
| `xsd:boolean` | `u8`, 0 or 1 |

Every property is `sh:minCount 1` and `sh:maxCount 1`, so a frame has no
presence bits and no length prefixes inside it. A shape outside these rules
is not a frame shape, and a compiler refuses it rather than compiling part
of it:

| refusal | when |
|---|---|
| `not_closed` | the frame shape, or a shape it nests, is not `sh:closed true` |
| `not_required` | a property is not exactly once |
| `not_fixed_layout` | a property is none of the kinds above, or its span does not fit 32 bits |
| `bad_tag` | a tag outside 0–255, or two frames with one tag |

## One value, one encoding

Varints MUST be minimal, and a decoder refuses a longer form. So a frame's
bytes are its identity: hashing the bytes names the value, and two parties
that agree on a value agree on its bytes. A decoded value re-encodes to the
bytes it came from.

## The digest

The **frame digest** is `sha256:` over the canonical JSON of the compiled
layout: every frame's tag, shape, and fields with their kinds, bounds and enum
values, keys sorted. It is not computed over the Turtle, so reformatting the
shapes changes nothing, while changing a bound, an enum or a field changes it.

The digest is what a channel's open names (`spec/channels.md`). Peers that
disagree are refused at open (`frame_digest_mismatch`), never mid-stream.
A CID that offers frames publishes its digest beside its shapes.

## Decoding

A decoder answers either the value, its tag and its size, or a refusal:

| reason | meaning |
|---|---|
| `unknown_frame` | a tag this layout does not have |
| `frame_malformed` | a field's bytes are not a value of its kind and bounds (for example, an enum index past its list, an integer past its max, a non-minimal varint); names the field |
| `frame_truncated` | the bytes end inside a frame |

On a channel each of these closes the channel (`spec/channels.md`, Closing).

## What the shapes still do

The shapes stay the contract. The layout is derived from them, never written
beside them, so there is no second copy to drift (`spec/repo-format.md`).
A compiler's output is checked against the shapes in CI: regenerate, and
refuse a codec on disk that differs. The JSON-RPC-LD envelope and its
per-message SHACL check are unchanged for every method. Frames type the
entries a channel carries, and only those.

## Evidence

The reference seam in UC_GameSurface (IQ monorepo) compiles its input-entry
shape with this rule, generating a straight-line codec, and holds the codec to
the shapes:

* every valid entry round-trips, including at each varint width;
* the encoder refuses exactly the values the shapes' own check refuses
  (317 values tried), and the decoder refuses every out-of-range byte,
  naming the field (256 tried);
* of 200,000 random byte strings, decoding never throws, and each of the
  ~9,800 it accepts satisfies the shape and re-encodes to the same bytes;
* per entry: about 120 ns for encode plus decode, the check included, at
  5 bytes, against about 500 ns for JSON stringify plus parse plus a shape
  check, at 59 bytes (Bun 1.4.3, Apple silicon).
