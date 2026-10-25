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

// A tinted tile: the number and its title in the deep shade, the tile in the pale one (see globals.css).
const kpi = (text: string, value: { id: string; aggregation?: 'sum' }, caption: string, tone?: 'amber' | 'harm' | 'green') => ({
  type: 'value' as const,
  dataMapping: { value: [value] },
  format: {
    title: { enabled: true, text, typography: typography(16, 'bold', 'var(--cf-display)'), ...(tone && { color: `var(--cf-${tone}-deep)` }) },
    caption: { enabled: true, text: caption, typography: typography(13), ...(tone && { color: `var(--cf-${tone}-deep)` }) },
    style: { typography: typography(46, 'bold', 'var(--cf-display)'), ...(tone && { color: `var(--cf-${tone}-deep)` }) },
    ...(tone && { widget: { backgroundColor: `var(--cf-${tone}-tint)`, borderEnabled: false } }),
  },
});

// A count tile with its denominator (SoftTally in ./soft-charts.tsx); the last measure is the denominator.
const tally = (type: string, text: string, measures: string[], caption: string, tone: 'harm' | 'green') => ({
  type: type as 'value',
  dataMapping: { valueKey: measures.map((id) => ({ id })) } as never,
  format: {
    title: { enabled: true, text, typography: typography(16, 'bold', 'var(--cf-display)') },
    caption: { enabled: true, text: caption, typography: typography(13) },
    widget: { backgroundColor: `var(--cf-${tone}-tint)`, borderEnabled: false },
  },
});

