import type { SessionStatus } from '../types'

type Props = {
  onStart: () => void
  onResume: () => void
  onFresh: () => void
  starting: boolean
  returning: SessionStatus | null
}

export function Landing({ onStart, onResume, onFresh, starting, returning }: Props) {
  // Narrowed once, so the rest of the component can use it safely.
  const back = returning?.found ? returning : null
  const knowsYou = back !== null
  const finished = back?.survey_done ?? false

  return (
    <main className="landing">
      {back && (
        <section className="welcome-back">
          <h2>Welcome back 👋</h2>
          {finished ? (
            <p>
              You scored <strong>{back.latest_score} out of 10</strong> last time
              {(back.completed_steps ?? 0) > 0
                ? ` and have ticked off ${back.completed_steps} step${back.completed_steps === 1 ? '' : 's'}.`
                : '.'}{' '}
              Pick up where you left off.
            </p>
          ) : (
            <p>
              You were <strong>{Math.round((back.progress ?? 0) * 100)}% through</strong> the
              questions. Your answers are still here.
            </p>
          )}
          <div className="welcome-actions">
            <button className="primary" onClick={onResume}>
              {finished ? 'See my score and steps' : 'Carry on where I left off'}
            </button>
            <button onClick={onFresh}>Start fresh</button>
          </div>
        </section>
      )}

      <span className="eyebrow">Free · No account</span>
      <h1>How ready is your family for an emergency?</h1>
      <p className="lede">
        Answer a few friendly questions and find out in about three minutes. No judgement —
        most households start lower than they expect, and that is exactly the point.
      </p>

      <div className="facts">
        <div className="fact">
          <span className="big">3 min</span>
          <span className="cap">of easy questions</span>
        </div>
        <div className="fact">
          <span className="big">1–10</span>
          <span className="cap">your readiness score</span>
        </div>
        <div className="fact">
          <span className="big">3 steps</span>
          <span className="cap">to raise it, free ones first</span>
        </div>
      </div>

      <h2 style={{ fontSize: '1.1rem' }}>How it works</h2>
      <ol className="steps-preview">
        <li>
          <span className="num">1</span>
          <span>
            <strong>Tell us about your household.</strong> Who lives with you, anything that would
            make leaving harder, pets, and what you already have. Tap an answer or type your own.
          </span>
        </li>
        <li>
          <span className="num">2</span>
          <span>
            <strong>Get your score out of 10.</strong> Built from Ready.gov, CDC and Red Cross
            checklists, and adjusted to your household — you are never marked down for something
            that does not apply to you.
          </span>
        </li>
        <li>
          <span className="num">3</span>
          <span>
            <strong>Do three things, watch it climb.</strong> Just three at a time, each showing
            exactly how many points it earns. Many of them are free.
          </span>
        </li>
      </ol>

      <p>
        Built for real households — a toddler, a grandparent who uses oxygen, a dog, no car. Every
        suggestion links to official guidance you can check yourself.
      </p>

      <button className="primary" onClick={onStart} disabled={starting}>
        {starting ? 'Starting…' : knowsYou ? 'Start a new check' : 'Start — it takes 3 minutes'}
      </button>

      <p className="muted" style={{ marginTop: '0.9rem' }}>
        No sign-up, no name, no street address. We ask for your ZIP and state only so we can point
        you to local help, and your progress is remembered on this device.
      </p>

      <p className="disclaimer">
        Not medical advice. Ask your doctor or pharmacist about medications and medical devices.
      </p>
    </main>
  )
}
