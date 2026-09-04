// CPCP pull example: read access. Node fetch (mirrors the pod's switch UI
// client). Reads a method result without changing anything.
//
// Usage:
//   CPCP_URL=http://localhost:13002/_cpcp node pull.mjs [method] [params-json]
//
// A non-200 status still carries the envelope: read the body on every
// status. fetch only rejects on network failure, never on HTTP errors.
const BASE = process.env.CPCP_URL || 'http://localhost:13002/_cpcp';

async function pull(baseUrl, method, params = {}) {
  const body = { jsonrpc: '2.0', id: 1, method, params };
  try {
    const res = await fetch(`${baseUrl.replace(/\/$/, '')}/rpc`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(body),
    });
    const text = await res.text();
    let envelope;
    try { envelope = JSON.parse(text || '{}'); }
    catch { envelope = { ok: false, reason: 'cpcp_unparseable', because: 'no JSON body' }; }
    return { status: res.status, envelope };
  } catch (err) {
    return { status: 0, envelope: { ok: false, reason: 'unreachable', because: String((err && err.message) || err) } };
  }
}

const method = process.argv[2] || 'note.list';
let params = {};
try { params = process.argv[3] ? JSON.parse(process.argv[3]) : {}; }
catch { console.error('params must be JSON'); process.exit(2); }
const { status, envelope } = await pull(BASE, method, params);
console.log(JSON.stringify({ status, envelope }, null, 2));
process.exit(envelope.ok === true ? 0 : 1);
