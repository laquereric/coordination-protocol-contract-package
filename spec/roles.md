# Roles

A CPCP unit is **four roles**. They are not a deployment preference: the
reference implementation states the conformance claim directly —

> Co-locating FRONT and BACK in one container is **not** a conformant CPCP
> deployment.

— so a reader of a `.cpcp/` manifest is entitled to know which role a repo
reifies, and to be told rather than left to infer it from a directory name.

Scope says *how far a surface reaches*. Role says *what a container is for*.
Neither substitutes for the other, and a manifest carrying only one leaves a
reader guessing at the other.

## The four roles

| Role | Is for | Serves a seam |
|---|---|---|
| **FRONT** | The surface users see, and a bounded view onto what BACK holds. | **No.** It calls; it publishes no method and no CID. |
| **BACK** | Context, memory, and the `/_cpcp` contract seam. Authoritative, synchronous. | **Yes.** It is the seam. |
| **BackJob** | Durable asynchronous work, on the same image as BACK. | No. No ingress. |
| **GRAPH** | The unit's RDF/SPARQL store, projected from BACK's models. | No. BACK holds the authority. |

Two of these are load-bearing for conformance and two are structural:

* **FRONT must be distinct from BACK.** A FRONT co-located with its BACK can
  reach domain state without crossing the seam, and a seam that can be bypassed
  is not a boundary. This is the claim above, and the one rule here that a
  manifest can be caught violating.
* **BackJob is separate from BACK.** In-process jobs on BACK make a synchronous
  authority do asynchronous work; the split is what keeps BACK's answer prompt
  and its writes ordered.
* **GRAPH is downstream of BACK, never beside it.** It is a projection. A writer
  reaching GRAPH directly has invented a second authority.

## Declaring a role

A repo that reifies a role says so in `.cpcp/package.json`:

```json
"role": {
  "name": "BACK",
  "of": "magenticmarket.ai",
  "also_reified": {
    "BackJob": "the same image running bin/jobs",
    "GRAPH": "per-unit oxigraph, projected from the Rails models",
    "FRONT": "cpcp/front/app.py, a separate container on the pod network"
  },
  "separate_containers": true
}
```

* `name` — one of the four, exactly. The set is closed.
* `of` — which unit. A role is always a role *of* something; a repo that
  reifies BACK for two units is describing two units.
* `also_reified` — other roles this repo ships, each as its own container.
  A repo commonly carries several: one image, several commands.
* `separate_containers` — **required when FRONT and BACK both appear.** The
  conformance claim is about containers, not repositories, so a repo carrying
  both must state that it does not co-locate them. Silence there is exactly the
  arrangement the claim forbids, and the manifest would otherwise read as
  conformant while describing a non-conformant unit.

### A role may be reified outside the unit's pod

The role says what a container is for; it does not say the container sits
beside the others. A FRONT reached over the internet is still a FRONT — it
declares `dependency` rather than `pod_internal_dependencies`, because its
reach is different while its purpose is not.

One role can therefore have several reifications: a reference client inside the
repo and a real one somewhere else, both FRONT. That is not a conflict, and a
manifest naming only the in-repo one tells a reader something false by omission.

## What this does not do

It does not say how a unit is deployed, orchestrated, or scaled; it names four
purposes and one prohibition. It does not require a repo to declare a role — a
library that serves and calls nothing has none — and a repo that declares none
is not thereby non-conformant.

---

## Notes

**[1] Reifications in the wild.**
[magentic-market-ai-site](https://github.com/laquereric/magentic-market-ai-site)
is a BACK that also reifies BackJob, GRAPH and an in-repo reference FRONT.
[express-meaning](https://github.com/laquereric/express-meaning) is a second
FRONT for the same unit, in another language and another repository, reaching
that BACK at `services` scope rather than across a pod network.

**[2] Where the roles are elaborated.**
[magentic-stack](https://github.com/laquereric/magentic-stack)
`docs/architecture/OVERVIEW.md` describes these four alongside SWITCH and MIND,
which belong to that deployment's pod architecture rather than to this contract.
A repo extending the set cites its own definition with `role.defined_by`
(`{repo, rev, doc}`); the four here are the ones CPCP itself claims.
