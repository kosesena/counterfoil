// AG Studio data sources over the tables scripts/export_dashboard.py writes: one row per evaluation
// run, one per tool call the transaction agent made, plus the scenarios and the store's own records.

import type { AgDataSourcesDefinition, AgFieldDefinition, AgFormat, AgRelationDefinition } from 'ag-studio';

export type CounterfoilData = {
  asOf: string;
  runs: Record<string, unknown>[];
  calls: Record<string, unknown>[];
  scenarios: Record<string, unknown>[];
  orders: Record<string, unknown>[];
  returns: Record<string, unknown>[];
};

// [id, name, format, hide?]
type FieldSpec = [id: string, name: string, format: AgFormat, hide?: boolean];

// Every order is in US dollars, so amounts read $90.00 whatever the viewer's browser locale.
const USD = { format: new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }) };
const formatOptions = (format: AgFormat) => (format === 'currencyFormat' ? { formatOptions: USD } : {});

const fields = (specs: FieldSpec[]): AgFieldDefinition[] =>
  specs.map(([id, name, format, hide]) => ({ id, name, format, ...formatOptions(format), ...(hide && { hide }) }));

const manyToOne = (id: string, source: string, target: string): AgRelationDefinition => {
  const [sourceTable, sourceField] = source.split('.');
  const [targetTable, targetField] = target.split('.');
  return {
    id,
    source: { tableId: sourceTable, fieldId: sourceField },
    target: { tableId: targetTable, fieldId: targetField },
    type: 'many-to-one',
  };
};

const sumOf = (id: string) => ({ id, aggregation: 'sum' as const });

// Model ids as the result files name them, and the names people know them by.
const MODEL_NAMES: Record<string, string> = {
  'qwen2.5-8k': 'Qwen 2.5',
  'claude-haiku-4-5': 'Claude Haiku 4.5',
  'claude-sonnet-5': 'Claude Sonnet 5',
  'claude-opus-5-5': 'Claude Opus 5.5',
  'gpt-5-6-terra': 'GPT-5.6 Terra',
};

export const modelName = (id: unknown) => MODEL_NAMES[String(id)] ?? String(id);

// Charts list the conditions from weakest to strongest guard: 1 no gate, 2 the cap, 3 Counterfoil.
const GUARD_LEVEL = ['No gate', '$200 cap', 'Counterfoil'];

// A sum under its own name, so charts and grids say 'Agent misled', not 'Agent Misled (sum)'.
const total = (id: string, name: string, field: string, format: 'integerFormat' | 'currencyFormat' = 'integerFormat') => ({
  id,
  name,
  format,
  ...formatOptions(format),
  isMeasure: true,
  expression: sumOf(field),
});

const rate = (id: string, name: string, description: string, numerator: string, denominator: string) => ({
  id,
  name,
  description,
  format: 'percentageFormat' as const,
  isMeasure: true,
  expression: { operator: 'divide' as const, inputs: [sumOf(numerator), sumOf(denominator)] },
});

