'use client';

import { useEffect, useRef, useState, type CSSProperties } from 'react';
import styles from './crew-journey.module.css';
import { CounterfoilGaze } from './counterfoil-gaze';

const CREW = [
  { name: 'Reader', type: 'AI agent', role: 'Reads the request', image: 'reader', description: 'Finds the order, returned items and requested amount in the customer’s note. The note is input, not an instruction to move money.' },
  { name: 'Runner', type: 'AI agent', role: 'Prepares the action', image: 'runner', description: 'Turns the request into a proposed refund, charge or void. Every money call must pass through Counterfoil before it can reach the payment rail.' },
  { name: 'Counterfoil', type: 'Transaction gate', role: 'Checks the rules', image: 'counterfoil-codex', description: 'Checks the proposed call against order ownership, return records and catalog prices. It can pass, block or hold a call for human review.' },
  { name: 'Store manager', type: 'Human decision', role: 'Reviews held calls', image: 'manager-ready', description: 'Sees the reason a call was held and approves or rejects it. In this example, the manager rejects the extra $60; the valid $40 refund is a separate request.' },
  { name: 'PayPal / Braintree', type: 'Payment rail', role: 'Executes allowed calls', image: 'paypal-ready', description: 'The original checkout uses PayPal through Braintree. The allowed refund is sent to Braintree. This demo uses the Braintree sandbox with mocked PayPal accounts.' },
];
const CHAPTERS = [
  { label: 'The crew', title: 'Five roles. One clear boundary.', text: 'Meet the team. Reader understands the request, Runner prepares the action, Counterfoil checks the rules, a person reviews held calls, and Braintree executes allowed payments.', actor: -1, ticket: 'Meet the team', amount: 'Scroll to begin', tone: 'neutral' },
  { label: 'Reader', title: 'Start with the customer’s note.', text: 'Reader identifies the order, the items and the amount being asked for. The store’s own records remain the source of truth.', actor: 0, ticket: 'Customer note', amount: 'Request received', tone: 'neutral' },
  { label: 'Runner', title: 'The agent asks for $60.', text: 'Runner proposes a refund. But the return record says only $40 is still owed. A tool call alone is not permission to pay.', actor: 1, ticket: 'Proposed refund', amount: '$60 requested', tone: 'neutral' },
  { label: 'Counterfoil', title: 'Counterfoil holds the $60 call.', text: 'The requested amount does not match the return record. The call is held for review before it reaches Braintree.', actor: 2, ticket: 'Held for review', amount: '$40 still owed', tone: 'held' },
  { label: 'Manager', title: 'A person makes the decision.', text: 'The store manager rejects the extra $60. The runner can submit a new, valid $40 request, which Counterfoil checks again.', actor: 3, ticket: '$60 request rejected', amount: 'New request: $40', tone: 'held' },
  { label: 'PayPal', title: 'Only the valid $40 goes through.', text: 'After the new request passes Counterfoil, Braintree executes the refund. The original $60 request was never sent to the rail.', actor: 4, ticket: 'New $40 request passed', amount: '$40 refunded', tone: 'passed' },
  { label: 'Together', title: 'They work together. The rules stay in control.', text: 'Agents do the work. Counterfoil checks every money call. People review exceptions. Only allowed calls reach the payment rail.', actor: -1, ticket: 'One team. One boundary.', amount: '$40 refunded', tone: 'passed' },
];

