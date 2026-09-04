#!/usr/bin/env python3
"""Fail if either demo CID's embedded shape diverges from the canonical file.

Audit F4: the CIDs stay self-contained (standalone portability), and this
check -- run by run-demo.sh -- fails loudly on silent drift instead.
Usage:  python3 demo/check-shapes.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CANONICAL = HERE / "shapes" / "note-shape.ttl"


def normalized(text):
    """Compare shape graphs, not comment bytes: drop full-line comments."""
    out = [line.rstrip() for line in text.splitlines()
           if line.strip() and not line.strip().startswith("#")]
    return "\n".join(out).strip() + "\n"


def main():
    canonical = normalized((HERE / "shapes" / "note-shape.ttl").read_text(encoding="utf-8"))
    digest = hashlib.sha256(canonical.encode()).hexdigest()
    ok = True
    for name in ("pull-note.cid.json", "push-note.cid.json"):
        cid = json.loads((HERE / name).read_text(encoding="utf-8"))
        embedded = normalized(cid.get("shapes") or "")
        match = embedded == canonical
        print("%s shapes-identical=%s sha256=%s" % (name, match, digest[:16]))
        ok = ok and match
    record = {"canonical": "demo/shapes/note-shape.ttl", "version": 1, "sha256": digest}
    (HERE / "SHAPES.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print("wrote demo/SHAPES.json")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
