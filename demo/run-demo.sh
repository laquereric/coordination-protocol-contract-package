#!/usr/bin/env bash
# Executable PushNote/PullNote demo: stub seam plus every language client.
# No pod, no credentials. Toolchains present run; missing ones SKIP loudly
# (a skip is reported, never silent, never a pass).
set -u
cd "$(dirname "$0")"

PORT="${PORT:-18080}"
PASS=0
FAIL=0
SKIPPED=""

have() { command -v "$1" >/dev/null 2>&1; }
run_case() { # name + command...
  local name="$1"; shift
  if "$@" >/tmp/cpcp-case.log 2>&1; then
    PASS=$((PASS + 1)); echo "PASS $name"
  else
    FAIL=$((FAIL + 1)); echo "FAIL $name"; tail -n 5 /tmp/cpcp-case.log
  fi
}
skip_case() { SKIPPED="$SKIPPED $1"; echo "SKIP $1 ($2)"; }

echo "== shapes: embedded match canonical =="
python3 check-shapes.py || exit 1

python3 server.py &>/tmp/cpcp-demo.log &
SERVER_PID=$!
trap 'kill $SERVER_PID 2>/dev/null' EXIT
for i in $(seq 1 30); do
  curl -sf "http://127.0.0.1:${PORT}/_cpcp/up" >/dev/null 2>&1 && break
  sleep 0.2
done

export CPCP_URL="http://127.0.0.1:${PORT}/_cpcp"
L=../languages

echo "== pull: seed visible (python reference) =="
run_case py-pull python3 $L/python/examples/pull/pull.py
echo "== push + replay: one write, first receipt twice =="
run_case py-push python3 $L/python/examples/push/push.py note.create \
  '{"title":"demo note","body":"written through the demo seam"}' demo-op-1
run_case py-replay python3 $L/python/examples/push/push.py note.create \
  '{"title":"demo note","body":"written through the demo seam"}' demo-op-1
echo "== pull: two notes =="
run_case py-pull-2 python3 $L/python/examples/pull/pull.py

if have node; then
  run_case js-pull node $L/javascript/examples/pull/pull.mjs
  run_case js-push node $L/javascript/examples/push/push.mjs
  run_case ts-pull node $L/typescript/examples/pull/pull.ts
  run_case ts-push node $L/typescript/examples/push/push.ts
else skip_case "js+ts" "no node"; fi

if have ruby; then
  run_case rb-pull ruby $L/ruby/examples/pull/pull.rb
  run_case rb-push ruby $L/ruby/examples/push/push.rb
else skip_case "ruby" "no ruby"; fi

if have go; then
  run_case go-pull env GO111MODULE=off go run $L/go/examples/pull/pull.go
  run_case go-push env GO111MODULE=off go run $L/go/examples/push/push.go
else skip_case "go" "no go"; fi

if have java; then
  run_case java-pull java $L/java/examples/pull/Pull.java
  run_case java-push java $L/java/examples/push/Push.java from-java
else skip_case "java" "no java"; fi

if have cc; then
  cc -O2 -o /tmp/cpcp-pull $L/c/examples/pull/pull.c \
    && cc -O2 -o /tmp/cpcp-push $L/c/examples/push/push.c \
    && run_case c-pull /tmp/cpcp-pull && run_case c-push /tmp/cpcp-push from-c \
    || { FAIL=$((FAIL + 1)); echo "FAIL c-build"; }
else skip_case "c" "no cc"; fi

if have c++; then
  c++ -O2 -std=c++17 -o /tmp/cpcp-ppull $L/cpp/examples/pull/pull.cpp \
    && c++ -O2 -std=c++17 -o /tmp/cpcp-ppush $L/cpp/examples/push/push.cpp \
    && run_case cpp-pull /tmp/cpcp-ppull && run_case cpp-push /tmp/cpcp-ppush from-cpp \
    || { FAIL=$((FAIL + 1)); echo "FAIL cpp-build"; }
else skip_case "cpp" "no c++"; fi

echo "== pass=$PASS fail=$FAIL skipped:$SKIPPED =="
[ "$FAIL" = 0 ]