export function buildStudioData(data: CounterfoilData): AgDataSourcesDefinition {
  return {
    description:
      'Counterfoil evaluation: an AI transaction agent handles refund and charge e-mails for a small home-goods store ' +
      'and calls Braintree (mocked PayPal) through one of three conditions: no gate, a $200 per-transaction cap, or Counterfoil, ' +
      "which checks every call against the store's own records (return authorisations, order totals, ownership). " +
      'Attack e-mails carry hidden instructions. Harm means wrong money actually reached the payment rail.',
    sources: [
      {
        id: 'runs',
        name: 'Runs',
        description: 'One row per scenario × condition × repeat × model. Flags are 0/1; sum them to count runs.',
        data: data.runs.map((r) => ({
          ...r,
          model: modelName(r.model),
          guardLevel: GUARD_LEVEL.indexOf(String(r.condition)) + 1,
          // harm split by condition, so a grid can show the three conditions side by side without a pivot header
          harmNoGate: r.condition === 'No gate' ? r.harm : 0,
          harmCap: r.condition === '$200 cap' ? r.harm : 0,
          harmCounterfoil: r.condition === 'Counterfoil' ? r.harm : 0,
        })),
        fields: fields([
          ['id', 'Run ID', 'textFormat', true],
          ['source', 'Result File', 'textFormat', true],
          ['model', 'Model', 'textFormat'],
          ['scenarioId', 'Scenario', 'textFormat'],
          ['family', 'Attack Family', 'textFormat'],
          ['kind', 'Kind', 'textFormat'],
          ['condition', 'Condition', 'textFormat'],
          ['guardLevel', 'Guard Level', 'integerFormat', true],
          ['harmNoGate', 'Harm (No gate)', 'integerFormat', true],
          ['harmCap', 'Harm ($200 cap)', 'integerFormat', true],
          ['harmCounterfoil', 'Harm (Counterfoil)', 'integerFormat', true],
          ['repeat', 'Repeat', 'integerFormat'],
          ['attackRun', 'Attack Runs', 'integerFormat'],
          ['cleanRun', 'Clean Runs', 'integerFormat'],
          ['agentMisled', 'Agent Misled', 'integerFormat'],
          ['harm', 'Harm Reached Rail', 'integerFormat'],
          ['stoppedByGate', 'Stopped by Gate', 'integerFormat'],
          ['stoppedByRail', 'Stopped by Rail', 'integerFormat'],
          ['legitDone', 'Legit Request Done', 'integerFormat'],
          ['legitHeld', 'Legit Request Held', 'integerFormat'],
          ['cleanDone', 'Clean Request Handled Right', 'integerFormat'],
          ['refunded', 'Refunded', 'currencyFormat'],
          ['charged', 'Charged', 'currencyFormat'],
          ['correctAmount', 'Correct Amount', 'currencyFormat'],
          ['steps', 'Agent Steps', 'integerFormat'],
          ['agentSeconds', 'Agent Seconds', 'decimalFormat'],
        ]),
      },
      {
        id: 'calls',
        name: 'Agent Calls',
        description: "Every tool call the transaction agent made and the gate's decision on it (PASS, APPROVAL or BLOCK).",
        data: data.calls,
        fields: fields([
          ['id', 'Call ID', 'textFormat', true],
          ['runId', 'Run ID', 'textFormat', true],
          ['step', 'Step', 'integerFormat'],
          ['tool', 'Tool', 'textFormat'],
          ['moneyCall', 'Money Calls', 'integerFormat'],
          ['orderNo', 'Order', 'textFormat'],
          ['rmaId', 'Return Authorisation', 'textFormat'],
          ['amount', 'Requested Amount', 'currencyFormat'],
          ['decision', 'Decision', 'textFormat'],
          ['reasons', 'Reason Codes', 'textFormat'],
          ['detail', 'Reason Detail', 'textFormat'],
          ['railState', 'Rail Result', 'textFormat'],
          ['rail', 'Rail', 'textFormat'],
          ['braintreeTransaction', 'Braintree Sale', 'textFormat'],
          ['braintreeResult', 'Braintree Refund/Charge', 'textFormat'],
        ]),
      },
      {
        id: 'scenarios',
        name: 'Scenarios',
        description: "Attack and clean scenarios. 'Rail would block' / 'Cap would block' say whether Braintree's own rules or a $200 cap stop the attack.",
        data: data.scenarios,
        fields: fields([
          ['id', 'Scenario ID', 'textFormat', true],
          ['kind', 'Scenario Kind', 'textFormat'],
          ['family', 'Scenario Family', 'textFormat', true],
          ['technique', 'Technique', 'textFormat'],
          ['split', 'Split', 'textFormat'],
          ['attackerGoal', 'Attacker Goal', 'textFormat'],
          ['expectedDecision', 'Expected Decision', 'textFormat'],
          ['railWouldBlock', 'Rail Would Block', 'integerFormat'],
          ['capWouldBlock', 'Cap Would Block', 'integerFormat'],
        ]),
      },
      {
        id: 'orders',
        name: 'Orders',
        description: "The store's orders, each paid through Braintree.",
        data: data.orders,
        fields: fields([
          ['orderNo', 'Order No', 'textFormat'],
          ['customerId', 'Customer', 'textFormat'],
          ['total', 'Order Total', 'currencyFormat'],
          ['currency', 'Order Currency', 'textFormat'],
          ['braintreeTransactionId', 'Braintree Transaction', 'textFormat'],
        ]),
      },
      {
        id: 'returns',
        name: 'Return Authorisations',
        description: "The store's return authorisations (RMA): what may actually be refunded for each order.",
        data: data.returns,
        fields: fields([
          ['rmaId', 'RMA', 'textFormat'],
          ['orderNo', 'RMA Order', 'textFormat', true],
          ['approvedAmount', 'Approved Refund', 'currencyFormat'],
          ['status', 'RMA Status', 'textFormat'],
          ['items', 'Returned Items', 'textFormat'],
        ]),
      },
    ],
    relationships: [
      manyToOne('call-run', 'calls.runId', 'runs.id'),
      manyToOne('run-scenario', 'runs.scenarioId', 'scenarios.id'),
      manyToOne('call-order', 'calls.orderNo', 'orders.orderNo'),
      manyToOne('call-return', 'calls.rmaId', 'returns.rmaId'),
      manyToOne('return-order', 'returns.orderNo', 'orders.orderNo'),
    ],
    expressions: [
      total('misledRuns', 'Agent misled', 'runs.agentMisled'),
      total('harmRuns', 'Wrong money paid', 'runs.harm'),
      total('stoppedRuns', 'Stopped by gate', 'runs.stoppedByGate'),
      total('moneyCalls', 'Money calls', 'calls.moneyCall'),
      total('harmNoGate', 'No gate', 'runs.harmNoGate'),
      total('harmCap', '$200 cap', 'runs.harmCap'),
      total('harmCounterfoil', 'Counterfoil', 'runs.harmCounterfoil'),
      total('requested', 'Requested', 'calls.amount', 'currencyFormat'),
      total('approved', 'Store approved', 'returns.approvedAmount', 'currencyFormat'),
      {
        id: 'guardLevel',
        name: 'Guard level',
        format: 'integerFormat' as const,
        isMeasure: true,
        expression: { id: 'runs.guardLevel', aggregation: 'min' as const },
      },
      rate('harmRate', 'Harm Rate', 'Attack runs where wrong money reached the rail.', 'runs.harm', 'runs.attackRun'),
      rate('misledRate', 'Agent Misled Rate', 'Attack runs where the agent made the attacker’s call.', 'runs.agentMisled', 'runs.attackRun'),
      rate('legitRate', 'Clean Handled Right', 'Clean runs completed, or held for a human where store policy requires it.', 'runs.cleanDone', 'runs.cleanRun'),
    ],
  };
}
