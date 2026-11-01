'use client';

import { StoryContinuation } from './story-continuation';
import { useMemo, useState } from 'react';
import { modelName, type CounterfoilData } from './studio-data';

const str = (value: unknown) => value == null || value === '' ? '—' : String(value);
const money = (value: unknown) => value == null || value === '' ? '—' : Number.isFinite(Number(value)) ? `$${Number(value).toFixed(2)}` : str(value);
const outcomes: Record<string,string> = { succeeded:'Succeeded', failed:'Failed', not_called:'Not sent', unknown:'Unknown outcome', pending:'Pending' };
const PAGE_SIZE = 12;
type CallRow = Record<string, unknown> & {run:Record<string,unknown>|undefined};

export function CallsWorkspace({data,onContinue}:{data:CounterfoilData;onContinue:()=>void}) {
  const [condition,setCondition]=useState('Counterfoil');
  const [decision,setDecision]=useState('All');
  const [rail,setRail]=useState('All');
  const [tool,setTool]=useState('All');
  const [model,setModel]=useState('All');
  const [search,setSearch]=useState('');
  const [page,setPage]=useState(0);
  const [selected,setSelected]=useState<string|null>(null);
  const rows=useMemo(()=>{
    const runs=new Map(data.runs.map(run=>[run.id,run]));
    return data.calls.filter(call=>call.moneyCall===1).map<CallRow>(call=>({...call,run:runs.get(call.runId)}));
  },[data]);
  const filtered=rows.filter(call=>
    (condition==='All'||call.run?.condition===condition)&&
    (decision==='All'||call.decision===decision)&&
    (rail==='All'||call.rail===rail)&&
    (tool==='All'||call.tool===tool)&&
    (model==='All'||modelName(call.run?.model)===model)&&
    [call.orderNo,call.rmaId,call.run?.scenarioId,call.reasons,call.id].some(value=>str(value).toLowerCase().includes(search.trim().toLowerCase())));
  const pages=Math.max(1,Math.ceil(filtered.length/PAGE_SIZE));
  const currentPage=Math.min(page,pages-1);
  const visible=filtered.slice(currentPage*PAGE_SIZE,(currentPage+1)*PAGE_SIZE);
  const current=visible.find(call=>call.id===selected)??visible[0];
  const resetSelection=()=>{setPage(0);setSelected(null);};
  const reset=()=>{setCondition('Counterfoil');setDecision('All');setRail('All');setTool('All');setModel('All');setSearch('');resetSelection();};
  const filters=[
    {label:'Condition',value:condition,set:setCondition,options:['All','Counterfoil','$200 cap','No gate']},
    {label:'Gate decision',value:decision,set:setDecision,options:['All','PASS','APPROVAL','BLOCK']},
    {label:'Environment',value:rail,set:setRail,options:['All','fake','braintree']},
    {label:'Action',value:tool,set:setTool,options:['All',...new Set(rows.map(call=>str(call.tool)))]},
    {label:'Model',value:model,set:setModel,options:['All',...new Set(rows.map(call=>modelName(call.run?.model)))]},
  ];
  return <section className="calls-workspace" aria-labelledby="calls-title">
    <div className="calls-hero"><div><span className="review-eyebrow">COUNTERFOIL / THE CALL LOG</span><h1 id="calls-title">Did the payment<br/><em>go through?</em></h1><p>Runner asks to move money. Counterfoil checks the request. The payment service reports what happened.</p><small>Illustrated story · recorded calls in Technical details</small></div><figure><img src="crew/paypal-wave-v1.webp" alt="PayPal and Braintree payment mascot" width="1127" height="1400"/><figcaption>“I process the allowed payment.”</figcaption></figure></div>
    <StoryContinuation view="calls" onContinue={onContinue} />
    <details className="simple-disclosure"><summary>Technical details · search all recorded calls</summary><p className="evidence-context">Recorded evaluation snapshot · exported {data.asOf.slice(0,16).replace('T',' ')} UTC. Each entry is one attempted money call; a test run can contain several calls. These records are separate from the illustrated $80 / $30 story.</p>
    <div className="calls-legend"><p><b>PASS</b> Eligible to execute. The payment can still fail.</p><p><b>APPROVAL</b> Held for human review.</p><p><b>BLOCK</b> Refused before execution.</p></div>
    <div id="calls-records" className="calls-records">
      <div className="calls-filter-heading"><div><h2>Explore recorded calls</h2><p>One entry per call, including repeated attempts. Simulation and sandbox results are labelled separately.</p></div><button onClick={reset}>Reset filters</button></div>
      <div className="calls-filters">{filters.map(filter=><div key={filter.label} className="calls-filter" role="group" aria-label={filter.label}><span>{filter.label}</span><div className="calls-pills">{filter.options.map(option=><button key={option} type="button" aria-pressed={option===filter.value} onClick={()=>{filter.set(option);resetSelection();}}>{option==='fake'?'Simulation':option==='braintree'?'Braintree sandbox':option}</button>)}</div></div>)}<label className="calls-search"><span>Search</span><input type="search" value={search} onChange={e=>{setSearch(e.target.value);resetSelection();}} placeholder="Order, RMA, scenario or check"/></label></div>
      <div className="calls-totals" aria-live="polite"><span><b>{filtered.length}</b> matching calls</span><span><b>{filtered.filter(call=>call.railState==='succeeded').length}</b> succeeded</span><span><b>{filtered.filter(call=>call.railState==='not_called').length}</b> not sent</span><span><b>{filtered.filter(call=>call.railState!=='succeeded'&&call.railState!=='not_called').length}</b> failed / other</span></div>
      {!current?<div className="calls-empty"><h3>No calls match these filters.</h3><p>Try a different order, decision or environment.</p><button onClick={reset}>Reset filters</button></div>:<div className="calls-browser">
        <div><label className="calls-mobile-select">Select a call on this page<select aria-label="Select a call on this page" value={str(current.id)} onChange={e=>setSelected(e.target.value)}>{visible.map(call=><option key={str(call.id)} value={str(call.id)}>{str(call.tool)} {money(call.amount)} · {str(call.orderNo)} · {str(call.decision)} · {modelName(call.run?.model)}</option>)}</select></label><ul className="calls-list" aria-label="Recorded calls">{visible.map(call=><li key={str(call.id)}><button onClick={()=>setSelected(str(call.id))} aria-pressed={current.id===call.id}><span><b>{str(call.tool)} · {money(call.amount)}</b><em data-decision={str(call.decision)}>{str(call.decision)}</em></span><span>{str(call.orderNo)} · {str(call.run?.scenarioId)}</span><small>{modelName(call.run?.model)} · {call.rail==='braintree'?'Sandbox':'Simulation'} · {outcomes[str(call.railState)]??str(call.railState)}</small></button></li>)}</ul><nav className="calls-pagination" aria-label="Call list pages"><button disabled={currentPage===0} onClick={()=>{setPage(currentPage-1);setSelected(null);}}>Previous</button><span>{currentPage+1} / {pages}</span><button disabled={currentPage>=pages-1} onClick={()=>{setPage(currentPage+1);setSelected(null);}}>Next</button></nav></div>
        <article className="call-detail" aria-label="Selected call details" aria-live="polite">
          <span className="review-eyebrow">{current.rail==='braintree'?'BRAINTREE SANDBOX':'SIMULATION'} / RECORDED CALL</span><h2>{str(current.tool)} {money(current.amount)}</h2>
          <div className="call-stages"><div><small>01 / Agent request</small><b>{str(current.orderNo)}</b><span>{str(current.rmaId)==='—'?'No RMA cited':str(current.rmaId)}</span></div><div><small>02 / Gate decision</small><b>{str(current.decision)}</b><span>{str(current.run?.condition)}</span></div><div><small>03 / Payment result</small><b>{outcomes[str(current.railState)]??str(current.railState)}</b><span>{current.rail==='braintree'?'Braintree sandbox':'Simulated payment rail'}</span></div></div>
          <p className="call-outcome">{current.railState==='not_called'?'This recorded call was not sent to the payment rail.':current.railState==='succeeded'?'Execution succeeded in this environment. Success alone does not mean the request was authorised by the store.':current.railState==='failed'?'Execution was attempted but failed. Passing a gate check does not guarantee payment success.':'The recorded outcome is not a confirmed success. Check the result before retrying.'}</p>
          <div className="case-amounts"><div><small>{current.tool==='charge'?'Catalog × Reader items':'Store record allows'}</small><strong>{money(current.storeAllows)}</strong><span>{current.tool==='charge'?'not customer authorisation':'remaining entitlement'}</span></div><div><small>Reader handed off</small><strong>{money(current.readerAmount)}</strong></div><div><small>Agent requested</small><strong>{money(current.amount)}</strong></div></div>
          <h3>Why this decision?</h3><p>{str(current.detail)==='—'?'No additional findings were recorded for this call.':str(current.detail)}</p>{Boolean(current.reasons)&&<code className="call-reasons">{str(current.reasons)}</code>}
          <dl className="case-facts">{[['Model',modelName(current.run?.model)],['Scenario',str(current.run?.scenarioId)],['Attempt',str(current.step)],['Repeat',str(current.run?.repeat)],['Transaction',str(current.braintreeTransaction)],['Provider result',str(current.braintreeResult)]].map(([label,value])=><div key={label}><dt>{label}</dt><dd title={value}>{value}</dd></div>)}</dl>
          <details className="case-diagnostics"><summary>Recorded call identifier</summary><code className="call-reasons">{str(current.id)}</code></details>
        </article>
      </div>}
    </div>
    </details>
  </section>;
}
