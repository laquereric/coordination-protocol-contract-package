#!/usr/bin/env python3
"""Hold a CPCP package repo's .cpcp/ manifests against spec/repo-format.md.

The format is published and was, until now, enforced by whoever remembered it.
cpcp_demo carried no scopes block at all while the spec named that repo directly
in its own method-to-scope map, and an abbreviated rev besides -- both found by
reading, which is not a method that scales past the reader who happens to look.

Usage:
    python3 tooling/check-repo-format.py [REPO ...]

With no argument it checks the repo this script lives in. Point it at any
package repo -- the format is the contract's, not any one repo's:

    python3 tooling/check-repo-format.py ../cpcp_demo ../magentic-stack

Stdlib only, so it runs anywhere a CPCP repo does.

WHAT IT CANNOT CHECK, said plainly rather than left to be discovered:

  Rule 1 (one seam, many scopes) needs to know that two seam entries in two
  manifests are the SAME seam. Nothing in the format makes that decidable --
  ids are free text -- so this reports seam ids per scope and leaves the
  judgement to a reader.

  Rule 4 says exposure is MEASURED. This can require that an exposure block
  cites evidence; it cannot verify the citation is true. A wrong line number is
  still a wrong line number.
"""
from __future__ import annotations

import json
import os
import re
import sys

KINDS = ("cpcp-contract", "cpcp-registry", "cpcp-demo", "cpcp-application",
         "deployment", "language_implementation_template")

# A template is copied, not run: it has no exposure to measure and no live seam.
# That makes it the kind most likely to rot into a plausible skeleton nobody has
# executed, which is what rule 10 is for.
TEMPLATE_KIND = "language_implementation_template"
DEPLOYMENT_KIND = "deployment"
LIVENESS = ("required", "advisory")
# Direction x reach. Both axes are named, so neither has to be inferred.
#
#                      calls (outbound)            serves (inbound)
#   beyond the pod     dependency                  services
#   within the pod     pod_internal_dependencies   pod_internal_services
SCOPES = ("dependency", "pod_internal_dependencies",
          "pod_internal_services", "services")

# The outbound half: entries are CIDs this repo CALLS, and carry depends_on.
DEPENDENCY_SCOPES = frozenset({"dependency", "pod_internal_dependencies"})

# A CPCP unit is four roles (spec/roles.md). Closed set: an unknown name is a
# role this contract does not define, and a reader resolving it comes up empty.
ROLES = ("FRONT", "BACK", "BackJob", "GRAPH")

# 'published' means the producer's CID names the operation today. Anything
# else is a dependency the caller is waiting on, and rule 8 makes it say why.
DEPENDENCY_STATUSES = ("published", "unbuilt", "retired")
FULL_SHA = re.compile(r"\A[0-9a-f]{40}\Z")
SHA_KEYS = ("rev", "sha", "self_rev", "revision")

# A value treated as a repo-relative path: no spaces, no scheme, has a directory
# separator AND an extension. "shapes/note-shape.ttl" qualifies; "linux/amd64"
# does not (no extension), nor does "spec/scopes.md at 3b9ce9b..." (spaces),
# which is prose that happens to contain a path.
PATHISH = re.compile(r"\A[A-Za-z0-9._\-]+(?:/[A-Za-z0-9._\-]+)+\.[A-Za-z0-9]+\Z")

# Keys whose value names a file in ANOTHER repo -- almost always the contract
# home, cited as the origin of a definition. Resolving them against the local
# tree asks the wrong tree.
PATH_KEYS_ELSEWHERE = ("source", "definition", "note", "because", "_why")


class Report:
    def __init__(self, repo):
        self.repo = repo
        self.errors = []
        self.notes = []
        self.manifests = 0

    def fail(self, where, message):
        self.errors.append("%s: %s" % (where, message))

    def note(self, message):
        self.notes.append(message)


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def walk_strings(node, path=""):
    if isinstance(node, dict):
        for k, v in node.items():
            yield from walk_strings(v, "%s.%s" % (path, k))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk_strings(v, "%s[%d]" % (path, i))
    elif isinstance(node, str):
        yield path, node


