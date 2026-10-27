// The case agent: built on AG Studio's agent framework, it turns one held or blocked call into a case
// file for the "Why held, why blocked" widget (./case-file.tsx).
//
// Its turns are produced by rules, not an LLM (clientToolRunner: Studio runs the loop and executes the
// tools, we decide each round's tool calls). What keeps it safe is the tool list, which would hold for
// an LLM-driven agent as well:
//   - it can read only the store's own records through Studio's data engine: the call, the checks that
//     fired, the refunds already on the order. No tool returns the customer's e-mail text or the
//     Reader's free-text note, so nothing a customer writes can instruct it;
//   - it has no tool that approves, rejects or moves money. Approval stays with the merchant, on the
//     live demo's approval screen, where the gate re-checks the call.

import {
  clientToolRunner,
  createAiHarness,
  type AgAiEvent,
  type AgAiHarness,
  type AgAiParamsBuilder,
  type AgAiRunInput,
  type AgAiTool,
  type AgAiToolContext,
  type AgApiQuery,
  type AgStudioApi,
} from 'ag-studio';

export type CaseLine = { rmaId: string | null; amount: number | null; status: string; source: string; sameRma: boolean };
export type CaseCheck = { code: string; check: string; severity: string };

export type CaseFile = {
  callId: string;
  tool: string;
  decision: string;
  customer: string | null;
  paymentMethod: string | null;
  orderNo: string | null;
  rmaId: string | null;
  model: string;
  scenarioId: string;
  condition: string;
  allows: number | null;
  handedOff: number | null;
  asked: number | null;
  approved: number | null;
  checks: CaseCheck[];
  details: string[];
  ledger: CaseLine[];
  headline: string;
  explanation: string;
  trace: { tool: string; ok: boolean }[];
};

export type CaseState = { status: 'working' } | { status: 'done'; file: CaseFile } | { status: 'failed'; error: string };

// --- the store the widget reads, one entry per call -------------------------------------------------

const cases = new Map<string, CaseState>();
const listeners = new Set<() => void>();
const publish = (callId: string, state: CaseState) => {
  cases.set(callId, state);
  listeners.forEach((l) => l());
};
export const caseStore = {
  get: (callId: string) => cases.get(callId),
  subscribe: (l: () => void) => {
    listeners.add(l);
    return () => void listeners.delete(l);
  },
};

let harness: AgAiHarness | null = null;
const waiting = new Set<string>(); // asked for before the harness existed

/** Ask the case agent for a call's case file. Runs once per call; later asks read the store. */
export async function requestCase(callId: string) {
  if (!harness) return void waiting.add(callId);
  if (cases.has(callId)) return;
  publish(callId, { status: 'working' });
  try {
    const session = await harness.createThread({ agentId: AGENT_ID, title: `Case ${callId}` });
    session.sendMessage(JSON.stringify({ callId }));
  } catch (e) {
    publish(callId, { status: 'failed', error: String(e) });
  }
}

// --- tools: read-only, allowlisted fields --------------------------------------------------------

const money = (v: unknown) => (v === null || v === undefined || v === '' ? null : Number(v));
const text = (v: unknown) => (v === null || v === undefined ? null : String(v));

// Every read goes through Studio's own execute_query tool, with a query fixed here: the agent picks the
// call, never the fields. Studio joins calls to orders, returns and runs through the data relations.
type Query = (fields: string[], where: [string, string], ctx: AgAiToolContext) => Promise<Record<string, unknown>[]>;

