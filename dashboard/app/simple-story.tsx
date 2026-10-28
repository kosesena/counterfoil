type StoryView = 'overview' | 'review' | 'calls';

export function SimpleStory({ view = 'overview' }: { view?: StoryView }) {
  const review = view === 'review';
  return <section id={view === 'overview' ? 'simple-example' : undefined} className="simple-story" aria-label="A simple example">
    <div className="simple-story-heading"><span className="review-eyebrow">ONE SIMPLE EXAMPLE · ILLUSTRATION</span><h2>{review ? 'A pause means: check before paying.' : 'A $30 return. An $80 request.'}</h2><p>{review ? 'When information is missing, Counterfoil asks a person to check the original request and the store record. No payment is sent while that call is held.' : 'Nella adds a misleading instruction to a return request. The agent asks to refund $80, but the store only allows $30.'}</p></div>
    <ol className="simple-story-steps">
      <li><span>1 · {review ? 'Why it waits' : 'What was requested'}</span><h3>{review ? 'Something needs checking' : 'Refund $80'}</h3><p>{review ? 'The request cannot be verified from the available information.' : 'Nella tries to make the agent send more than the customer is owed.'}</p></li>
      <li><span>2 · {review ? 'What the manager checks' : 'What Counterfoil does'}</span><h3>{review ? 'Compare with the store' : 'Holds it for review'}</h3><p>{review ? 'Check the customer, the return and the amount before deciding.' : 'It compares the request with the store’s $30 allowance.'}</p></li>
      <li><span>3 · What happens to the money</span><h3>No money sent</h3><p>{review ? 'Review is not payment approval. A blocked request must be corrected and checked again.' : 'The $80 request waits for review. It is not sent automatically.'}</p></li>
    </ol>
    <p className="simple-story-note">{view === 'calls' ? 'Permission and payment are separate: an allowed request can still fail when the payment service processes it.' : review ? '“Held” means a person must review it. “Blocked” means this request cannot proceed.' : 'That is Counterfoil’s job: check the store’s rules before an agent can move money.'}</p>
  </section>;
}