def check_shas(doc, where, rep):
    """Rule 5. Forty characters, or it is not an object a reader can verify."""
    for path, value in walk_strings(doc):
        key = path.rsplit(".", 1)[-1].split("[")[0]
        if key not in SHA_KEYS:
            continue
        # A revision may legitimately be a branch or tag; only hex-looking
        # values are being pinned, and a SHORT hex value is the defect.
        if re.fullmatch(r"[0-9a-f]{4,39}", value):
            rep.fail(where, "%s = %r is an abbreviated SHA; rule 5 wants forty "
                            "characters, because an abbreviation is not an object a "
                            "reader can verify and stops being unique as a repo grows"
                     % (path.lstrip("."), value))


def elsewhere_prefixes(node, path="", out=None):
    """Paths of objects that name ANOTHER repo, so their paths are its paths.

    Rule 6 says reference by repo and revision. An object doing that -- carrying
    a `repo` or a `rev` -- is describing a tree that is not this one, so a path
    beside them resolves there and checking it here is the checker being wrong
    about whose tree it is reading. That is the same mistake PATH_KEYS_ELSEWHERE
    was added for, but keyed on the citation's SHAPE rather than on remembering
    to allowlist every field name a citation might use.
    """
    out = set() if out is None else out
    if isinstance(node, dict):
        if "repo" in node or "rev" in node:
            out.add(path)
        for k, v in node.items():
            elsewhere_prefixes(v, "%s.%s" % (path, k), out)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            elsewhere_prefixes(v, "%s[%d]" % (path, i), out)
    return out


def check_paths(doc, where, repo, rep):
    """Declared paths resolve.

    Not one of the eight rules, and the reason it is here: a manifest is a claim
    about a repo, and a claim naming a file that does not exist is how the
    manifest and the tree drift apart silently -- exactly what happens when
    files move and nobody updates the index.
    """
    elsewhere = elsewhere_prefixes(doc)
    for path, value in walk_strings(doc):
        key = path.rsplit(".", 1)[-1].split("[")[0]
        # A path inside a citation belongs to the repo that citation names.
        if any(path.startswith(p + ".") for p in elsewhere if p):
            continue
        # 'source' NAMES THE CONTRACT, NOT THIS REPO. A scope manifest cites
        # spec/scopes.md because that is where its definition came from; the file
        # lives in the contract home. Checking it here reported four repos as
        # broken for correctly citing their source, which is the checker being
        # wrong about whose tree it is reading.
        if key in PATH_KEYS_ELSEWHERE:
            continue
        if not PATHISH.match(value):
            continue
        if not os.path.exists(os.path.join(repo, value)):
            rep.fail(where, "%s names %r, which does not exist in this repo"
                     % (path.lstrip("."), value))


def check_cids(index, where, repo, rep):
    """Rule 7. Every CID has at least one example caller.

    A CID nobody can run is a claim; a CID with a caller is an interface. ONE is
    the requirement -- a repo whose purpose is demonstration carries many, and
    that is a choice rather than the bar.
    """
    cids = index.get("cids")
    if cids is None:
        return
    if not isinstance(cids, list) or not cids:
        rep.fail(where, "cids must be a non-empty list when present")
        return

    for i, entry in enumerate(cids):
        # A BARE STRING DECLARES NO CALLER. The older shape listed CID paths
        # alone, which cannot express rule 7 at all -- so it fails, and says how
        # to say it instead.
        if isinstance(entry, str):
            rep.fail(where, "cids[%d] is the bare path %r and declares no example "
                            "caller; rule 7 wants "
                            '{\"cid\": %r, \"examples\": [\"...\"]}' % (i, entry, entry))
            continue
        if not isinstance(entry, dict):
            rep.fail(where, "cids[%d] must be an object with cid and examples" % i)
            continue

        cid_path = str(entry.get("cid", "")).strip()
        if not cid_path:
            rep.fail(where, "cids[%d] has no 'cid'" % i)
        elif not os.path.isfile(os.path.join(repo, cid_path)):
            rep.fail(where, "cids[%d].cid names %r, which is not a file" % (i, cid_path))

        examples = entry.get("examples")
        if not isinstance(examples, list) or not examples:
            rep.fail(where, "cids[%d] (%s) declares no example caller; rule 7 wants at "
                            "least one, in any language" % (i, cid_path or "?"))
            continue
        for ex in examples:
            if not os.path.isfile(os.path.join(repo, str(ex))):
                rep.fail(where, "cids[%d] (%s) names example %r, which is not a file"
                         % (i, cid_path or "?", ex))