function projector(api: AgStudioApi): Query {
  const executeQuery = api.getAiTools().executeQuery();
  return async (fields, where, ctx) => {
    const query: AgApiQuery = {
      kind: 'apiQuery',
      variant: 'projection',
      projection: fields.map((id) => ({ field: { id }, as: id.replace('.', '_') })),
      filter: { field: { id: where[0] }, operator: 'equals', value: where[1] },
    };
    const result = await executeQuery.execute!({ toolCallId: `query-${where[1]}`, name: executeQuery.name, args: { query } }, ctx);
    if (!result.success) throw new Error(result.issues.map((i) => i.message).join('; '));
    const rows = (result.data as { result?: Record<string, unknown>[] } | undefined)?.result ?? [];
    return rows.map((r) => Object.fromEntries(fields.map((f) => [f, r[f.replace('.', '_')]])));
  };
}

const CALL_FIELDS = [
  'calls.id', 'calls.runId', 'calls.tool', 'calls.decision', 'calls.orderNo',
  'calls.rmaId', 'calls.amount', 'calls.readerAmount', 'calls.storeAllows', 'calls.detail',
];

const byCall = (s: AgAiParamsBuilder) => s.object({ callId: s.string() });

function caseTools(api: AgStudioApi): AgAiTool[] {
  const project = projector(api);
  return [
    api.defineAiTool({
      name: 'read_held_call',
      description: 'The held or blocked call: amounts, order, RMA, customer and payment method from the store record.',
      params: byCall,
      async execute({ callId }: { callId: string }, ctx) {
        const [row] = await project(CALL_FIELDS, ['calls.id', callId], ctx);
        if (!row) return ctx.error(`no call ${callId}`);
        if (row['calls.decision'] === 'PASS') return ctx.error('this call passed the gate; only held or blocked calls get a case file');
        // Missing order/RMA references are themselves reasons to hold a call.
        // Joining all sources in one projection silently drops those cases.
        const [runs, orders, returns] = await Promise.all([
          project(['runs.model', 'runs.scenarioId', 'runs.condition'], ['runs.id', String(row['calls.runId'])], ctx),
          row['calls.orderNo'] ? project(['orders.customerEmail', 'orders.paymentMethod'], ['orders.orderNo', String(row['calls.orderNo'])], ctx) : Promise.resolve([]),
          row['calls.rmaId'] ? project(['returns.approvedAmount'], ['returns.rmaId', String(row['calls.rmaId'])], ctx) : Promise.resolve([]),
        ]);
        const record = { ...row, ...runs[0], ...orders[0], ...returns[0] };
        return ctx.success(JSON.stringify(record), record);
      },
    }),
    api.defineAiTool({
      name: 'read_checks',
      description: 'The gate checks that fired on the call.',
      params: byCall,
      async execute({ callId }: { callId: string }, ctx) {
        const rows = await project(['findings.code', 'findings.check', 'findings.severity'], ['findings.callId', callId], ctx);
        return ctx.success(JSON.stringify(rows), rows);
      },
    }),
    api.defineAiTool({
      name: 'read_refund_ledger',
      description: 'Refunds and reservations already on the order when the call was held or blocked.',
      params: byCall,
      async execute({ callId }: { callId: string }, ctx) {
        const rows = await project(
          ['ledger.id', 'ledger.rmaId', 'ledger.amount', 'ledger.status', 'ledger.source', 'ledger.sameRma'],
          ['ledger.callId', callId],
          ctx,
        );
        rows.sort((a, b) => String(a['ledger.id']).localeCompare(String(b['ledger.id'])));
        return ctx.success(JSON.stringify(rows), rows);
      },
    }),
    api.defineAiTool({
      name: 'place_case_file',
      description: 'Show the case file in the "Why held, why blocked" widget. Display only: it cannot approve or reject.',
      params: (s: AgAiParamsBuilder) => s.object({ callId: s.string(), file: s.string() }),
      execute({ callId, file }: { callId: string; file: string }, ctx) {
        publish(callId, { status: 'done', file: JSON.parse(file) as CaseFile });
        return ctx.success('placed');
      },
    }),
  ];
}

// --- the rules that write the case -------------------------------------------------------------------

const usd = (v: number | null) => (v === null ? '—' : `$${v.toFixed(2)}`);

