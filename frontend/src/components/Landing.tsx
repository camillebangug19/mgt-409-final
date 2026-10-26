import { LANDING } from '../copy/landing'
import type { SessionStatus } from '../types'
import { Sunny } from './Sunny'

type Props = {
  onStart: () => void
  onResume: () => void
  onFresh: () => void
  starting: boolean
  returning: SessionStatus | null
}

export function Landing({ onStart, onResume, onFresh, starting, returning }: Props) {
  const back = returning?.found ? returning : null
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
              Pick up right where you left off.
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

      <span className="eyebrow">{LANDING.eyebrow}</span>

      <div className="landing-hero">
        <Sunny mood="hi" size={104} title="Sunny, your helper" />
        <h1>{LANDING.headline}</h1>
      </div>

      <p className="lede">{LANDING.subhead}</p>

      <div className="facts">
        {LANDING.tiles.map((tile) => (
          <div className="fact" key={tile.big}>
            <span className="big">{tile.big}</span>
            <span className="cap">{tile.cap}</span>
          </div>
        ))}
      </div>

      <h2 style={{ fontSize: '1.1rem' }}>{LANDING.howItWorksTitle}</h2>
      <ol className="steps-preview">
        {LANDING.howItWorks.map((item, index) => (
          <li key={item.lead}>
            <span className="num">{index + 1}</span>
            <span>
              <strong>{item.lead}</strong> {item.rest}
            </span>
          </li>
        ))}
      </ol>

      <p>{LANDING.closing}</p>

      <button className="primary" onClick={onStart} disabled={starting}>
        {starting ? 'Starting…' : LANDING.button}
      </button>

      <p className="muted" style={{ marginTop: '0.9rem' }}>
        {LANDING.underButton}
      </p>

      <p className="disclaimer">{LANDING.footer}</p>
    </main>
  )
}