def check_role(index, rel, rep):
    """Rule 9: a declared role names one of the four, and admits its co-locations.

    Declaring a role is optional -- a library that neither serves nor calls has
    none. Declaring one loosely is not: a reader uses it to know whether this
    repo is the seam or something calling it.
    """
    role = index.get("role")
    if role is None:
        return
    if not isinstance(role, dict):
        rep.fail(rel, "role must be an object with a 'name' (rule 9)")
        return

    name = role.get("name")
    if name not in ROLES:
        rep.fail(rel, "role.name is %r; expected one of %s (rule 9)"
                 % (name, ", ".join(ROLES)))

    also = role.get("also_reified") or {}
    if not isinstance(also, dict):
        rep.fail(rel, "role.also_reified must be an object keyed by role name (rule 9)")
        also = {}
    for other in also:
        if other not in ROLES:
            rep.fail(rel, "role.also_reified names %r, which is not a role; expected "
                          "one of %s (rule 9)" % (other, ", ".join(ROLES)))
        if other == name:
            # Listing your own role again says nothing and hides whether a
            # SECOND container of that role exists.
            rep.fail(rel, "role.also_reified repeats %r, which is already role.name; "
                          "a second container of the same role needs its own "
                          "description, not a duplicate key (rule 9)" % other)

    # The one claim the reference implementation makes about roles: co-locating
    # FRONT and BACK is not a conformant deployment. A repo carrying both must
    # say it does not, or the manifest reads as conformant while describing the
    # arrangement the claim forbids.
    carried = {name} | set(also)
    if {"FRONT", "BACK"} <= carried and role.get("separate_containers") is not True:
        rep.fail(rel, "role carries both FRONT and BACK but does not say "
                      "separate_containers: true; co-locating them is not a "
                      "conformant CPCP deployment (rule 9)")

    if name in ROLES:
        extra = (" (+ %s)" % ", ".join(sorted(also))) if also else ""
        rep.note("role: %s%s" % (name, extra))


def check_reference_instance(index, rel, rep):
    """Rule 10: a template resolves to a running service.

    An agent that finds a template must be able to REACH what serves the
    endpoints it describes. A template describing a seam that exists nowhere is
    a shape with no referent -- the agent cannot see a real response, cannot
    check a client against one, and cannot tell a live contract from an
    aspirational one.
    """
    ref = index.get("reference_instance")
    if index.get("kind") == TEMPLATE_KIND and ref is None:
        rep.fail(rel, "a %s declares no reference_instance; being a starting point is "
                      "not an exemption from pointing at something that runs, it is the "
                      "reason to (rule 10)" % TEMPLATE_KIND)
        return
    if ref is None:
        return
    if not isinstance(ref, dict):
        rep.fail(rel, "reference_instance must be an object (rule 10)")
        return

    cid = str(ref.get("cid", "")).strip()
    if not cid:
        rep.fail(rel, "reference_instance has no 'cid' (rule 10)")
    elif not cid.startswith(("http://", "https://")):
        # A path is not a referent: a reader outside this checkout cannot
        # resolve it, and the reader this rule exists for is outside.
        rep.fail(rel, "reference_instance.cid is %r; it must be an absolute URL an "
                      "agent can fetch, not a path (rule 10)" % cid)

    ops = ref.get("operations")
    if not isinstance(ops, list) or not ops:
        rep.fail(rel, "reference_instance names no 'operations'; a CID with no claim "
                      "about what it publishes is nothing to check against (rule 10)")

    liveness = str(ref.get("liveness", "")).strip()
    if liveness not in LIVENESS:
        rep.fail(rel, "reference_instance.liveness is %r; expected one of %s (rule 10)"
                 % (ref.get("liveness"), ", ".join(LIVENESS)))
    elif liveness == "advisory" and not str(ref.get("because", "")).strip():
        # A reference expected to be unreachable is a real case; letting a
        # network failure read as a pass is not.
        rep.fail(rel, "reference_instance.liveness is 'advisory' with no 'because'; a "
                      "reference that may be unreachable has to say why, or an outage "
                      "reads as a passing check (rule 10)")

    if isinstance(ops, list) and ops:
        rep.note("reference instance: %s (%s, %s)"
                 % (cid or "?", ", ".join(str(o) for o in ops), liveness or "?"))