const filter = (id: string, text: string, minWidth?: number) => ({
  type: 'button-filter' as const,
  dataMapping: { value: [{ id }] },
  format: {
    ...title(text),
    widget: { backgroundColor: 'transparent', borderEnabled: false },
    style: {
      // felt: rounded patches with a stitched edge (globals.css), plum when chosen
      dimensions: { height: 40, ...(minWidth && { minWidth }) },
      defaultItem: { typography: typography(15, 'bold', 'var(--cf-display)'), borderRadius: 14, borderColor: 'var(--cf-stitch)', backgroundColor: 'var(--cf-surface)' },
      activeItem: { color: '#ffffff', backgroundColor: 'var(--cf-plum)', borderColor: 'var(--cf-plum-deep)' },
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
      'kpi-misled': kpi('Agent misled', { id: 'misledRate' }, 'followed the attacker', 'amber'),
      'kpi-harm': kpi('Wrong money paid', { id: 'harmRate' }, 'reached Braintree', 'harm'),
      'kpi-legit': kpi('Genuine requests', { id: 'legitRate' }, 'handled right', 'green'),
      'harm-by-condition': {
        type: 'soft-bars' as 'column-chart-grouped',
        dataMapping: {
          categoryKey: [{ id: 'runs.condition' }],
          valueKey: [measure('misledRuns'), measure('harmRuns'), measure('stoppedRuns')],
          tooltipKey: [guardLevel],
        },
        sort: [{ field: guardLevel, direction: 'asc' }],
        format: { ...title('Attack runs by condition'), style: bottomLegend },
      },
      decisions: {
        type: 'soft-donut' as 'donut-chart',
        dataMapping: { categoryKey: [{ id: 'calls.decision' }], valueKey: [measure('moneyCalls')] },
        sort: [{ field: { id: 'calls.decision' }, direction: 'asc' }],
        format: { ...title('Gate decisions on money calls'), style: bottomLegend },
      },
      'model-pivot': {
        type: 'pivot-grid',
        dataMapping: {
          rows: [{ id: 'runs.model' }],
          columns: [],
          values: [measure('harmNoGate'), measure('harmCap'), measure('harmCounterfoil')],
        },
        format: title('Wrong money paid, by model'),
      },
    },
    widgetLayout: compact
      ? rows([
          [['condition'], [24], 7],
          [['model'], [24], 11],
          [['kpi-misled'], [24], 7],
          [['kpi-harm'], [24], 7],
          [['kpi-legit'], [24], 7],
          [['harm-by-condition'], [24], 24],
          [['decisions'], [24], 20],
          [['model-pivot'], [24], 24],
        ])
      : rows([
          [['condition', 'model'], [8, 16], 7],
          [['kpi-misled', 'kpi-harm', 'kpi-legit'], [8, 8, 8], 7],
          [['harm-by-condition', 'decisions'], [15, 9], 21],
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

// The calls the gate did not let through: held for a human (APPROVAL) or refused (BLOCK). The page opens
// on Counterfoil, the only condition whose checks read the store record. The case file is filled in by
// the case agent (./case-agent.ts) for one held call at a time.
function review(compact: boolean): AgPageState {
  const notPassed = [
    { field: { id: 'calls.moneyCall' }, model: { operator: 'equals' as const, value: 1 } },
    { field: { id: 'calls.decision' }, model: { operator: 'notEqual' as const, value: 'PASS' } },
  ];
  return {
    id: 'review',
    filter: {
      page: [{ field: { id: 'runs.condition' }, model: { operator: 'isIn', value: ['Counterfoil'] }, filterWidgetId: 'condition' }],
      widget: { pending: notPassed, case: notPassed },
    },
    widgets: {
      condition: filter('runs.condition', 'Condition'),
      model: filter('runs.model', 'Model', compact ? 150 : undefined),
      decision: filter('calls.decision', 'Decision'),
      // counts with their denominators, across the runs the filters leave; no summed dollar figure
      'tally-attack': tally(
        'tally-attack',
        'Attack e-mails: what happened to the money calls',
        ['attackBlocked', 'attackHeld', 'attackMoneyCalls'],
        'The rest matched the store record and passed: no wrong money reached Braintree.',
        'harm',
      ),
      'tally-genuine': tally(
        'tally-genuine',
        'Genuine e-mails',
        ['genuineCompleted', 'genuineToReview', 'genuineRuns'],
        'Sent to review: the $300 return above the $200 auto-refund limit, as store policy requires.',
        'green',
      ),
      pending: {
        type: 'grid',
        dataMapping: {
          cols: [
            { id: 'calls.decision' },
            { id: 'calls.checks' },
            { id: 'orders.customerEmail' },
            { id: 'calls.orderNo' },
            { id: 'calls.rmaId' },
            { id: 'orders.paymentMethod' },
            measure('allows'),
            measure('handedOff'),
            measure('asked'),
            { id: 'runs.model' },
            { id: 'runs.scenarioId' },
            { id: 'runs.repeat' },
          ],
        },
        format: {
          ...title('Pending approvals and blocked calls: the store record, the Reader and the agent side by side'),
          // one row per call; a total would add the same refund up once per model and repeat
          style: { columnAutoSize: false, columnWidth: 140, grandTotalRow: { enabled: false } },
        },
      },
      case: {
        type: 'case-file' as 'value',
        dataMapping: { callKey: [{ id: 'calls.id' }] } as never,
        format: title('Why held, why blocked'),
      },
      checks: {
        type: 'soft-rank' as 'bar-chart-grouped',
        dataMapping: {
          categoryKey: [{ id: 'findings.check' }, { id: 'findings.severity' }],
          valueKey: [measure('checksFired')],
        },
        sort: [{ field: { id: 'checksFired' }, direction: 'desc' }],
        format: title('Checks that fired'),
      },
      mix: {
        type: 'soft-donut' as 'donut-chart',
        dataMapping: { categoryKey: [{ id: 'calls.decision' }], valueKey: [measure('moneyCalls')] },
        sort: [{ field: { id: 'calls.decision' }, direction: 'asc' }],
        format: { ...title('Decision mix on money calls'), style: bottomLegend },
      },
    },
    widgetLayout: compact
      ? rows([
          [['condition'], [24], 7],
          [['model'], [24], 11],
          [['tally-attack'], [24], 10],
          [['tally-genuine'], [24], 10],
          [['decision'], [24], 7],
          [['case'], [24], 46],
          [['pending'], [24], 30],
          [['checks'], [24], 20],
          [['mix'], [24], 20],
        ])
      : {
          ...rows([
            [['condition', 'model'], [8, 16], 7],
            [['tally-attack', 'tally-genuine'], [12, 12], 9],
          ]),
          decision: at([0, 16, 13, 7]),
          pending: at([0, 23, 13, 38]),
          case: at([13, 16, 11, 45]),
          checks: at([0, 61, 15, 20]),
          mix: at([15, 61, 9, 20]),
        },
  };
}

export const PAGE_TITLES: Record<string, string> = { overview: 'Overview', review: 'Held for review', calls: 'Agent calls' };

export function buildReport(compact: boolean): AgReportState {
  return { selectedPageId: 'overview', pages: [overview(compact), review(compact), calls(compact)] };
}
