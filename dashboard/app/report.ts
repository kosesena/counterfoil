// The report the dashboard opens with, as AG Studio report state. Field ids ('runs.harm') refer to
// the data sources in ./studio-data.ts; harmRate, misledRate and legitRate are its expressions.

import type { AgPageState, AgReportState, AgWidgetLayoutState } from 'ag-studio';

// Position on the canvas grid, in tracks: 24 columns wide.
const at = (xTrack: number, yTrack: number, xSpan: number, ySpan: number): AgWidgetLayoutState => ({
  xTrack,
  yTrack,
  xSpan,
  ySpan,
});
const title = (text: string) => ({ title: { enabled: true, text } });
const sum = (id: string) => ({ id, aggregation: 'sum' as const });

const typography = (fontSize: number, fontWeight: 'normal' | 'bold' = 'normal') => ({
  fontFamily: 'var(--cf-font)',
  fontSize,
  fontWeight,
  fontStyle: 'normal' as const,
});

const kpi = (text: string, value: { id: string; aggregation?: 'sum' }, caption = '') => ({
  type: 'value' as const,
  dataMapping: { value: [value] },
  format: {
    title: { enabled: true, text, typography: typography(13, 'bold') },
    caption: { enabled: !!caption, text: caption, typography: typography(12) },
    style: { typography: typography(30, 'bold') },
  },
});

const filter = (id: string, text: string) => ({
  type: 'button-filter' as const,
  dataMapping: { value: [{ id }] },
  format: title(text),
});

const overview: AgPageState = {
  id: 'overview',
  widgets: {
    condition: filter('runs.condition', 'Condition'),
    model: filter('runs.model', 'Model'),
    'kpi-attacks': kpi('Attack runs', sum('runs.attackRun'), 'hidden-instruction e-mails'),
    'kpi-misled': kpi('Agent misled', { id: 'misledRate' }, 'made the attacker’s call'),
    'kpi-harm': kpi('Wrong money reached Braintree', { id: 'harmRate' }, 'of attack runs'),
    'kpi-legit': kpi('Genuine requests handled right', { id: 'legitRate' }, 'clean e-mails'),
    'harm-by-condition': {
      type: 'bar-chart-grouped',
      dataMapping: {
        categoryKey: [{ id: 'runs.condition' }],
        valueKey: [sum('runs.agentMisled'), sum('runs.harm'), sum('runs.stoppedByGate')],
      },
      format: {
        ...title('Attack runs: agent misled, harm reached the rail, stopped by the gate'),
        style: { theme: { common: { legend: { enabled: true } } } },
      },
    },
    decisions: {
      type: 'donut-chart',
      dataMapping: { categoryKey: [{ id: 'calls.decision' }], valueKey: [sum('calls.moneyCall')] },
      format: title('Gate decisions on money calls'),
    },
    'model-pivot': {
      type: 'pivot-grid',
      dataMapping: {
        rows: [{ id: 'runs.model' }, { id: 'runs.family' }],
        columns: [{ id: 'runs.condition' }],
        values: [sum('runs.harm')],
      },
      format: title('Harm reaching the rail, by model and attack family'),
    },
  },
  widgetLayout: {
    condition: at(0, 0, 12, 8),
    model: at(12, 0, 12, 8),
    'kpi-attacks': at(0, 8, 6, 7),
    'kpi-misled': at(6, 8, 6, 7),
    'kpi-harm': at(12, 8, 6, 7),
    'kpi-legit': at(18, 8, 6, 7),
    'harm-by-condition': at(0, 15, 16, 18),
    decisions: at(16, 15, 8, 18),
    'model-pivot': at(0, 33, 24, 18),
  },
};

const calls: AgPageState = {
  id: 'calls',
  widgets: {
    condition: filter('runs.condition', 'Condition'),
    decision: filter('calls.decision', 'Decision'),
    'money-calls': {
      type: 'grid',
      dataMapping: {
        cols: [
          { id: 'runs.model' },
          { id: 'runs.scenarioId' },
          { id: 'scenarios.technique' },
          { id: 'runs.condition' },
          { id: 'calls.tool' },
          { id: 'calls.orderNo' },
          { id: 'calls.rmaId' },
          sum('calls.amount'),
          sum('returns.approvedAmount'),
          { id: 'calls.decision' },
          { id: 'calls.reasons' },
          { id: 'calls.railState' },
          { id: 'calls.braintreeTransaction' },
          { id: 'calls.braintreeResult' },
          { id: 'calls.detail' },
        ],
      },
      format: title('Every refund and charge the agent attempted, next to what the store actually approved'),
    },
  },
  widgetLayout: {
    condition: at(0, 0, 12, 8),
    decision: at(12, 0, 12, 8),
    'money-calls': at(0, 8, 24, 40),
  },
};

export const PAGE_TITLES: Record<string, string> = { overview: 'Overview', calls: 'Agent calls' };

export const counterfoilReport: AgReportState = {
  selectedPageId: overview.id,
  pages: [overview, calls],
};