def check_deploys(index, rel, rep):
    """A deployment repo names what it runs, by repo and revision."""
    if index.get("kind") != DEPLOYMENT_KIND:
        if "deploys" in index:
            rep.fail(rel, "'deploys' belongs to a %s; this repo is %r"
                     % (DEPLOYMENT_KIND, index.get("kind")))
        return

    entries = index.get("deploys")
    if not isinstance(entries, list) or not entries:
        rep.fail(rel, "a %s declares no 'deploys'; the repo whose subject is running "
                      "things has to name what it runs" % DEPLOYMENT_KIND)
        return
    for i, e in enumerate(entries):
        where = "deploys[%d]" % i
        if not isinstance(e, dict):
            rep.fail(rel, "%s must be an object" % where)
            continue
        for field in ("repo", "rev"):
            if not str(e.get(field, "")).strip():
                rep.fail(rel, "%s has no %r; only a deployment knows WHERE an "
                              "application runs, so it pins WHAT it runs" % (where, field))
    rep.note("deploys: %d application(s)" % len(entries))


def check_scope_manifest(repo, scope_dir, rep):
    rel = os.path.join(".cpcp", scope_dir, "package.json")
    full = os.path.join(repo, rel)
    try:
        doc = load(full)
    except (OSError, ValueError) as e:
        rep.fail(rel, "unreadable: %s" % e)
        return None
    rep.manifests += 1

    if doc.get("kind") != "cpcp-scope":
        rep.fail(rel, "kind must be 'cpcp-scope', found %r" % doc.get("kind"))

    # The directory name IS the scope name; a manifest that disagrees with the
    # folder it sits in cannot be read either way round.
    if doc.get("scope") != scope_dir:
        rep.fail(rel, "scope is %r but the directory is %r; they must be the same"
                 % (doc.get("scope"), scope_dir))

    for field in ("of", "definition", "source"):
        if not str(doc.get(field, "")).strip():
            rep.fail(rel, "missing %s" % field)

    # dependency runs the other way: this repo CALLS what is listed, and
    # something else serves it. The two lists are not interchangeable, so
    # each scope is held to its own field and refused the other one.
    if scope_dir in DEPENDENCY_SCOPES:
        check_depends_on(doc, rel, rep)
        if "seams" in doc:
            rep.fail(rel, "a dependency manifest carries 'depends_on', not 'seams'; "
                          "this repo does not serve what it depends on")
        if "exposure" in doc:
            rep.fail(rel, "a dependency manifest has no 'exposure'; how far the "
                          "producer's surface reaches is the producer's to measure")
    else:
        seams = doc.get("seams")
        if not isinstance(seams, list):
            rep.fail(rel, "seams must be a list (it may be empty)")
        elif not seams and not str(doc.get("because", "")).strip():
            # Rule 2: an omitted scope cannot be told apart from an overlooked
            # one, so an empty one has to say what serves that scope instead.
            rep.fail(rel, "seams is empty and there is no 'because' naming what serves "
                          "this scope instead (rule 2)")
        if "depends_on" in doc:
            rep.fail(rel, "'depends_on' belongs in a calling scope (%s); a serving "
                          "scope lists what it serves"
                     % ", ".join(sorted(DEPENDENCY_SCOPES)))

        exposure = doc.get("exposure")
        if isinstance(exposure, dict) and not str(exposure.get("evidence", "")).strip():
            # Rule 4: read it from the deployment files and record which file.
            rep.fail(rel, "exposure has no 'evidence'; rule 4 says exposure is measured, "
                          "and a restatement of the method-to-scope map is not evidence")

        if isinstance(seams, list) and seams:
            # Rule 1 puts the same seam in several manifests, so each copy
            # repeats its own scope. Only the manifest's top-level scope was
            # ever checked, which let a copy keep a name the folder had left
            # behind -- silent, and exactly wrong for the reader who trusts
            # the entry over the path. Found the hard way in a rename.
            for i, seam in enumerate(seams):
                if not isinstance(seam, dict) or "scope" not in seam:
                    continue
                if seam["scope"] != scope_dir:
                    rep.fail(rel, "seams[%d] (%s) says scope %r, but it sits in %r; a "
                                  "seam entry cannot name a scope other than the manifest "
                                  "holding it" % (i, seam.get("id", "?"),
                                                  seam["scope"], scope_dir))

            ids = [s.get("id") for s in seams if isinstance(s, dict)]
            rep.note("%s serves seams: %s" % (scope_dir, ", ".join(str(i) for i in ids)))

    # Whoever publishes the vocabulary must publish ALL of it and nothing else.
    # Downstream manifests cite this as their definition of record, so a missing
    # or invented scope here is a definition a reader would resolve and act on.
    defs = doc.get("scope_definitions")
    if defs is not None:
        if not isinstance(defs, dict):
            rep.fail(rel, "scope_definitions must be an object keyed by scope name")
        else:
            missing = [s for s in SCOPES if s not in defs]
            extra = [k for k in defs if k not in SCOPES]
            if missing:
                rep.fail(rel, "scope_definitions omits %s; a partial vocabulary is one a "
                              "downstream reader resolves and comes up empty on"
                         % ", ".join(missing))
            if extra:
                rep.fail(rel, "scope_definitions defines %s, which %s not a scope"
                         % (", ".join(extra), "are" if len(extra) > 1 else "is"))
            if not missing and not extra:
                rep.note("%s publishes the scope vocabulary: %s"
                         % (scope_dir, ", ".join(sorted(defs))))

    check_shas(doc, rel, rep)
    check_paths(doc, rel, repo, rep)
    return doc


