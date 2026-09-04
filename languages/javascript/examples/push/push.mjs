// CPCP push example: write access. Node fetch.
//
// A PUSH names its intent before performing it: asking twice with the same
// name must not perform it twice. This example WRITES to the backend --
// point CPCP_URL at your own pod.
//
// Usage:
//   CPCP_URL=http://localhost:13002/_cpcp node push.mjs [method] [params-json] [operation-id]
//   Defaults: note.create {"title": "hello from cpcp"} with a random operationId.
import { randomBytes } from 'node:crypto';

const BASE = process.env.CPCP_URL || 'http://localhost:13002/_cpcp';

async function push(baseUrl, method, params = {}, operationId = null) {
  const op = operationId || `example-${randomBytes(8).toString('hex')}`;
  const body = { jsonrpc: '2.0', id: 1, method, params, operationId: op };
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

const method = process.argv[2] || 'note.create';
let params = { title: 'hello from cpcp', body: 'posted by the CPCP push example' };
try { if (process.argv[3]) params = JSON.parse(process.argv[3]); }
catch { console.error('params must be JSON'); process.exit(2); }
const { status, envelope } = await push(BASE, method, params, process.argv[4] || null);
console.log(JSON.stringify({ status, envelope }, null, 2));
process.exit(envelope.ok === true ? 0 : 1);