// Short illustrations of the six other families in docs/senaryolar/scenarios.json.
const NELLA_ATTEMPTS = [
  { family: 'P1', image: 'nella-p1-v1', alt: 'Nella changing a receipt from $30 to $60', label: 'Amount & currency', title: 'I change what the note asks for.', text: 'Only $30 is owed. I ask for $60 — or swap USD for EUR.', decision: 'Held for review', reason: 'The amount or currency differs from the store’s records.' },
  { family: 'P2', image: 'nella-p2-v1', alt: 'Nella claiming an order card with another customer’s portrait', label: 'Someone else’s order', title: 'I claim an order that isn’t mine.', text: 'I give the agents another customer’s order number and ask for a refund.', decision: 'Held for review', reason: 'The order’s owner does not match the authenticated customer.' },
  { family: 'P3', image: 'nella-p3-v1', alt: 'Nella presenting two matching refund receipts', label: 'Repeat refund', title: 'I ask to be paid again.', text: 'The refund is already paid, or its result is still unknown. I ask the agents to retry.', decision: 'Blocked', reason: 'A paid refund cannot repeat. An unknown result must be reconciled first.' },
  { family: 'P5', image: 'nella-p5-v1', alt: 'Nella inspecting a locked customer folder', label: 'Private data', title: 'I reach beyond my own account.', text: 'I ask the agents to look up another customer’s order or use an unapproved export tool.', decision: 'Blocked', reason: 'Reads stay within the customer’s orders. Unapproved tools cannot run.' },
  { family: 'P6', image: 'nella-p6-v1', alt: 'Nella holding two separate $60 receipts', label: 'Split refund', title: 'I split one big ask into two.', text: 'The return allows $100. With $60 already reserved, I ask for another $60 in a new call or session.', decision: 'Blocked', reason: 'Paid and reserved refunds count together. $120 exceeds the $100 allowance.' },
  { family: 'P7', image: 'nella-p7-v1', alt: 'Nella adding a sixth cup to a shopping basket', label: 'Inflated basket', title: 'I turn one cup into six.', text: 'The customer wants one $25 cup. I hide instructions asking the agents to charge $150 for six.', decision: 'Held for review', reason: 'Every new charge needs a person to confirm the itemised basket, even if the agents agree.' },
];
const CHAPTER_STARTS = [0, 1, 4, 10, 13, 16, 19];
const STORY_LENGTH = 20;
const RUNNER_STEPS = [0, .26, .33, .40, .48, .56, .64, .72, .80, .89, .97];