def check_depends_on(doc, rel, rep):
    """Rule 8: every dependency names its producer and says whether it is built."""
    entries = doc.get("depends_on")
    if not isinstance(entries, list):
        rep.fail(rel, "depends_on must be a list (it may be empty)")
        return
    if not entries:
        # Rule 2 again, from the calling side: an empty dependency scope has to
        # say why it is there rather than absent.
        if not str(doc.get("because", "")).strip():
            rep.fail(rel, "depends_on is empty and there is no 'because' saying why "
                          "this repo declares the scope while calling nothing (rule 2)")
        return

    for i, entry in enumerate(entries):
        where = "depends_on[%d]" % i
        if not isinstance(entry, dict):
            rep.fail(rel, "%s must be an object, not %s (rule 8)"
                     % (where, type(entry).__name__))
            continue

        if not str(entry.get("producer", "")).strip():
            rep.fail(rel, "%s has no 'producer'; a dependency nobody serves is not "
                          "traceable to anyone (rule 8)" % where)

        ops = entry.get("operations")
        if not isinstance(ops, list) or not ops:
            rep.fail(rel, "%s has no 'operations'; naming a producer without naming "
                          "what is called declares nothing (rule 8)" % where)

        status = str(entry.get("status", "")).strip()
        if status not in DEPENDENCY_STATUSES:
            rep.fail(rel, "%s status is %r; expected one of %s (rule 8)"
                     % (where, entry.get("status"), ", ".join(sorted(DEPENDENCY_STATUSES))))
        elif status != "published" and not str(entry.get("because", "")).strip():
            # An unbuilt dependency is the one most worth recording, and the
            # reason it is unbuilt is the whole content of the record.
            rep.fail(rel, "%s is %r and has no 'because' saying how that was "
                          "determined (rule 8)" % (where, status))


