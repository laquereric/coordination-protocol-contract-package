"""Demo CPCP seam: note.list + note.create over in-memory notes. Stdlib only.

Implements the PushNote/PullNote CIDs in this directory so every language
example runs standalone: no pod, no credentials, nothing to install.
State evaporates with the process -- this is a demo, not a store.

Endpoints:
  POST /_cpcp/rpc   note.list {} | note.create {title, body} + operationId
  GET  /_cpcp/cid.json   both CID documents
  GET  /up           liveness
"""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

NOTES = [{"id": 1, "title": "Welcome", "body": "seeded by the demo seam"}]
RECEIPTS = {}

CONTEXT = {
    "@vocab": "https://w3id.org/laquereric/cpcp/ns#",
    "id": "@id",
    "type": "@type",
    "operationId": "https://w3id.org/laquereric/json-rpc-ld/ns#operationId",
}


def fail(rid, reason, because, status=400):
    return status, {"ok": False, "reason": reason, "because": because,
                    "@context": CONTEXT, "jsonrpc": "2.0", "id": rid}


def ok(rid, result):
    return 200, {"ok": True, "result": result, "@context": CONTEXT,
                 "jsonrpc": "2.0", "id": rid}


def dispatch(body):
    rid = body.get("id")
    method = str(body.get("method") or "")
    params = body.get("params")
    if params is None:
        params = {}
    if not isinstance(params, dict):
        return fail(rid, "unparseable_json", {"offender": "params"})
    if method == "note.list":
        graph = [dict(n, **{"@id": "note:%d" % n["id"], "@type": "Note"}) for n in NOTES]
        return ok(rid, {"@graph": graph})
    if method == "note.create":
        title = params.get("title")
        content = params.get("body")
        op = body.get("operationId") or params.get("operationId") or ""
        if not isinstance(title, str) or not title.strip():
            return fail(rid, "missing_params", {"missing": "title"})
        if not isinstance(content, str) or not content.strip():
            return fail(rid, "missing_params", {"missing": "body"})
        if not op:
            return fail(rid, "operation_id_required", {"because": "PUSH names its intent first"})
        if op in RECEIPTS:
            row = RECEIPTS[op]
            return ok(rid, dict(row, **{"@id": "note:%d" % row["id"], "@type": "Note"}))
        row = {"id": len(NOTES) + 1, "title": title, "body": content}
        NOTES.append(row)
        RECEIPTS[op] = dict(row)
        return ok(rid, dict(row, **{"@id": "note:%d" % row["id"], "@type": "Note"}))
    return fail(rid, "unknown_operation", {"method": method})


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _send(self, status, payload):
        raw = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path in ("/up", "/_cpcp/up"):
            return self._send(200, {"ok": True})
        if self.path == "/_cpcp/cid.json":
            import os

            here = os.path.dirname(os.path.abspath(__file__))
            cids = []
            for name in ("pull-note.cid.json", "push-note.cid.json"):
                with open(os.path.join(here, name), encoding="utf-8") as fh:
                    cids.append(json.load(fh))
            return self._send(200, {"ok": True, "result": {"cids": cids},
                                    "jsonrpc": "2.0", "id": None})
        return self._send(404, {"ok": False, "reason": "not_found",
                                "because": {"path": self.path},
                                "jsonrpc": "2.0", "id": None})

    def do_POST(self):
        if self.path != "/_cpcp/rpc":
            return self._send(404, {"ok": False, "reason": "not_found",
                                    "because": {"path": self.path},
                                    "jsonrpc": "2.0", "id": None})
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        raw = self.rfile.read(length) if length > 0 else b""
        if not raw.strip():
            return self._send(*fail(None, "empty_body", {"offender": "body"}))
        try:
            body = json.loads(raw.decode())
        except (ValueError, UnicodeDecodeError):
            return self._send(*fail(None, "unparseable_json", {"offender": "body"}))
        if not isinstance(body, dict):
            return self._send(*fail(None, "unparseable_json", {"offender": "body"}))
        self._send(*dispatch(body))


if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", "18080"))
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
