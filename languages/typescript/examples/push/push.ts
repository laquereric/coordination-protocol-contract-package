// CPCP push example: write access. TypeScript with erasable syntax only,
// so plain `node` runs it with no build step.
//
// A PUSH names its intent before performing it. This example WRITES to the
// backend -- point CPCP_URL at your own pod.
//
// Usage:
//   CPCP_URL=http://localhost:13002/_cpcp node push.ts [method] [params-json] [operation-id]
import { randomBytes } from 'node:crypto';

interface Envelope {
  ok?: boolean;
  reason?: string;
  [key: string]: unknown;
}

interface Outcome {
  status: number;
  envelope: Envelope;
}

const BASE: string = process.env.CPCP_URL || 'http://localhost:13002/_cpcp';

async function push(
  baseUrl: string,
  method: string,
  params: Record<string, unknown> = {},
  operationId: string | null = null,
): Promise<Outcome> {
  const op: string = operationId || `example-${randomBytes(8).toString('hex')}`;
  const body = { jsonrpc: '2.0', id: 1, method, params, operationId: op };
  try {
    const res: Response = await fetch(`${baseUrl.replace(/\/$/, '')}/rpc`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(body),
    });
    const text: string = await res.text();
    let envelope: Envelope;
    try { envelope = JSON.parse(text || '{}'); }
    catch { envelope = { ok: false, reason: 'cpcp_unparseable', because: 'no JSON body' }; }
    return { status: res.status, envelope };
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return { status: 0, envelope: { ok: false, reason: 'unreachable', because: message } };
  }
}

const method: string = process.argv[2] || 'note.create';
let params: Record<string, unknown> = { title: 'hello from cpcp', body: 'posted by the CPCP push example' };
try { if (process.argv[3]) params = JSON.parse(process.argv[3]); }
catch { console.error('params must be JSON'); process.exit(2); }
const { status, envelope }: Outcome = await push(BASE, method, params, process.argv[4] || null);
console.log(JSON.stringify({ status, envelope }, null, 2));
process.exit(envelope.ok === true ? 0 : 1);
