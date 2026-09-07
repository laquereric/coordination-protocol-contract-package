# Kinds

`kind` in `.cpcp/package.json` says what a repo **is**, and a reader uses it to
know what to expect before reading anything else.

| kind | is | serves a seam |
|---|---|---|
| `cpcp-contract` | the contract home: spec, ontology, the format itself | no |
| `cpcp-registry` | naming, versioning, the method and seam registries | no |
| `cpcp-demo` | a runnable reference: CIDs, a stub seam, example callers | yes, evaporating |
| `cpcp-application` | a real application that serves or calls a seam | usually |
| `deployment` | how one or more applications are *run*: images, compose, ingress, secrets | no — it deploys things that do |
| `language_implementation_template` | a starting point for building one of the above, in one language | no — it is copied, not run |

The first four describe things that exist. The last two describe, respectively,
how something is **run** and how something is **started**.

## `deployment`

A repo whose product is a running arrangement rather than an application: the
images, the compose or deploy scripts, the ingress, the secret plumbing.

It serves no seam of its own and declares none. What it declares is what it
*runs* — and therefore where exposure is genuinely measurable, because a
deployment repo is the one place that knows which ports are published.

A deployment repo carries `deploys`: each entry naming the application it runs
(by repo and revision) and the surfaces that arrangement publishes. Rule 4
applies with full force here — this is the repo that can read its own files.

## `language_implementation_template`

A repo somebody copies to start a new application in a particular language.

It is not run, so it has no exposure to measure and no live seam to describe.
That makes it the kind most likely to rot into a plausible-looking skeleton
nobody has ever executed, and the one rule below exists for that.

### A template must resolve to a running service

**An agent that finds a template must be able to reach the service that serves
the endpoints the template describes.** A template describing a seam that
exists nowhere is a shape with no referent; the agent cannot see a real
response, cannot check its own client against one, and cannot tell a live
contract from an aspirational one.

So a template declares `reference_instance`:

```json
"reference_instance": {
  "repo": "https://github.com/laquereric/magentic-market-ai-site",
  "rev": "<full sha>",
  "cid": "https://magenticmarket.ai/_cpcp/cid.json",
  "operations": ["build.list", "build.get", "build.create"],
  "liveness": "required",
  "because": "the running instance this template is extracted from"
}
```

* `cid` is an **absolute URL**, fetchable without credentials. A path is not a
  referent: an agent reading the repo cannot resolve it.
* `operations` are what the template claims that instance publishes. The
  template's validator fetches the CID and compares. A claim nobody fetched is
  the thing this rule exists to prevent.
* `liveness` is `required` or `advisory`. `advisory` needs a `because` — a
  template whose reference is *expected* to be unreachable is a real case
  (nothing deployed yet), and it has to say so rather than let a network
  failure read as a passing check.

A template repo that declares no `reference_instance` fails. Being a starting
point is not an exemption from pointing at something that runs; it is the
reason to.

### Templates carry their own validator

Every template ships a script that checks a copy of it still conforms — the
layout it promises, the manifest it carries, and the reference instance it
names. It runs in CI **beside** `check-repo-format.py`, not instead of it: the
format checker holds the `.cpcp` manifests, the template validator holds
everything the template claims that is not a manifest.

Neither subsumes the other, and a template that runs only one of them is
checking half of what it promises.

---

## Notes

**[1] Why `deployment` is separate from `cpcp-application`.**
An application knows what it serves; only a deployment knows where. Keeping
them one kind is what made exposure claims unfalsifiable — four ports in one
repo and two in another asserted loopback while bound to `0.0.0.0`, and in both
cases the deployment files were the evidence that settled it. A repo whose
entire subject is those files should say so.
