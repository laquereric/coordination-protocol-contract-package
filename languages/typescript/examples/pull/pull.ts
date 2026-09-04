// CPCP pull example: read access. TypeScript with erasable syntax only
// (interfaces + annotations), so plain `node` runs it with no build step.
// Same contract as the JavaScript twin: reads without changing anything.
//
// Usage:
//   CPCP_URL=http://localhost:13002/_cpcp node pull.ts [method] [params-json]
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

async function pull(baseUrl: string, method: string, params: Record<string, unknown> = {}): Promise<Outcome> {
  const body = { jsonrpc: '2.0', id: 1, method, params };
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

const method: string = process.argv[2] || 'note.list';
let params: Record<string, unknown> = {};
try { params = process.argv[3] ? JSON.parse(process.argv[3]) : {}; }
catch { console.error('params must be JSON'); process.exit(2); }
const { status, envelope }: Outcome = await pull(BASE, method, params);
console.log(JSON.stringify({ status, envelope }, null, 2));
process.exit(envelope.ok === true ? 0 : 1);