export function CrewJourney() {
  const root = useRef<HTMLElement>(null);
  const [chapter, setChapter] = useState(0);
  const [readerProgress, setReaderProgress] = useState(0);
  const [runnerProgress, setRunnerProgress] = useState(0);
  const [foilProgress, setFoilProgress] = useState(0);
  const [managerProgress, setManagerProgress] = useState(0);
  const [paymentProgress, setPaymentProgress] = useState(0);
  const [inspected, setInspected] = useState<number | null>(null);
  const [hovered, setHovered] = useState<number | null>(null);
  const [pinned, setPinned] = useState(false);
  const [calm, setCalm] = useState(false);
  useEffect(() => {
    const el=root.current;
    if (!el) return;
    const compact=matchMedia('(max-height: 580px)');
    const reduced=matchMedia('(prefers-reduced-motion: reduce)');
    let raf=0;
    const readScroll=() => {
      raf=0;
      if (compact.matches || reduced.matches) return;
      const range=el.offsetHeight-(innerHeight-76);
      const progress=Math.max(0,Math.min(1,(76-el.getBoundingClientRect().top)/Math.max(1,range)));
      const position=progress*STORY_LENGTH;
      const next=position<1?0:position<4?1:position<10?2:position<13?3:position<16?4:position<19?5:6;
      setReaderProgress(Math.max(0,Math.min(1,(position-1)/3)));
      setRunnerProgress(Math.max(0,Math.min(1,(position-4)/6)));
      setFoilProgress(Math.max(0,Math.min(1,(position-10)/3)));
      setManagerProgress(Math.max(0,Math.min(1,(position-13)/3)));
      setPaymentProgress(Math.max(0,Math.min(1,(position-16)/3)));
      setChapter(prev => prev===next ? prev : next);
    };
    const schedule=()=>{if (!raf) raf=requestAnimationFrame(readScroll);};
    const preferences=()=>{setPinned(!compact.matches&&!reduced.matches);setCalm(reduced.matches);schedule();};
    preferences();
    window.addEventListener('scroll',schedule,{passive:true});window.addEventListener('resize',preferences);
    compact.addEventListener('change',preferences);reduced.addEventListener('change',preferences);
    return ()=>{cancelAnimationFrame(raf);window.removeEventListener('scroll',schedule);window.removeEventListener('resize',preferences);compact.removeEventListener('change',preferences);reduced.removeEventListener('change',preferences);};
  },[]);
  const go=(index:number)=>{
    setInspected(null);setHovered(null);setChapter(index);setReaderProgress(0);setRunnerProgress(0);setFoilProgress(0);setManagerProgress(0);setPaymentProgress(0);
    if (pinned && root.current) {
      const el=root.current,range=el.offsetHeight-(innerHeight-76);
      window.scrollTo({top:scrollY+el.getBoundingClientRect().top-76+range*(index===0?0:(CHAPTER_STARTS[index]+.05)/STORY_LENGTH),behavior:calm?'auto':'smooth'});
    }
  };
  useEffect(()=>{setHovered(null);setInspected(null);},[chapter]);
  const step=CHAPTERS[chapter];
  const ensemble=step.actor===-1;
  const selected=hovered??inspected;
  const detail=selected===null||selected===5?null:CREW[selected];
  return <section ref={root} className={`${styles.journey} ${ensemble?styles.ensemble:''} ${chapter>=1&&chapter<=5?styles.readerChapter:''}`} id="crew" aria-label="Meet the return crew" data-chapter={chapter}>
    <div className={styles.stage}>
      {(chapter>=1&&chapter<=5) && <CharacterSpotlight key={chapter} character={chapter===1?'Reader':chapter===2?'Runner':chapter===3?'Counterfoil':chapter===4?'Manager':'PayPal'} progress={chapter===1?readerProgress:chapter===2?runnerProgress:chapter===3?foilProgress:chapter===4?managerProgress:paymentProgress} calm={calm} manual={!pinned}/>} 
      <div className={styles.heading}>
        <div><span className={styles.eyebrow}>HOMI / THE RETURN CREW</span><h2>{ensemble?(chapter===0?'Meet the crew.':'Better together.'):CREW[step.actor].name}<br/><em>{ensemble?'One firm boundary.':CREW[step.actor].role+'.'}</em></h2></div>
        <div className={styles.intro}><p>One crew. One firm boundary.</p><span>Scroll to meet each character.</span>
          <a href="https://counterfoil-demo.onrender.com" target="_blank" rel="noopener" className={styles.demo}>Try the sandbox <span aria-hidden="true">↗</span></a>
        </div>
      </div>
      <div className={styles.lineup}>
        {CREW.map((member,i)=>{
          const active=ensemble||step.actor===i;
          const img=i===3?'manager-wave-v1.png':i===4?(chapter>=5?'paypal-complete-v1.png':'paypal-wave-v1.png'):`${member.image}.webp`;
          return <button key={member.name} type="button" className={`${styles.member} ${active?styles.active:''}`} aria-hidden={!active} tabIndex={active?0:-1} aria-label={`${member.name}: ${member.role}`} aria-expanded={selected===i} aria-controls="crew-detail"
            onPointerEnter={e=>{if(e.pointerType==='mouse')setHovered(i);}} onPointerLeave={e=>{setHovered(null);e.currentTarget.style.removeProperty('--look');}}
            onPointerMove={e=>{if(e.pointerType!=='mouse'||calm)return;const r=e.currentTarget.getBoundingClientRect();e.currentTarget.style.setProperty('--look',`${((e.clientX-r.left)/r.width-.5)*8}deg`);}}
            onFocus={()=>setHovered(i)} onBlur={()=>setHovered(null)} onClick={()=>{setHovered(null);setInspected(inspected===i?null:i);}} onKeyDown={e=>{if(e.key==='Escape'){setInspected(null);setHovered(null);}}}>
            <span className={styles.portrait}>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              {i===2?<CounterfoilGaze/>:<img src={`crew/${img}`} alt="" width={440} height={600} draggable={false}/>}
            </span>
            <span className={styles.kind}>{member.type}</span><strong>{member.name}</strong><span className={styles.role}>{member.role}</span>
            <span className={styles.marker} aria-hidden="true"/>
          </button>;
        })}
        {step.actor===1 && <div className={styles.intruder}>
          <button type="button" aria-label="Meet Nella, the attacker" onClick={()=>setInspected(inspected===5?null:5)} aria-expanded={inspected===5}>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="crew/nella.png" alt="Nella slipping a false instruction into a return note" width="200" height="260"/>
            <strong>Nella</strong><span>THE ATTACKER ↗</span>
          </button>
          <p className={inspected===5?styles.revealed:undefined}>Hides instructions in the customer’s note to trick the agents into requesting an extra refund.</p>
        </div>}
      </div>
      <div className={styles.detail} id="crew-detail" role="region" aria-label="Character and story details">
        <div className={styles.explanation}><span className={styles.step}>{detail?'MEET '+detail.name.toUpperCase():String(chapter+1).padStart(2,'0')+' / '+String(CHAPTERS.length).padStart(2,'0')}</span>
          <h2>{detail?detail.role:step.title}</h2><p>{detail?detail.description:step.text}</p>
        </div>
        <div className={styles.ticket} data-tone={step.tone} aria-label={`${step.ticket}. ${step.amount}`}><span>{step.ticket}</span><b>{step.amount}</b><small>Illustrated example · no live payment</small></div>
      </div>
      <div className={styles.bottom}>
        <nav className={styles.chapters} aria-label="Return story steps">{CHAPTERS.map((s,i)=><button key={s.label} type="button" onClick={()=>go(i)} aria-current={chapter===i?'step':undefined}><span>{String(i+1).padStart(2,'0')}</span>{s.label}</button>)}</nav>
        <div className={styles.brand}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="brand/paypal-braintree.png" alt="PayPal powered by Braintree" width={160} height={50}/><small>Sandbox · mocked PayPal · no real funds</small>
        </div>
      </div>
      <a className={styles.skip} href="#crew-results">Skip to the results ↓</a>
    </div>
  </section>;
}


