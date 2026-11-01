'use client';

// AG Studio custom widgets that draw the charts the way the design sketch does: rounded bars with
// a pale fill and a firmer edge, no gridlines, and a donut with the total in its centre. Studio still
// owns the data: each widget asks its widgetApi for rows (filters and cross-filters applied), so the
// condition and model buttons drive these exactly as they drive Studio's own charts.

import { useEffect, useRef, useState } from 'react';
import type { AgWidgetData, AgWidgetDataFormat, AgWidgetFieldReference, AgWidgetParams } from 'ag-studio';
import type { AgWidgetDefinition } from 'ag-studio-react';

type Mapping = { categoryKey: AgWidgetFieldReference[]; valueKey: AgWidgetFieldReference[] };
type SoftWidget = AgWidgetData<Mapping, AgWidgetDataFormat<unknown>>;

// Series / category colours by meaning, in the same order as the palette in globals.css.
const TONES = [
  { fill: '#f6d98a', edge: '#d9b24f' }, // butter: agent misled, APPROVAL
  { fill: '#f2b8a6', edge: '#cf7a62' }, // terracotta: harm, BLOCK
  { fill: '#f0c8f8', edge: '#c77ddb' }, // lilac: stopped, PASS
];

type Row = Record<string, unknown>;

// Rows for the widget's own mapping; Studio applies the page filters. Refetches when a filter changes.
function useRows(params: AgWidgetParams<SoftWidget>) {
  const { widgetApi, dataMapping, sort } = params;
  const [rows, setRows] = useState<Row[] | null>(null);
  const fields = [...(dataMapping.categoryKey ?? []), ...(dataMapping.valueKey ?? [])];
  const key = JSON.stringify([fields.map((f) => f.key), sort?.map((s) => s.field.key + s.direction)]);

  useEffect(() => {
    let live = true;
    const load = () =>
      widgetApi
        .getData({ fields, sort: sort?.map((s) => ({ field: s.field, direction: s.direction })) })
        .then((r) => live && setRows(r.results.rows))
        .catch(() => live && setRows([]));
    load();
    return () => {
      live = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [widgetApi, key, params]);

  return rows;
}

// The chart's real pixel size, so text stays at its CSS size instead of scaling with the drawing.
function useSize() {
  const ref = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState({ w: 0, h: 0 });
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const ro = new ResizeObserver(([e]) => setSize({ w: e.contentRect.width, h: e.contentRect.height }));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);
  return [ref, size] as const;
}

const label = (params: AgWidgetParams<SoftWidget>, row: Row) => {
  const f = params.dataMapping.categoryKey?.[0];
  return f ? String(params.widgetApi.formatFieldValue(f, row[f.key]) ?? row[f.key]) : '';
};

function Legend({ items }: { items: { name: string; tone: (typeof TONES)[number] }[] }) {
  return (
    <div className="soft-legend">
      {items.map((i) => (
        <span key={i.name}>
          <i style={{ background: i.tone.fill, borderColor: i.tone.edge }} />
          {i.name}
        </span>
      ))}
    </div>
  );
}

export function SoftBars(params: AgWidgetParams<SoftWidget>) {
  const rows = useRows(params);
  const series = params.dataMapping.valueKey ?? [];
  const values = (rows ?? []).flatMap((r) => series.map((s) => Number(r[s.key]) || 0));
  const max = Math.max(1, ...values);
  const top = Math.ceil(max / 10) * 10;

  const [box, { w: W, h: H }] = useSize();
  const left = 30, base = H - 30, plot = base - 14;
  const groups = rows ?? [];
  const slot = (W - left) / Math.max(1, groups.length);
  const bar = Math.min(56, (slot * 0.7) / Math.max(1, series.length));

  return (
    <div className="soft">
      <div ref={box} className="soft-svg">
      {W > 0 && (
      <svg width={W} height={H} role="img">
        {[0, top / 2, top].map((v) => (
          <text key={v} x={left - 10} y={base - (v / top) * plot + 4} className="soft-axis" textAnchor="end">
            {v}
          </text>
        ))}
        <line x1={left} x2={W} y1={base} y2={base} className="soft-base" />
        {groups.map((row, g) => {
          const x0 = left + slot * g + (slot - bar * series.length - 6 * (series.length - 1)) / 2;
          return (
            <g key={g}>
              {series.map((s, i) => {
                const v = Number(row[s.key]) || 0;
                const h = (v / top) * plot;
                const tone = TONES[i % TONES.length];
                return (
                  <rect
                    key={s.key}
                    x={x0 + i * (bar + 6)}
                    y={base - h}
                    width={bar}
                    height={Math.max(h, 0)}
                    rx={Math.min(10, bar / 3)}
                    fill={tone.fill}
                    stroke={tone.edge}
                    strokeWidth={1}
                  >
                    <title>{`${label(params, row)} · ${params.widgetApi.getFieldName(s)}: ${v}`}</title>
                  </rect>
                );
              })}
              <text x={left + slot * g + slot / 2} y={base + 26} className="soft-cat" textAnchor="middle">
                {label(params, row)}
              </text>
            </g>
          );
        })}
      </svg>
      )}
      </div>
      <Legend items={series.map((s, i) => ({ name: params.widgetApi.getFieldName(s), tone: TONES[i % TONES.length] }))} />
    </div>
  );
}

export function SoftDonut(params: AgWidgetParams<SoftWidget>) {
  const rows = useRows(params);
  const value = params.dataMapping.valueKey?.[0];
  const slices = (rows ?? []).map((r, i) => ({ name: label(params, r), v: value ? Number(r[value.key]) || 0 : 0, tone: TONES[i % TONES.length] }));
  const total = slices.reduce((a, s) => a + s.v, 0);
  const R = 74, C = 2 * Math.PI * R;
  let offset = 0;

  return (
    <div className="soft">
      <svg viewBox="0 0 220 220" className="soft-svg soft-donut" role="img">
        <circle cx="110" cy="110" r={R} fill="none" stroke="var(--cf-gridline)" strokeWidth="26" />
        {slices.map((s) => {
          const len = total ? (s.v / total) * C : 0;
          const el = (
            <circle
              key={s.name}
              cx="110"
              cy="110"
              r={R}
              fill="none"
              stroke={s.tone.fill}
              strokeWidth="26"
              strokeDasharray={`${Math.max(len - 3, 0)} ${C}`}
              strokeDashoffset={-offset}
              strokeLinecap="round"
              transform="rotate(-90 110 110)"
            >
              <title>{`${s.name}: ${s.v}`}</title>
            </circle>
          );
          offset += len;
          return el;
        })}
        <text x="110" y="112" textAnchor="middle" className="soft-total">
          {total}
        </text>
        <text x="110" y="134" textAnchor="middle" className="soft-axis">
          {value ? params.widgetApi.getFieldName(value).toLowerCase() : ''}
        </text>
      </svg>
      <Legend items={slices.map((s) => ({ name: `${s.name} ${s.v}`, tone: s.tone }))} />
    </div>
  );
}

// Horizontal bars, longest first: one per check, toned by what the check does to a call (the second
// category field): amber for APPROVAL (held for a human), terracotta for BLOCK.
export function SoftRank(params: AgWidgetParams<SoftWidget>) {
  const rows = useRows(params);
  const [name, tone] = params.dataMapping.categoryKey ?? [];
  const value = params.dataMapping.valueKey?.[0];
  const items = (rows ?? []).map((r) => ({
    name: String(name ? r[name.key] : ''),
    v: value ? Number(r[value.key]) || 0 : 0,
    tone: TONES[tone && r[tone.key] === 'BLOCK' ? 1 : 0],
  }));
  const max = Math.max(1, ...items.map((i) => i.v));

  return (
    <div className="soft soft-rank">
      <ol>
        {items.map((i) => (
          <li key={i.name}>
            <span className="soft-rank-name">{i.name}</span>
            <span className="soft-rank-track">
              <i style={{ width: `${(i.v / max) * 100}%`, background: i.tone.fill, borderColor: i.tone.edge }} />
            </span>
            <b>{i.v}</b>
          </li>
        ))}
      </ol>
      <Legend items={[{ name: 'Holds for a human', tone: TONES[0] }, { name: 'Blocks', tone: TONES[1] }]} />
    </div>
  );
}

// Counts with their denominator, never a summed amount: the value fields are the parts ("25 blocked",
// "3 held for a person") and the last one is what they are counted out of ("of 94 attack money calls").
// Part colours come from the definition: the attack tally reads harm then amber, the genuine one green then amber.
function tally(tones: string[]) {
  return function SoftTally(params: AgWidgetParams<SoftWidget>) {
    const rows = useRows(params);
    const fields = params.dataMapping.valueKey ?? [];
    const row = rows?.[0] ?? {};
    const parts = fields.slice(0, -1);
    const of = fields[fields.length - 1];
    const n = (f: (typeof fields)[number]) => Number(row[f.key]) || 0;
    return (
      <div className="soft-tally">
        <div>
          {parts.map((f, i) => (
            <span key={f.key} style={{ color: `var(--cf-${tones[i % tones.length]}-deep)` }}>
              <strong>{rows ? n(f) : '…'}</strong> {params.widgetApi.getFieldName(f)}
            </span>
          ))}
        </div>
        {of && (
          <small>
            of {rows ? n(of) : '…'} {params.widgetApi.getFieldName(of)}
          </small>
        )}
      </div>
    );
  };
}

const mapping = {
  categoryKey: { type: 'fieldset' as const, supportedRoles: ['category' as const], intent: 'category' as const, sort: true },
  valueKey: { type: 'fieldset' as const, supportedRoles: ['numeric' as const], intent: 'value' as const },
};

const definition = (id: string, label: string, comp: typeof SoftBars): AgWidgetDefinition<string, SoftWidget> => ({
  id,
  label,
  comp,
  dataMapping: mapping,
  form: (p) => p.createDefaults({ dataMappingItems: [{ key: 'categoryKey', label: 'Category' }, { key: 'valueKey', label: 'Values' }] }),
  defaultSize: { width: 12, height: 18 },
  minSize: { width: 4, height: 8 },
});

export const SOFT_WIDGETS = [
  definition('soft-bars', 'Soft bars', SoftBars),
  definition('soft-donut', 'Soft donut', SoftDonut),
  definition('soft-rank', 'Soft ranking', SoftRank),
  definition('tally-attack', 'Attack tally', tally(['harm', 'amber'])),
  definition('tally-genuine', 'Genuine tally', tally(['green', 'amber'])),
];
