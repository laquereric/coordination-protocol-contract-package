# Repo format

Every CPCP package repo carries a machine manifest under `.cpcp/`. Machine
readers start at `.cpcp/package.json`; humans start at `README.md`.

```text
.cpcp/package.json            index. Always present.
.cpcp/<scope>/package.json    one per scope the repo SERVES. Zero or more.
```

Scope directory names are the scope names exactly: `public_cpcp`,
`pod_internal_cpcp`, `pod_external_cpcp` (see [scopes](scopes.md)).

## The index

`.cpcp/package.json` carries what is not scope-specific.

| Field | Required | Meaning |
|---|---|---|
| `kind` | yes | `cpcp-contract`, `cpcp-registry`, `cpcp-demo`, `cpcp-application` |
| `version` | yes | manifest schema version, currently `1` |
| `name`, `description` | yes | what this repo is |
| `contract` | yes, except in the contract home | `{repo, rev}` the revision this repo implements |
| `registry` | when methods are served | `{repo, sha}` |
| `scopes.manifests` | when scopes are served | `{scope: path}` for each scope directory |
| `unscoped_seams` | when any exists | seams with no declared scope, each with a `because` |
| `not_a_seam` | optional | surfaces a reader might mistake for seams, and why they are not |
| `gates` | optional | the checkers that hold these claims |

## A scope manifest

`.cpcp/<scope>/package.json` describes one scope as this repo serves it.

| Field | Required | Meaning |
|---|---|---|
| `kind` | yes | `cpcp-scope` |
| `scope` | yes | must equal the directory name |
| `of` | yes | the repo it belongs to |
| `definition` | yes | what the scope means, from `spec/scopes.md` |
| `source` | yes | where the definition came from |
| `seams` | yes | may be empty; see the empty-scope rule |
| `exposure` | when it can be measured | measured, not asserted |
| `invariants` | optional | what must hold at this scope |

## Six rules

1. **One seam, many scopes.** A seam appears in every scope manifest it is
   reachable at. The method contract is identical at every scope and exposure is
   not, so that is one seam under two exposure rules, never two seams.

2. **An empty scope still gets a manifest.** `seams: []` plus a `because` naming
   what serves that scope instead. An omitted scope cannot be told apart from an
   overlooked one.

3. **A seam with no scope goes in the index, not a folder.** Under
   `unscoped_seams`, with a `because`. Choosing a folder for it to tidy the tree
   invents contract.

4. **Exposure is measured.** Read published ports from the deployment files and
   record which file. Do not restate the method-to-scope map and call it
   evidence.

5. **Pin by full SHA.** Forty characters. An abbreviation is not an object a
   reader can verify and stops being unique as a repo grows.

6. **Reference by repo and revision, not by path.** A manifest that names a
   vendored checkout path couples this repo to a consumer's directory layout.

## Worked example

`magentic-stack` serves the seams and carries all four files:

```text
.cpcp/package.json                    index; registry by SHA; switchyard-offline
                                      under unscoped_seams with its because
.cpcp/public_cpcp/package.json        seams: [] - no public seam here, the
                                      reference public surface is cpcp_demo
.cpcp/pod_internal_cpcp/package.json  back, vault, bus, persist, mind
.cpcp/pod_external_cpcp/package.json  back (host), plus published surfaces that
                                      are not seams: config UI, FRONT page
```

`back` appears in two scope manifests, by rule 1.

## Checking a repo against this format

```bash
python3 tooling/check-repo-format.py [REPO ...]
```

With no argument it checks the contract home; point it at any package repo, or
several at once. It reads only `.cpcp/`. It holds the required fields, keeps a
scope directory and its manifest agreeing about which scope they are, requires
a `because` where rules 2 and 3 require one, requires exposure to cite evidence
(rule 4), and refuses an abbreviated SHA (rule 5). It also resolves declared
paths against the tree, which is not one of the six rules: a manifest naming a
file that does not exist is how a manifest and its repo drift apart when files
move.

Two things it cannot decide, and does not pretend to:

* **Rule 1** needs to know that two seam entries in two scope manifests are the
  *same* seam. Ids are free text, so the checker prints seam ids per scope and
  leaves that judgement to a reader.
* **Rule 4** can require that exposure cites evidence. It cannot tell whether
  the citation is true — a wrong line number is still a wrong line number.

`tooling/plant-repo-format.py` breaks each rule in a temporary repo and requires
the checker to refuse it. A checker nobody has watched fail is a guess about
what it would do.

## This repo

The contract home serves no seam and draws no route, so it has an index and
**no scope directories** - by rule 2's converse: a scope directory says *this
repo serves that scope*, and three empty ones here would say something false.
A repo that serves nothing carries the index alone.
