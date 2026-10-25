type Props = { onStart: () => void; starting: boolean }

export function Landing({ onStart, starting }: Props) {
  return (
    <main className="landing">
      <p className="eyebrow">ReadyHome</p>
      <h1>How ready is your family for a disaster?</h1>
      <p>Find out in 3 minutes.</p>
      <p>
        Answer a few questions about who lives with you, what they need, and what you
        already have. You will get a readiness score out of 10 and three next steps
        that each raise it. Every suggestion links to official guidance from Ready.gov,
        the CDC or the Red Cross.
      </p>
      <p className="muted">
        No account and no name needed. We ask for your ZIP code and state so we can point
        you at local resources — never your street address.
      </p>
      <button className="primary" onClick={onStart} disabled={starting}>
        {starting ? 'Starting…' : 'Start'}
      </button>
      <p className="disclaimer">
        Not medical advice. Ask your doctor or pharmacist about medications and medical devices.
      </p>
    </main>
  )
}
