#!/usr/bin/env python3
"""Plants for check-repo-format: every rule must FAIL when broken.

A checker nobody has watched fail is a guess about what it would do. Each plant
below is a violation the format forbids, built in a temporary repo so nothing
real is touched, and each must be refused.

Usage:  python3 tooling/plant-repo-format.py
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CHECKER = os.path.join(HERE, "check-repo-format.py")

VALID_INDEX = {
    "kind": "cpcp-demo",
    "version": 1,
    "name": "planted",
    "description": "a package repo built to be broken on purpose",
    "contract": {
        "repo": "https://github.com/laquereric/coordination-protocol-contract-package",
        "rev": "3b9ce9b3b4e788b961e4332bfbe0949ec2d31c2e",
    },
    "scopes": {"manifests": {"services": ".cpcp/services/package.json"}},
}

VALID_SCOPE = {
    "kind": "cpcp-scope",
    "scope": "services",
    "of": "planted",
    "definition": "served to callers beyond this pod",
    "source": "spec/scopes.md",
    "seams": [{"id": "stub", "methods": ["note.list"]}],
    "exposure": {"measured": True, "evidence": "seam/server.py:1 -- binds loopback"},
}

# The outbound scope: this repo CALLS these, and something else serves them.
DEPENDENCY_INDEX = dict(
    VALID_INDEX,
    scopes={"manifests": {"dependency": ".cpcp/dependency/package.json"}},
)

VALID_DEPENDENCY = {
    "kind": "cpcp-scope",
    "scope": "dependency",
    "of": "planted",
    "definition": "CIDs this repo calls, served elsewhere",
    "source": "spec/scopes.md",
    "depends_on": [{
        "producer": "https://example.test/_cpcp",
        "cid": "https://example.test/_cpcp/cid.json",
        "operations": ["note.list"],
        "status": "published",
    }],
}


FOUR_DEFS = {"dependency": {"summary": "d"},
             "pod_internal_dependencies": {"summary": "pd"},
             "pod_internal_services": {"summary": "ps"},
             "services": {"summary": "s"}}


def build(index=VALID_INDEX, scope=VALID_SCOPE, scope_dir="services", files=()):
    d = tempfile.mkdtemp(prefix="plant-repo-format-")
    os.makedirs(os.path.join(d, ".cpcp"), exist_ok=True)
    with open(os.path.join(d, ".cpcp/package.json"), "w", encoding="utf-8") as fh:
        json.dump(index, fh, indent=2)
    if scope is not None:
        os.makedirs(os.path.join(d, ".cpcp", scope_dir), exist_ok=True)
        with open(os.path.join(d, ".cpcp", scope_dir, "package.json"), "w",
                  encoding="utf-8") as fh:
            json.dump(scope, fh, indent=2)
    for rel in files:
        full = os.path.join(d, rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        open(full, "w").close()
    return d


def run(repo):
    out = subprocess.run([sys.executable, CHECKER, repo],
                         capture_output=True, text=True)
    return out.returncode, out.stdout + out.stderr


def edit(doc, path, value):
    """Return a copy with a dotted path set, or the key removed when value is None."""
    doc = json.loads(json.dumps(doc))
    keys = path.split(".")
    cur = doc
    for k in keys[:-1]:
        cur = cur[k]
    if value is None:
        cur.pop(keys[-1], None)
    else:
        cur[keys[-1]] = value
    return doc


CASES = [
    # (name, repo builder, substring the refusal must contain)
    ("clean", lambda: build(), None),

    ("no-cpcp-dir", lambda: tempfile.mkdtemp(prefix="plant-empty-"), "missing"),

    ("bad-kind", lambda: build(index=edit(VALID_INDEX, "kind", "cpcp-thing")),
     "kind must be one of"),

    ("wrong-version", lambda: build(index=edit(VALID_INDEX, "version", 2)),
     "version must be 1"),

    ("no-contract", lambda: build(index=edit(VALID_INDEX, "contract", None)),
     "missing contract"),

    # Rule 5. An abbreviation is not an object a reader can verify.
    ("abbreviated-sha", lambda: build(index=edit(VALID_INDEX, "contract.rev", "3b9ce9b")),
     "abbreviated SHA"),

    # A scope directory nobody declared: a claim nobody made.
    ("undeclared-scope-dir",
     lambda: build(index=edit(VALID_INDEX, "scopes.manifests", {})),
     "does not list it"),

    # And the mirror: declared with no directory behind it.
    ("declared-scope-missing",
     lambda: build(index=edit(VALID_INDEX, "scopes.manifests",
                              {"pod_internal_services": ".cpcp/pod_internal_services/package.json"})),
     "not a file"),

    ("scope-name-not-a-scope",
     lambda: build(index=edit(VALID_INDEX, "scopes.manifests",
                              {"private_cpcp": ".cpcp/private_cpcp/package.json"}),
                   scope=edit(VALID_SCOPE, "scope", "private_cpcp"),
                   scope_dir="private_cpcp"),
     "is not a scope"),

    # The folder and the manifest must agree about which scope this is.
    ("scope-disagrees-with-directory",
     lambda: build(scope=edit(VALID_SCOPE, "scope", "pod_internal_services")),
     "must be the same"),

    ("scope-kind-wrong",
     lambda: build(scope=edit(VALID_SCOPE, "kind", "cpcp-demo")),
     "kind must be 'cpcp-scope'"),

    ("scope-missing-definition",
     lambda: build(scope=edit(VALID_SCOPE, "definition", None)), "missing definition"),

    # Rule 2. An omitted scope cannot be told apart from an overlooked one.
    ("empty-seams-without-because",
     lambda: build(scope=edit(VALID_SCOPE, "seams", [])), "no 'because'"),

    # Rule 4. Exposure is measured; a citation is the difference.
    ("exposure-without-evidence",
     lambda: build(scope=edit(VALID_SCOPE, "exposure", {"measured": True})),
     "no 'evidence'"),

    # Rule 3. A seam with no scope belongs in the index WITH a because.
    ("unscoped-seam-without-because",
     lambda: build(index=edit(VALID_INDEX, "unscoped_seams", [{"id": "orphan"}])),
     "has no 'because'"),

    # A manifest naming a file the repo does not contain: the drift that happens
    # when files move and nobody updates the index.
    ("declared-path-missing",
     lambda: build(index=edit(VALID_INDEX, "cids", ["cid/pull-note.cid.json"])),
     "does not exist in this repo"),

    # Rule 7. A CID nobody can run is a claim, not an interface.
    ("cid-without-example",
     lambda: build(index=edit(VALID_INDEX, "cids",
                              [{"cid": "cid/pull-note.cid.json", "examples": []}]),
                   files=("cid/pull-note.cid.json",)),
     "declares no example caller"),

    ("cid-as-bare-string",
     lambda: build(index=edit(VALID_INDEX, "cids", ["cid/pull-note.cid.json"]),
                   files=("cid/pull-note.cid.json",)),
     "declares no example caller"),

    ("cid-example-missing",
     lambda: build(index=edit(VALID_INDEX, "cids",
                              [{"cid": "cid/pull-note.cid.json",
                                "examples": ["examples/python/pull.py"]}]),
                   files=("cid/pull-note.cid.json",)),
     "is not a file"),

    ("cid-file-missing",
     lambda: build(index=edit(VALID_INDEX, "cids",
                              [{"cid": "cid/gone.cid.json",
                                "examples": ["examples/python/pull.py"]}]),
                   files=("examples/python/pull.py",)),
     "is not a file"),

    # ---- Rule 8: a dependency names its producer and says whether it is built.

    # A valid dependency scope must PASS, or a repo that only calls could not
    # conform at all.
    ("dependency-clean",
     lambda: build(index=DEPENDENCY_INDEX, scope=VALID_DEPENDENCY,
                   scope_dir="dependency"),
     None),

    ("dependency-without-producer",
     lambda: build(index=DEPENDENCY_INDEX,
                   scope=edit(VALID_DEPENDENCY, "depends_on",
                              [{"operations": ["note.list"], "status": "published"}]),
                   scope_dir="dependency"),
     "no 'producer'"),

    ("dependency-without-operations",
     lambda: build(index=DEPENDENCY_INDEX,
                   scope=edit(VALID_DEPENDENCY, "depends_on",
                              [{"producer": "https://example.test/_cpcp",
                                "status": "published"}]),
                   scope_dir="dependency"),
     "no 'operations'"),

    ("dependency-with-unknown-status",
     lambda: build(index=DEPENDENCY_INDEX,
                   scope=edit(VALID_DEPENDENCY, "depends_on",
                              [{"producer": "https://example.test/_cpcp",
                                "operations": ["note.list"], "status": "someday"}]),
                   scope_dir="dependency"),
     "expected one of"),

    # An unbuilt dependency is the one most worth recording, and the reason it
    # is unbuilt is the whole content of the record.
    ("dependency-unbuilt-without-because",
     lambda: build(index=DEPENDENCY_INDEX,
                   scope=edit(VALID_DEPENDENCY, "depends_on",
                              [{"producer": "https://example.test/_cpcp",
                                "operations": ["contextframe.list"],
                                "status": "unbuilt"}]),
                   scope_dir="dependency"),
     "no 'because'"),

    ("empty-depends-on-without-because",
     lambda: build(index=DEPENDENCY_INDEX,
                   scope=edit(VALID_DEPENDENCY, "depends_on", []),
                   scope_dir="dependency"),
     "no 'because'"),

    # The two lists are not interchangeable in either direction.
    ("dependency-carrying-seams",
     lambda: build(index=DEPENDENCY_INDEX,
                   scope=dict(VALID_DEPENDENCY, seams=[{"id": "stub"}]),
                   scope_dir="dependency"),
     "not 'seams'"),

    ("serving-scope-carrying-depends-on",
     lambda: build(scope=dict(VALID_SCOPE,
                              depends_on=[{"producer": "x", "operations": ["y"],
                                           "status": "published"}])),
     "belongs in a calling scope"),

    # A dependency scope asserts nothing about the producer's exposure.
    ("dependency-carrying-exposure",
     lambda: build(index=DEPENDENCY_INDEX,
                   scope=dict(VALID_DEPENDENCY,
                              exposure={"measured": True, "evidence": "somewhere"}),
                   scope_dir="dependency"),
     "no 'exposure'"),

    # A path inside a repo+rev citation is that repo's path, not ours. Without
    # this, a manifest citing a doc in another repo is reported as broken for
    # citing it correctly.
    ("citation-path-not-checked-locally",
     lambda: build(index=dict(VALID_INDEX, role={
         "name": "FRONT",
         "defined_by": {"repo": "https://github.com/laquereric/magentic-stack",
                        "rev": "918227713fb1929dbd48836a0b47dc3390e7e9d9",
                        "doc": "docs/architecture/OVERVIEW.md"}})),
     None),

    # But a path OUTSIDE any citation still has to exist here, or the exemption
    # would be a hole big enough to drive the whole check through.
    ("local-path-still-checked",
     lambda: build(index=dict(VALID_INDEX, role={
         "name": "FRONT", "doc": "docs/architecture/OVERVIEW.md"})),
     "does not exist in this repo"),

    # ---- Rule 9: a declared role names one of the four.

    ("role-valid", lambda: build(index=dict(VALID_INDEX,
        role={"name": "BACK", "of": "example.test"})), None),

    # Declaring no role is fine: a library that neither serves nor calls has none.
    ("role-absent", lambda: build(), None),

    ("role-unknown-name", lambda: build(index=dict(VALID_INDEX,
        role={"name": "SWITCH", "of": "example.test"})), "expected one of"),

    ("role-not-an-object", lambda: build(index=dict(VALID_INDEX, role="BACK")),
     "must be an object"),

    ("role-also-reified-unknown", lambda: build(index=dict(VALID_INDEX,
        role={"name": "BACK", "also_reified": {"MIND": "x"}})), "which is not a role"),

    ("role-also-reified-duplicates-name", lambda: build(index=dict(VALID_INDEX,
        role={"name": "BACK", "also_reified": {"BACK": "x"}})), "repeats"),

    # The conformance claim: co-locating FRONT and BACK is not a conformant
    # deployment, so a repo carrying both must say it does not.
    ("role-front-and-back-unstated", lambda: build(index=dict(VALID_INDEX,
        role={"name": "BACK", "also_reified": {"FRONT": "x"}})),
     "separate_containers"),

    ("role-front-and-back-declared-separate", lambda: build(index=dict(VALID_INDEX,
        role={"name": "BACK", "also_reified": {"FRONT": "x"},
              "separate_containers": True})), None),

    # Only `true` counts. A truthy string is somebody hedging.
    ("role-separate-containers-not-true", lambda: build(index=dict(VALID_INDEX,
        role={"name": "BACK", "also_reified": {"FRONT": "x"},
              "separate_containers": "yes"})), "separate_containers"),

    # ---- The published vocabulary must be complete and must invent nothing.

    ("scope-definitions-complete",
     lambda: build(scope=dict(VALID_SCOPE, scope_definitions=FOUR_DEFS)),
     None),

    ("scope-definitions-incomplete",
     lambda: build(scope=dict(VALID_SCOPE, scope_definitions={
         k: v for k, v in FOUR_DEFS.items() if k != "pod_internal_services"})),
     "omits pod_internal_services"),

    ("scope-definitions-invented",
     lambda: build(scope=dict(VALID_SCOPE,
                              scope_definitions=dict(FOUR_DEFS, private={"summary": "?"}))),
     "which is not a scope"),

    ("pod-internal-dependency-clean",
     lambda: build(index=dict(VALID_INDEX, scopes={"manifests": {
                       "pod_internal_dependencies":
                           ".cpcp/pod_internal_dependencies/package.json"}}),
                   scope=dict(VALID_DEPENDENCY, scope="pod_internal_dependencies"),
                   scope_dir="pod_internal_dependencies"),
     None),

    ("pod-internal-dependency-carrying-seams",
     lambda: build(index=dict(VALID_INDEX, scopes={"manifests": {
                       "pod_internal_dependencies":
                           ".cpcp/pod_internal_dependencies/package.json"}}),
                   scope=dict(VALID_DEPENDENCY, scope="pod_internal_dependencies",
                              seams=[{"id": "stub"}]),
                   scope_dir="pod_internal_dependencies"),
     "not 'seams'"),

    # A seam entry repeats its own scope; only the manifest's was ever read,
    # so a stale copy could contradict the folder it sat in.
    ("seam-entry-scope-disagrees",
     lambda: build(scope=dict(VALID_SCOPE, seams=[
         {"id": "stub", "scope": "pod_internal_services"}])),
     "cannot name a scope other than the manifest"),

    ("seam-entry-scope-agrees",
     lambda: build(scope=dict(VALID_SCOPE, seams=[
         {"id": "stub", "scope": "services"}])),
     None),

    # ONE caller is the bar. This must PASS, or the standard would be demanding
    # a demonstration from every package.
    ("cid-with-one-example",
     lambda: build(index=edit(VALID_INDEX, "cids",
                              [{"cid": "cid/pull-note.cid.json",
                                "examples": ["examples/python/pull.py"]}]),
                   files=("cid/pull-note.cid.json", "examples/python/pull.py")),
     None),
]


def main():
    rows = []
    ok = True
    for name, builder, needle in CASES:
        repo = builder()
        try:
            rc, out = run(repo)
            if needle is None:
                passed, detail = rc == 0, "exit %d" % rc
            else:
                passed = rc != 0 and needle in out
                detail = "exit %d%s" % (rc, "" if passed else " (needle %r absent)" % needle)
            rows.append((name, passed, detail))
            ok = ok and passed
        finally:
            shutil.rmtree(repo, ignore_errors=True)

    for name, passed, detail in rows:
        print("  %-32s %-4s %s" % (name, "ok" if passed else "FAIL", detail))
    print("repo-format plants: %s (%d)" % ("OK" if ok else "FAIL", len(rows)))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