function compose(callId: string, call: Record<string, unknown>, checks: Record<string, unknown>[], ledger: Record<string, unknown>[]) {
  const file: CaseFile = {
    callId,
    tool: String(call['calls.tool']),
    decision: String(call['calls.decision']),
    customer: text(call['orders.customerEmail']),
    paymentMethod: text(call['orders.paymentMethod']),
    orderNo: text(call['calls.orderNo']),
    rmaId: text(call['calls.rmaId']),
    model: String(call['runs.model']),
    scenarioId: String(call['runs.scenarioId']),
    condition: String(call['runs.condition']),
    allows: money(call['calls.storeAllows']),
    handedOff: money(call['calls.readerAmount']),
    asked: money(call['calls.amount']),
    approved: money(call['returns.approvedAmount']),
    checks: checks.map((c) => ({ code: String(c['findings.code']), check: String(c['findings.check']), severity: String(c['findings.severity']) })),
    details: String(call['calls.detail'] ?? '').split('; ').filter(Boolean),
    ledger: ledger.map((l) => ({
      rmaId: text(l['ledger.rmaId']),
      amount: money(l['ledger.amount']),
      status: String(l['ledger.status']),
      source: String(l['ledger.source']),
      sameRma: Number(l['ledger.sameRma']) === 1,
    })),
    headline: '',
    explanation: '',
    trace: [],
  };
  const codes = new Set(file.checks.map((c) => c.code));
  const { allows, asked, approved, rmaId } = file;
  const spent = approved !== null && allows !== null ? approved - allows : null;
  const over = allows !== null && asked !== null ? asked - allows : null;

  if (codes.has('RMA_ALREADY_REFUNDED')) {
    file.headline = `${rmaId} is already refunded`;
    file.explanation = `The return was approved for ${usd(approved)} and ${usd(spent)} has gone out against it. Paying ${usd(asked)} again would refund the same return twice.`;
  } else if (codes.has('CUMULATIVE_REFUND_EXCEEDS_RMA')) {
    file.headline = `${usd(asked)} asked, ${usd(allows)} left on ${rmaId}`;
    file.explanation = `${rmaId} approves ${usd(approved)}. ${usd(spent)} is already refunded or reserved by another session, so ${usd(allows)} is left. This call asks for ${usd(over)} more than that.`;
  } else if (codes.has('AUTO_REFUND_LIMIT_EXCEEDED') || codes.has('OVER_CAP')) {
    file.headline = `${usd(asked)} needs a person to sign it off`;
    file.explanation =
      over !== null && over <= 0
        ? `The amount matches the store record (${usd(allows)} left on ${rmaId}), but it is above the automatic limit, so it waits for the merchant.`
        : `The amount is above the automatic limit, so it waits for the merchant.`;
  } else if (file.tool === 'charge') {
    file.headline = `${usd(asked)} charge, ${usd(allows)} on record`;
    file.explanation = `The store has no quantity on record for a re-order, so every charge waits for the merchant. The catalog price of the items the Reader handed off comes to ${usd(allows)}; the agent asked for ${usd(asked)}.`;
  } else {
    file.headline = file.decision === 'BLOCK' ? 'Blocked by the gate' : 'Held for the merchant';
    file.explanation = file.details.join('. ');
  }
  return file;
}

// --- the agent ----------------------------------------------------------------------------------------

const AGENT_ID = 'case-agent';
const READS = ['read_held_call', 'read_checks', 'read_refund_ledger'] as const;

type Thread = { callId: string; names: Map<string, string>; results: Map<string, unknown>; trace: { tool: string; ok: boolean }[]; n: number };
const threads = new Map<string, Thread>();

function* callTool(t: Thread, name: string, args: object): Generator<AgAiEvent> {
  const toolCallId = `${AGENT_ID}-${t.n++}`;
  t.names.set(toolCallId, name);
  yield { type: 'TOOL_CALL_START', toolCallId, toolCallName: name };
  yield { type: 'TOOL_CALL_ARGS', toolCallId, delta: JSON.stringify(args) };
  yield { type: 'TOOL_CALL_END', toolCallId };
}

