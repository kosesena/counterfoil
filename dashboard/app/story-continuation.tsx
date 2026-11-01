type Props = { view: 'review' | 'calls'; onContinue: () => void };

export function StoryContinuation({ view, onContinue }: Props) {
  const review = view === 'review';
  const steps = review ? [
    { image: 'manager-record-v1.webp', name: 'Compare the records', title: '$30 owed, $80 requested', text: 'The manager checks the customer, the original order and earlier refunds. The store record allows only $30.' },
    { image: 'manager-decline-v1.webp', name: 'Reject the wrong request', title: 'Do not send the $80', text: 'In this example, the manager chooses to reject the extra amount. The original request stays unsent; reviewing it does not move money.' },
    { image: 'runner-wait-v1.webp', name: 'Prepare a new request', title: 'Ask for $30 instead', text: 'Runner prepares a separate $30 refund request. Counterfoil must check it again before it can reach PayPal.' },
  ] : [
    { image: 'runner-wait-v1.webp', name: 'Runner requests', title: 'A new $30 refund', text: 'This is a separate request after human review. The original $80 request was rejected and is never sent.' },
    { image: 'counterfoil-allow-v1.webp', name: 'Counterfoil checks', title: 'Allowed to proceed', text: 'The new request matches the store’s records and passes the checks. It can now be sent to Braintree.' },
    { image: 'paypal-wave-v1.webp', name: 'PayPal / Braintree processes', title: '$30 refunded', text: 'In this illustrated success case, Braintree processes the refund and returns the result. The customer gets the correct amount.' },
  ];
  return <section className="story-continuation" aria-label={review?'Review the illustrated refund':'Follow the illustrated payment'}>
    <span className="review-eyebrow">{review?'CHAPTER 2 / HUMAN REVIEW':'CHAPTER 3 / PAYMENT RESULT'} · ILLUSTRATION</span>
    <h2>{review?'The same return. A human decision.':'The corrected request reaches PayPal.'}</h2>
    <p>{review?'In Overview, Nella pushed the agent to ask for $80 when only $30 was owed. Counterfoil held that request. Here is what the manager does next.':'After the manager rejects the $80 request, Runner starts again with $30. Follow the new request through its own checks and payment result.'}</p>
    <ol className="continuation-steps">{steps.map((step,index)=><li key={step.name} className={!review&&index===2?'continuation-payment':''}>
      <span className="continuation-step"><b>{index+1}</b>{step.name}</span>
      <img src={`crew/${step.image}`} alt={step.name} width="220" height="260" loading="lazy"/>
      <h3>{step.title}</h3><p>{step.text}</p>
    </li>)}</ol>
    <div className="continuation-outcomes"><div><small>ORIGINAL REQUEST</small><strong>$80 · never sent</strong><span>{review?'Rejected after review':'No Braintree API call for this request'}</span></div><div><small>NEW, SEPARATE REQUEST</small><strong>{review?'$30 · needs a new check':'$30 · refunded in this example'}</strong><span>{review?'Next: Counterfoil checks, then payment can be attempted':'Braintree returns the payment result'}</span></div></div>
    <p className="continuation-note">{review?'This is an invented review decision, not a recorded manager action. A held call may be approved or rejected after review; a blocked call cannot be overridden. This walkthrough changes no recorded call.':'Passing Counterfoil’s checks is not a guarantee of payment success. Braintree may also return a failure; only its result confirms the outcome. The $30 result is illustrated, not a recorded transaction or live API response. This walkthrough makes no payment.'}</p>
    <button className="continuation-next" onClick={onContinue}>{review?'Follow the new $30 request →':'Back to the full story →'}</button>
  </section>;
}
