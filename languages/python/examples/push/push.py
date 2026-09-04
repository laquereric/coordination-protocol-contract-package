"""CPCP push example: write access. Stdlib only.

Adapted from the pod's Python harness (operationId-first PUSH). A PUSH
names its intent before performing it: asking twice with the same name
must not perform it twice. This example WRITES to the backend -- point
CPCP_URL at your own pod.

Usage:
    CPCP_URL=http://localhost:13002/_cpcp python3 push.py [method] [params-json] [operation-id]
    Defaults: note.create {"title": "hello from cpcp", "body": "posted by the CPCP push example"} with a random operationId.
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
import uuid

BASE = "http://localhost:13002/_cpcp"


def push(base_url, method, params=None, operation_id=None):
    """Returns (status, envelope dict). Never raises."""
    if params is None:
        params = {}
    if not isinstance(params, dict):
        return 0, {"ok": False, "reason": "client_params_not_object",
                   "because": "params must be an object; the server would refuse it"}
    op = operation_id or ("example-" + uuid.uuid4().hex[:16])
    body = {"jsonrpc": "2.0", "id": 1, "method": method,
            "params": params or {}, "operationId": op}
    req = urllib.request.Request(
        base_url.rstrip("/") + "/rpc",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            return res.status, json.loads(res.read().decode() or "{}")
    except urllib.error.HTTPError as err:
        return err.code, json.loads(err.read().decode() or "{}")
    except Exception as exc:  # noqa: BLE001
        return 0, {"ok": False, "reason": "unreachable",
                   "because": "%s: %s" % (exc.__class__.__name__, exc)}


def main(argv):
    import os

    base = os.environ.get("CPCP_URL", BASE)
    method = argv[1] if len(argv) > 1 else "note.create"
    try:
        params = json.loads(argv[2]) if len(argv) > 2 else {"title": "hello from cpcp", "body": "posted by the CPCP push example"}
    except ValueError:
        print("params must be JSON", file=sys.stderr)
        return 2
    op = argv[3] if len(argv) > 3 else None
    status, env = push(base, method, params, op)
    print(json.dumps({"status": status, "envelope": env}, indent=2))
    return 0 if env.get("ok") is True else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
