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

KINDS = ("cpcp-contract", "cpcp-registry", "cpcp-demo", "cpcp-application")
SCOPES = ("public_cpcp", "pod_internal_cpcp", "pod_external_cpcp")
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


def check_paths(doc, where, repo, rep):
    """Declared paths resolve.

    Not one of the six rules, and the reason it is here: a manifest is a claim
    about a repo, and a claim naming a file that does not exist is how the
    manifest and the tree drift apart silently -- exactly what happens when
    files move and nobody updates the index.
    """
    for path, value in walk_strings(doc):
        key = path.rsplit(".", 1)[-1].split("[")[0]
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

    seams = doc.get("seams")
    if not isinstance(seams, list):
        rep.fail(rel, "seams must be a list (it may be empty)")
    elif not seams and not str(doc.get("because", "")).strip():
        # Rule 2: an omitted scope cannot be told apart from an overlooked one,
        # so an empty one has to say what serves that scope instead.
        rep.fail(rel, "seams is empty and there is no 'because' naming what serves "
                      "this scope instead (rule 2)")

    exposure = doc.get("exposure")
    if isinstance(exposure, dict) and not str(exposure.get("evidence", "")).strip():
        # Rule 4: read it from the deployment files and record which file.
        rep.fail(rel, "exposure has no 'evidence'; rule 4 says exposure is measured, "
                      "and a restatement of the method-to-scope map is not evidence")

    check_shas(doc, rel, rep)
    check_paths(doc, rel, repo, rep)

    if isinstance(seams, list) and seams:
        ids = [s.get("id") for s in seams if isinstance(s, dict)]
        rep.note("%s serves seams: %s" % (scope_dir, ", ".join(str(i) for i in ids)))
    return doc


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