function* say(t: Thread, words: string): Generator<AgAiEvent> {
  const messageId = `${AGENT_ID}-msg-${t.n++}`;
  yield { type: 'TEXT_MESSAGE_START', messageId, role: 'assistant' };
  yield { type: 'TEXT_MESSAGE_CONTENT', messageId, delta: words };
  yield { type: 'TEXT_MESSAGE_END', messageId };
}

// One round: read the new messages (the request, or the results of the last round's tools), then call
// the next tools or finish. Round 1 reads the three record sources at once; round 2 places the case.
async function* round(input: AgAiRunInput): AsyncGenerator<AgAiEvent> {
  let t = threads.get(input.threadId);
  for (const m of input.messages) {
    if (m.role === 'user' && !t) {
      const { callId } = JSON.parse(m.content) as { callId: string };
      t = { callId, names: new Map(), results: new Map(), trace: [], n: 0 };
      threads.set(input.threadId, t);
    } else if (m.role === 'tool' && t) {
      const name = t.names.get(m.toolCallId) ?? '?';
      // the tool message carries the tool's whole result: { success, response, data }
      let result: { success?: boolean; data?: unknown; issues?: {message:string}[] } = {};
      try {
        result = JSON.parse(m.content);
      } catch {
        result = {};
      }
      const ok = !m.error && result.success === true;
      const value = result.data ?? null;
      if (!ok) {
        publish(t.callId, {status:'failed', error: `${name}: ${result.issues?.map(issue=>issue.message).join('; ') || m.content}`});
        return;
      }
      t.trace.push({ tool: name, ok });
      if (ok) t.results.set(name, value);
    }
  }
  if (!t) return yield* say({ n: 0 } as Thread, 'Send {"callId": "..."} to build a case file.');

  if (t.results.has('place_case_file')) return yield* say(t, 'Case file placed. Approving or rejecting is up to the merchant.');
  if (t.trace.some((s) => !s.ok)) {
    publish(t.callId, { status: 'failed', error: `${t.trace.find((s) => !s.ok)?.tool} failed` });
    return yield* say(t, 'Could not read the store record for this call.');
  }
  if (!READS.every((r) => t.results.has(r))) {
    for (const r of READS) yield* callTool(t, r, { callId: t.callId });
    return;
  }
  let file: CaseFile;
  try {
    file = compose(
      t.callId,
      t.results.get('read_held_call') as Record<string, unknown>,
      (t.results.get('read_checks') as Record<string, unknown>[]) ?? [],
      (t.results.get('read_refund_ledger') as Record<string, unknown>[]) ?? [],
    );
  } catch (e) {
    publish(t.callId, { status: 'failed', error: String(e) });
    return yield* say(t, 'Could not compose the case file.');
  }
  file.trace = [...t.trace, { tool: 'place_case_file', ok: true }];
  yield* callTool(t, 'place_case_file', { callId: t.callId, file: JSON.stringify(file) });
}

let harnessApi: AgStudioApi | null = null;

/** The case agent's harness for this Studio instance; built once per instance. */
export function buildCaseHarness(api: AgStudioApi): AgAiHarness {
  if (harness && harnessApi === api) return harness;
  harnessApi = api;
  cases.clear();
  const tools = caseTools(api);
  harness = createAiHarness(api, () => ({
    agents: [
      clientToolRunner({
        id: AGENT_ID,
        name: 'Case agent',
        description: 'Builds a case file for a call the gate held or blocked, from the store record only.',
        tools: () => tools,
        maxTurns: 4,
        run: (input) => round(input),
      }),
    ],
    primary: AGENT_ID,
  }));
  waiting.forEach((id) => requestCase(id));
  waiting.clear();
  return harness;
}
