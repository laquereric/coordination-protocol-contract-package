#!/usr/bin/env bash
# Executable PushNote/PullNote demo: stub seam plus the Python examples
# against it. No pod, no credentials, nothing to install.
set -euo pipefail
cd "$(dirname "$0")"

PORT="${PORT:-18080}"
python3 server.py &>/tmp/cpcp-demo.log &
SERVER_PID=$!
trap 'kill $SERVER_PID 2>/dev/null' EXIT

for i in $(seq 1 30); do
  curl -sf "http://127.0.0.1:${PORT}/up" >/dev/null 2>&1 && break
  sleep 0.2
done

export CPCP_URL="http://127.0.0.1:${PORT}/_cpcp"
echo "== pull: seed visible =="
python3 ../languages/python/examples/pull/pull.py
echo "== push: intent named =="
python3 ../languages/python/examples/push/push.py note.create \
  '{"title":"demo note","body":"written through the demo seam"}' demo-op-1
echo "== push again, same operationId: first receipt, no second write =="
python3 ../languages/python/examples/push/push.py note.create \
  '{"title":"demo note","body":"written through the demo seam"}' demo-op-1
echo "== pull: two notes =="
python3 ../languages/python/examples/pull/pull.py
echo "== demo OK =="