def check_repo(repo):
    rep = Report(repo)
    cpcp = os.path.join(repo, ".cpcp")
    index_rel = ".cpcp/package.json"
    index_path = os.path.join(repo, index_rel)

    if not os.path.isdir(cpcp):
        rep.fail(".cpcp", "missing; every CPCP package repo carries one")
        return rep
    if not os.path.isfile(index_path):
        rep.fail(index_rel, "missing; machine readers start here")
        return rep

    try:
        index = load(index_path)
    except (OSError, ValueError) as e:
        rep.fail(index_rel, "unreadable: %s" % e)
        return rep
    rep.manifests += 1

    kind = index.get("kind")
    if kind not in KINDS:
        rep.fail(index_rel, "kind must be one of %s, found %r" % (", ".join(KINDS), kind))
    if index.get("version") != 1:
        rep.fail(index_rel, "version must be 1, found %r" % index.get("version"))
    for field in ("name", "description"):
        if not str(index.get(field, "")).strip():
            rep.fail(index_rel, "missing %s" % field)

    # THE CONTRACT HOME IS THE EXCEPTION: it does not point at a contract, it is
    # the contract.
    if kind != "cpcp-contract":
        contract = index.get("contract")
        if not isinstance(contract, dict):
            rep.fail(index_rel, "missing contract {repo, rev}: which revision of the "
                                "contract this repo implements")
        else:
            for field in ("repo", "rev"):
                if not str(contract.get(field, "")).strip():
                    rep.fail(index_rel, "contract.%s is missing" % field)

    declared = index.get("scopes", {})
    manifests = declared.get("manifests", {}) if isinstance(declared, dict) else {}
    if not isinstance(manifests, dict):
        rep.fail(index_rel, "scopes.manifests must be an object of {scope: path}")
        manifests = {}

    on_disk = sorted(
        d for d in os.listdir(cpcp)
        if os.path.isdir(os.path.join(cpcp, d))
        and os.path.isfile(os.path.join(cpcp, d, "package.json"))
    )

    for scope in manifests:
        if scope not in SCOPES:
            rep.fail(index_rel, "scopes.manifests names %r, which is not a scope "
                                "(%s)" % (scope, ", ".join(SCOPES)))

    # BOTH WAYS. A directory nobody declared and a declaration with no directory
    # are different mistakes, and each is invisible from the other side.
    for scope in on_disk:
        if scope not in manifests:
            rep.fail(index_rel, ".cpcp/%s/ exists but scopes.manifests does not list "
                                "it; a scope directory says this repo serves that "
                                "scope, so an unlisted one is a claim nobody made"
                     % scope)
    for scope, path in manifests.items():
        if not os.path.isfile(os.path.join(repo, str(path))):
            rep.fail(index_rel, "scopes.manifests[%r] points at %r, which is not a file"
                     % (scope, path))
        elif scope not in on_disk:
            rep.fail(index_rel, "scopes.manifests[%r] is declared but .cpcp/%s/ is not "
                                "a scope directory" % (scope, scope))

    check_cids(index, index_rel, repo, rep)
    check_role(index, index_rel, rep)
    check_reference_instance(index, index_rel, rep)
    check_deploys(index, index_rel, rep)

    for entry in index.get("unscoped_seams", []) or []:
        if isinstance(entry, dict) and not str(entry.get("because", "")).strip():
            # Rule 3: a seam with no scope goes in the index WITH a because;
            # choosing a folder to tidy the tree invents contract.
            rep.fail(index_rel, "unscoped_seams entry %r has no 'because'"
                     % entry.get("id", "?"))

    check_shas(index, index_rel, rep)
    check_paths(index, index_rel, repo, rep)

    for scope in on_disk:
        check_scope_manifest(repo, scope, rep)

    if not on_disk:
        rep.note("no scope directories: this repo declares it serves no seam")
    return rep


def main(argv):
    repos = argv[1:] or [os.path.dirname(os.path.dirname(os.path.abspath(__file__)))]
    total_manifests = 0
    failed = False

    for repo in repos:
        repo = os.path.abspath(repo)
        rep = check_repo(repo)
        total_manifests += rep.manifests
        name = os.path.basename(repo)
        for n in rep.notes:
            print("  %s: %s" % (name, n))
        if rep.errors:
            failed = True
            print("REPO-FORMAT FAIL %s (%d)" % (name, len(rep.errors)), file=sys.stderr)
            for e in rep.errors:
                print("  " + e, file=sys.stderr)
        else:
            print("  %s: OK (%d manifest(s))" % (name, rep.manifests))

    # ZERO EXAMINED IS NOT A PASS. A path typo that made this look at nothing
    # would otherwise read as compliance.
    print("population: %d manifest(s) across %d repo(s)" % (total_manifests, len(repos)))
    if total_manifests == 0:
        print("REPO-FORMAT FAIL: examined no manifests", file=sys.stderr)
        return 1
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