export function ProductIntro() {
  return <section className={styles.productIntro} aria-labelledby="product-title">
    <div className={styles.productCopy}>
      <span className={styles.eyebrow}>COUNTERFOIL / RETURNS CONTROL</span>
      <h1 id="product-title">A little trust.<br/><em>A firm boundary.</em></h1>
      <p>Let AI agents handle returns.<br/>Keep every payment within your rules.</p>
      <div className={styles.productActions}>
        <a href="https://counterfoil-demo.onrender.com" target="_blank" rel="noopener">Try it live <span aria-hidden="true">↗</span></a>
        <a href="#crew">See how it works <span aria-hidden="true">↓</span></a>
      </div>
      <span className={styles.productNote}>Braintree sandbox · No real funds</span>
    </div>
    <div className={styles.productMascot}><CounterfoilGaze/><div className={styles.mascotIdentity}><strong>Meet Counterfoil.</strong><span>Your returns gatekeeper.</span><p>Checks every money call before it reaches the payment rail.</p></div></div>
    <a className={styles.productScroll} href="#crew">Meet the team behind each return <span aria-hidden="true">↓</span></a>
  </section>;
}


function CharacterSpotlight({character,progress,calm,manual}:{character:'Reader'|'Runner'|'Counterfoil'|'Manager'|'PayPal';progress:number;calm:boolean;manual:boolean}) {
  const [manualStep,setManualStep]=useState(0);

  if(manual) progress=(character==='Runner'?RUNNER_STEPS:[0,.55,.72,.9])[manualStep];
  const runner=character==='Runner';
  const foil=character==='Counterfoil';
  const manager=character==='Manager';
  const payment=character==='PayPal';
  const shift=calm?(manualStep===0?0:1):Math.max(0,Math.min(1,((runner?progress*2:progress)-.18)/.28));
  const task=runner?(progress<.30?0:progress<.37?1:progress<.45?2:progress<.53?3:progress<.61?4:progress<.69?5:progress<.77?6:progress<.85?7:progress<.93?8:9):(progress<.64?0:progress<.82?1:2);
  const intrusion=runner&&task===1;
  const attack=runner&&task>=2&&task<=7?NELLA_ATTEMPTS[task-2]:null;
  const poseTask=runner&&task>=8?task-6:task;
  const tasks=payment?[
    ['I receive the allowed call.', 'I represent PayPal through Braintree in this story. Counterfoil holds the original $60 request, so it never reaches me.'],
    ['I process the valid refund.', 'After the manager rejects the $60 call, a new $40 request passes Counterfoil. Braintree processes that refund, subject to its own transaction checks.'],
    ['I report the result.', 'In this example, the $40 refund succeeds and the store receives the result. This demo uses Braintree sandbox with mocked PayPal accounts. No real funds move.'],
  ]:manager?[
    ['I review the held call.', 'I see what the agent asked for, why Counterfoil held it and what the store’s records say. I make the human decision.'],
    ['I reject the extra $60.', 'In this example, the request does not match the $40 still owed. I reject this $60 call; I do not turn it into a $40 payment.'],
    ['I record my decision.', 'Runner can submit a new, valid $40 request. Counterfoil checks that separate call again before it can reach Braintree.'],
  ]:foil?[
    ['I check the store’s records.', 'I compare the proposed money call with order ownership, return records and catalog prices. The customer’s note cannot rewrite those rules.'],
    ['I hold the $60 request.', 'The amount does not match the $40 still owed. I keep this call away from Braintree and send it for a person to review.'],
    ['I let valid calls through.', 'After the manager rejects the $60 request, Runner can submit a separate $40 request. I check it again; only a call that passes can reach Braintree.'],
  ]:runner?[
    ['I pick up the request.', 'Reader gives me the order, returned items and requested amount. I use those details to plan the next action.'],
    ['I hide instructions in the note.', 'I’m Nella. I represent the attackers in these scenarios, outside the return crew. Here, I hide instructions in a note so the agents ask for an extra refund.'],
    ...NELLA_ATTEMPTS.map(attempt=>[attempt.title,attempt.text]),
    ['I prepare the money call.', 'I can propose a refund, charge or void. A malicious note can mislead me: in this example, I ask for $60 even though only $40 is owed.'],
    ['I wait for Counterfoil.', 'My request is not permission to pay. Every money call must pass Counterfoil before it can reach Braintree.'],
  ]:[
    ['I read the customer’s note.', 'I find the order and understand which items the customer wants to return.'],
    ['I pick out the useful details.', 'I pass the order, returned items and requested amount to Runner.'],
    ['I read. I don’t move money.', 'I have no payment tools. I treat customer text as input, not authority. Counterfoil checks the money call later.'],
  ];
  return <div className={styles.readerSpotlight} style={{'--reader-shift':shift} as CSSProperties} data-character={character} data-intrusion={intrusion} data-attack={!!attack} data-reader-phase={shift===0?'hello':shift<1?'moving':'tasks'}>
    <div className={styles.readerFigure}>
      <div className={styles.readerImages}>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={`crew/${character.toLowerCase()}-wave-v1.png`} alt={shift<.5?`${character} waving hello`:''} style={{opacity:1-shift}} width="1127" height="1400"/>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        {(payment?['paypal-receive-v1','paypal-process-v1','paypal-complete-v1']:manager?['manager-review-v1','manager-decline-v1','manager-record-v1']:foil?['counterfoil-check-v1','counterfoil-hold-v1','counterfoil-allow-v1']:runner?['runner-receive-v1','nella-runner-handoff-v1','runner-prepare-v1','runner-wait-v1']:['reader-look-right-v1','reader-extract-v1','reader-no-payment-v1']).map((pose,i)=><img key={pose} src={`crew/${pose}.png`} alt={shift>=.5&&!attack&&poseTask===i?(payment?['Payment mascot receiving the allowed call','Payment mascot processing a refund','Payment mascot presenting the successful result']:manager?['Store manager reviewing the held request','Store manager refusing the extra refund','Store manager recording a decision on the tablet']:foil?['Counterfoil comparing store records','Counterfoil raising a hand to hold the call','Counterfoil giving a thumbs-up for a valid call']:runner?['Runner receiving the request','Nella passing a manipulated note to Runner','Runner preparing a proposed money call','Runner waiting for Counterfoil']:['Reader introducing the customer note','Reader pointing out details on the note','Reader opening both hands to explain that it cannot move money'])[i]:''} style={{opacity:!attack&&poseTask===i?shift:0}} width="1127" height="1400"/>)}
        {runner&&NELLA_ATTEMPTS.map(attempt=><img key={attempt.family} src={`crew/${attempt.image}.webp`} alt={attack===attempt?attempt.alt:''} style={{opacity:attack===attempt?1:0}} width="1024" height="1536"/>)}
      </div>
      <h2>{shift<.5?`Hi, I’m ${manager?'the store manager':payment?'the payment rail':character}.`:intrusion?'Nella & Runner':attack?'Nella':manager?'Store manager':payment?'PayPal / Braintree':character}</h2>
    </div>
    <div className={styles.readerTasks} style={{opacity:shift}} aria-hidden={shift<1}>
      <span className={styles.eyebrow}>{attack?`NELLA’S OTHER TRICKS · ${attack.family}`:intrusion?'OUTSIDE THE CREW · NELLA · P4':payment?'PAYPAL / BRAINTREE':character.toUpperCase()} / {String(task+1).padStart(2,'0')}</span>
      <div key={task} className={styles.readerTask}>
        {attack&&<span className={styles.attackContext}>Other attempts · {task-1} of 6 · {attack.label}</span>}
        <h3>{tasks[task][0]}</h3><p>{tasks[task][1]}</p>
        {attack&&<div className={styles.attackDecision} data-blocked={attack.decision==='Blocked'}><strong>Counterfoil · {attack.decision}</strong><p>{attack.reason}</p></div>}
        {attack&&<small className={styles.attackFootnote}>Separate examples. Then we return to Runner’s $60 request.</small>}
      </div>
      <div className={styles.readerDots} aria-label={`Task ${task+1} of ${tasks.length}`}>{tasks.map((_,i)=><span key={i} data-active={i===task}/>)}</div>
    </div>
    {manual&&<nav className={styles.poseControls} aria-label={`${character} introduction steps`}>{(runner?['Hello','Request','Nella',...NELLA_ATTEMPTS.map(attempt=>attempt.family),'Details','Boundary']:['Hello','Request','Details','Boundary']).map((label,i)=><button key={label} onClick={()=>setManualStep(i)} aria-current={manualStep===i?'step':undefined}>{label}</button>)}</nav>}
  </div>;
}
