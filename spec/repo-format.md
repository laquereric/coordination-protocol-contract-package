# Repo format

A CPCP package repo declares its interface in `.cpcp/`. Machine readers start at
`.cpcp/package.json`; humans start at `README.md`.

```text
.cpcp/package.json            index. Always present.
.cpcp/<scope>/package.json    one per scope the repo SERVES. Zero or more.
```

Scope directory names are the scope names exactly: `public_cpcp`,
`pod_internal_cpcp`, `pod_external_cpcp` ([scopes](scopes.md)).

**A terse interface spec is the point.** A CID and a caller that runs say what a
paragraph cannot: what the methods are, what they accept, what comes back. Prose
explains; it does not specify. Everything under [Optional](#optional) can be
skipped by a conforming repo, and a repo that skips all of it is still a CPCP
package.

Every requirement below names the test that decides it. The test is
`tooling/check-repo-format.py`; run it before claiming conformance.

## Required

### Index — `.cpcp/package.json`

| Field | When | Test |
|---|---|---|
| `kind` | always | one of `cpcp-contract`, `cpcp-registry`, `cpcp-demo`, `cpcp-application` |
| `version` | always | equals `1` |
| `name`, `description` | always | non-empty |
| `contract` | every repo except the contract home | `{repo, rev}`, both non-empty |
| `registry` | when methods are served | `{repo, sha}` |
| `cids` | when CIDs are declared | each entry resolves, and carries at least one example — see rule 7 |
| `scopes.manifests` | when scopes are served | `{scope: path}`; each path is a file, each scope is a real scope name |
| `unscoped_seams` | when any exists | each entry has a `because` |

### Scope manifest — `.cpcp/<scope>/package.json`

| Field | When | Test |
|---|---|---|
| `kind` | always | equals `cpcp-scope` |
| `scope` | always | equals the directory name |
| `of` | always | non-empty |
| `definition` | always | non-empty |
| `source` | always | non-empty |
| `seams` | always | a list; may be empty, and then rule 2 applies |
| `exposure` | when it can be measured | carries `evidence` naming where it was read |

### Seven rules

1. **One seam, many scopes.** A seam appears in every scope manifest it is
   reachable at. Identical method contract, different exposure — one seam under
   two rules, never two seams.
   *Test: reported, not decided. Ids are free text; the checker prints seam ids
   per scope for a reader to judge.*

2. **An empty scope still gets a manifest.** `seams: []` plus a `because` naming
   what serves that scope instead. An omitted scope cannot be told apart from an
   overlooked one.
   *Test: empty `seams` without a `because` fails.*

3. **A seam with no scope goes in the index, not a folder.** Under
   `unscoped_seams`, with a `because`. Choosing a folder to tidy the tree invents
   contract.
   *Test: an `unscoped_seams` entry without a `because` fails.*

4. **Exposure is measured.** Read published ports from the deployment files and
   record which file. Restating the method-to-scope map is not evidence.
   *Test: an `exposure` block without `evidence` fails. Whether the citation is
   TRUE is not decidable here — a wrong line number is still a wrong line number.*

5. **Pin by full SHA.** Forty characters. An abbreviation is not an object a
   reader can verify, and stops being unique as a repo grows.
   *Test: a hex `rev`/`sha`/`self_rev` shorter than forty characters fails.*

6. **Reference by repo and revision, not by path.** A manifest naming a vendored
   checkout path couples this repo to a consumer's directory layout.
   *Test: reported, not decided.*

7. **Every CID has at least one example caller.** One working caller, in any
   language, per CID. A CID nobody can run is a claim; a CID with a caller is an
   interface. One is the requirement — a repo whose purpose is demonstration
   carries many, and that is a choice, not the bar.
   *Test: each `cids` entry declares `examples`, and every path resolves.*

```json
"cids": [
  { "cid": "cid/pull-note.cid.json", "examples": ["examples/python/pull.py"] }
]
```

A bare string in `cids` declares no caller and fails rule 7.

## Optional

None of this is required, and a repo without it conforms.

| | |
|---|---|
| `not_a_seam` | surfaces a reader might mistake for seams, and why they are not |
| `gates` | the checkers holding these claims |
| `invariants` | in a scope manifest: what must hold at that scope |
| more than one example per CID | one is the bar; more is demonstration |
| per-language or per-directory READMEs | |
| **elaborate documentation of any kind** | tutorials, rationale, worked examples, architecture notes |

Elaborate documentation is optional **because the CIDs are the specification**.
Prose that restates a CID is a second source of truth that will drift from the
first. Write it if it helps a reader; do not write it to satisfy this format,
and never let it stand in for a CID or a caller.

## Worked example

`magentic-stack` serves seams and carries all four files:

```text
.cpcp/package.json                    index; registry by SHA; switchyard-offline
                                      under unscoped_seams with its because
.cpcp/public_cpcp/package.json        seams: [] — the reference public surface
                                      is cpcp_demo
.cpcp/pod_internal_cpcp/package.json  back, vault, bus, persist, mind
.cpcp/pod_external_cpcp/package.json  back (host), plus published surfaces that
                                      are not seams
```

`back` appears in two scope manifests, by rule 1.

## The test

```bash
python3 tooling/check-repo-format.py [REPO ...]
```

No argument checks the contract home; otherwise point it at any package repo, or
several. It reads only `.cpcp/` and the paths that manifest declares. It also
resolves declared paths against the tree — not one of the seven rules, and it
earns its place: a manifest naming a file that does not exist is how a manifest
and its repo drift apart when files move.

`tooling/plant-repo-format.py` breaks each rule in a temporary repo and requires
refusal. A checker nobody has watched fail is a guess about what it would do.

## This repo

The contract home serves no seam and draws no route: an index and **no scope
directories**, by rule 2's converse. A scope directory says *this repo serves
that scope*, and three empty ones here would say something false. A repo that
serves nothing carries the index alone.
