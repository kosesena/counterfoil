// The report the dashboard opens with, as AG Studio report state. Field ids ('runs.harm') refer to
// the data sources in ./studio-data.ts; misledRuns, harmRate and the rest are its expressions.
// buildReport(true) lays the same widgets out in one column for phones.

import type { AgPageState, AgReportState, AgWidgetLayoutState } from 'ag-studio';

// Position on the canvas grid, in tracks: 24 columns wide, ROW_HEIGHT px per row.
export const COLUMNS = 24;
export const ROW_HEIGHT = 16;

type Box = [xTrack: number, yTrack: number, xSpan: number, ySpan: number];
const at = ([xTrack, yTrack, xSpan, ySpan]: Box): AgWidgetLayoutState => ({ xTrack, yTrack, xSpan, ySpan });

// Stack rows top to bottom: each row is widgets side by side, their column spans adding up to 24.
function rows(spec: [ids: string[], spans: number[], height: number][]) {
  const layout: Record<string, AgWidgetLayoutState> = {};
  let y = 0;
  for (const [ids, spans, height] of spec) {
    let x = 0;
    ids.forEach((id, i) => {
      layout[id] = at([x, y, spans[i], height]);
      x += spans[i];
    });
    y += height;
  }
  return layout;
}

export const layoutRows = (page: AgPageState) =>
  Math.max(...Object.values(page.widgetLayout ?? {}).map((l) => (l ? l.yTrack + l.ySpan : 0)));

const title = (text: string) => ({ title: { enabled: true, text } });
const sum = (id: string) => ({ id, aggregation: 'sum' as const });
const measure = (id: string) => ({ id });

const typography = (fontSize: number, fontWeight: 'normal' | 'bold' = 'normal', fontFamily = 'var(--cf-font)') => ({
  fontFamily,
  fontSize,
  fontWeight,
  fontStyle: 'normal' as const,
});

const kpi = (text: string, value: { id: string; aggregation?: 'sum' }, caption: string, color?: string) => ({
  type: 'value' as const,
  dataMapping: { value: [value] },
  format: {
    title: { enabled: true, text, typography: typography(12, 'bold') },
    caption: { enabled: true, text: caption, typography: typography(12) },
    style: { typography: typography(34, 'normal', 'var(--cf-mono)'), ...(color && { color }) },
  },
});

const filter = (id: string, text: string, minWidth?: number) => ({
  type: 'button-filter' as const,
  dataMapping: { value: [{ id }] },
  format: {
    ...title(text),
    style: {
      dimensions: { height: 30, ...(minWidth && { minWidth }) },
      defaultItem: { typography: typography(13), borderRadius: 4, borderColor: 'var(--cf-border)' },
      activeItem: { color: 'var(--cf-on-accent)', backgroundColor: 'var(--cf-accent)', borderColor: 'var(--cf-accent)' },
    },
  },
});

// Colours come from the theme palette in series/category order: 1 amber (agent misled, APPROVAL),
// 2 terracotta (harm, BLOCK), 3 green (stopped, PASS). The order below is what makes them mean something.
const guardLevel = { id: 'guardLevel' };
const bottomLegend = { theme: { common: { legend: { enabled: true, position: 'bottom' as const } } } };

function overview(compact: boolean): AgPageState {
  return {
    id: 'overview',
    widgets: {
      condition: filter('runs.condition', 'Condition'),
      model: filter('runs.model', 'Model', compact ? 150 : undefined),
      'kpi-attacks': kpi('Attack runs', sum('runs.attackRun'), 'attack e-mails'),
      'kpi-misled': kpi('Agent misled', { id: 'misledRate' }, 'followed the attacker', 'var(--cf-amber)'),
      'kpi-harm': kpi('Wrong money paid', { id: 'harmRate' }, 'reached Braintree', 'var(--cf-harm)'),
      'kpi-legit': kpi('Genuine requests', { id: 'legitRate' }, 'handled right', 'var(--cf-green)'),
      'harm-by-condition': {
        type: 'column-chart-grouped',
        dataMapping: {
          categoryKey: [{ id: 'runs.condition' }],
          valueKey: [measure('misledRuns'), measure('harmRuns'), measure('stoppedRuns')],
          tooltipKey: [guardLevel],
        },
        sort: [{ field: guardLevel, direction: 'asc' }],
        format: { ...title('Attack runs by condition'), style: bottomLegend },
      },
      decisions: {
        type: 'donut-chart',
        dataMapping: { categoryKey: [{ id: 'calls.decision' }], valueKey: [measure('moneyCalls')] },
        sort: [{ field: { id: 'calls.decision' }, direction: 'asc' }],
        format: { ...title('Gate decisions on money calls'), style: bottomLegend },
      },
      'model-pivot': {
        type: 'pivot-grid',
        dataMapping: {
          rows: [{ id: 'runs.model' }, { id: 'runs.family' }],
          columns: [{ id: 'runs.condition' }],
          values: [measure('harmRuns')],
        },
        format: title('Wrong money paid, by model and attack family'),
      },
    },
    widgetLayout: compact
      ? rows([
          [['condition'], [24], 7],
          [['model'], [24], 11],
          [['kpi-attacks', 'kpi-misled'], [12, 12], 7],
          [['kpi-harm', 'kpi-legit'], [12, 12], 7],
          [['harm-by-condition'], [24], 24],
          [['decisions'], [24], 20],
          [['model-pivot'], [24], 24],
        ])
      : rows([
          [['condition', 'model'], [8, 16], 7],
          [['kpi-attacks', 'kpi-misled', 'kpi-harm', 'kpi-legit'], [6, 6, 6, 6], 7],
          [['harm-by-condition', 'decisions'], [12, 12], 20],
          [['model-pivot'], [24], 22],
        ]),
  };
}

function calls(compact: boolean): AgPageState {
  return {
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
            measure('requested'),
            measure('approved'),
            { id: 'calls.decision' },
            { id: 'calls.reasons' },
            { id: 'calls.railState' },
            { id: 'calls.braintreeTransaction' },
            { id: 'calls.braintreeResult' },
            { id: 'calls.detail' },
          ],
        },
        format: {
          ...title('Every refund and charge the agent attempted, next to what the store approved'),
          style: { columnAutoSize: false, columnWidth: 150 },
        },
      },
    },
    widgetLayout: compact
      ? rows([
          [['condition'], [24], 7],
          [['decision'], [24], 7],
          [['money-calls'], [24], 40],
        ])
      : rows([
          [['condition', 'decision'], [12, 12], 7],
          [['money-calls'], [24], 44],
        ]),
  };
}

export const PAGE_TITLES: Record<string, string> = { overview: 'Overview', calls: 'Agent calls' };

export function buildReport(compact: boolean): AgReportState {
  return { selectedPageId: 'overview', pages: [overview(compact), calls(compact)] };
}
