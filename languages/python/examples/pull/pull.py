"""CPCP pull example: read access. Stdlib only.

Adapted from the pod's Python harness (urllib + envelopes). Reads a
method result without changing anything.

Usage:
    CPCP_URL=http://localhost:13002/_cpcp python3 pull.py [method] [params-json]

A non-200 status still carries the envelope: read the error body, never
raise on it (a `with urlopen` block that ignores HTTPError loses the
far side's reason).
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

BASE = "http://localhost:13002/_cpcp"


def pull(base_url, method, params=None):
    """Returns (status, envelope dict). Never raises."""
    if params is None:
        params = {}
    if not isinstance(params, dict):
        return 0, {"ok": False, "reason": "client_params_not_object",
                   "because": "params must be an object; the server would refuse it"}
    body = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
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
        # A 4xx/5xx IS the answer on this seam. URLError without a code is
        # infrastructure -- never collapse the two.
        return err.code, json.loads(err.read().decode() or "{}")
    except Exception as exc:  # noqa: BLE001
        return 0, {"ok": False, "reason": "unreachable",
                   "because": "%s: %s" % (exc.__class__.__name__, exc)}


def main(argv):
    import os

    base = os.environ.get("CPCP_URL", BASE)
    method = argv[1] if len(argv) > 1 else "note.list"
    try:
        params = json.loads(argv[2]) if len(argv) > 2 else {}
    except ValueError:
        print("params must be JSON", file=sys.stderr)
        return 2
    status, env = pull(base, method, params)
    print(json.dumps({"status": status, "envelope": env}, indent=2))
    return 0 if env.get("ok") is True else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
