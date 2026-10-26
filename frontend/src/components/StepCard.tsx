import { useState } from 'react'
import type { Step } from '../types'

type Props = {
  step: Step
  busy: boolean
  justDone: boolean
  onComplete: (stepId: string, checked: string[]) => void
}

export function StepCard({ step, busy, justDone, onComplete }: Props) {
  const [open, setOpen] = useState(false)
  const [ticked, setTicked] = useState<string[]>([])

  function toggle(itemId: string) {
    setTicked((previous) =>
      previous.includes(itemId) ? previous.filter((id) => id !== itemId) : [...previous, itemId],
    )
  }

  function confirm() {
    onComplete(step.id, ticked)
    setOpen(false)
    setTicked([])
  }

  return (
    <article className={`step-card${justDone ? ' just-done' : ''}`}>
      <div className="step-top">
        <h3>{step.title}</h3>
        <span className="gain">+{step.points_gain} points</span>
      </div>

      <p className="why">{step.why}</p>

      <div className="tags">
        <span className="tag">About {step.est_minutes} min</span>
        <span className={`tag${step.est_cost_band === 'free' ? ' free' : ''}`}>
          {step.est_cost_band === 'free' ? 'Free to do' : step.est_cost_band}
        </span>
      </div>

      <ol className="how-to">
        {step.how_to.map((line) => (
          <li key={line}>{line}</li>
        ))}
      </ol>

      {step.cheap_options.length > 0 && (
        <div className="cheap">
          Low-cost ways to do it:
          <ul>
            {step.cheap_options.map((option) => (
              <li key={option.id}>{option.label}</li>
            ))}
          </ul>
        </div>
      )}

      {step.medical_note && <p className="medical">{step.medical_note}</p>}

      <div className="read-more">
        <span className="label">Read more</span>
        <div className="sources">
          {step.sources.map((source) => (
            <a
              key={source.id}
              className="source-chip"
              href={source.source_url}
              target="_blank"
              rel="noopener noreferrer"
              title={`${source.title} — ${source.publisher}`}
            >
              {source.title} ↗
            </a>
          ))}
        </div>
      </div>

      {!open ? (
        <button className="primary" onClick={() => setOpen(true)} disabled={busy}>
          I did this → earn +{step.points_gain}
        </button>
      ) : (
        <div className="self-check">
          <p className="muted" style={{ marginBottom: '0.5rem' }}>
            Tick whatever is genuinely done — part of it still counts, and you can come back
            for the rest.
          </p>
          {step.self_check.map((item) => (
            <label key={item.item_id}>
              <input
                type="checkbox"
                checked={ticked.includes(item.item_id)}
                onChange={() => toggle(item.item_id)}
              />
              <span>{item.label}</span>
            </label>
          ))}
          <div className="self-check-actions">
            <button className="primary" onClick={confirm} disabled={busy || ticked.length === 0}>
              {busy ? 'Saving…' : 'Claim my points'}
            </button>
            <button onClick={() => setOpen(false)} disabled={busy}>
              Cancel
            </button>
          </div>
        </div>
      )}
    </article>
  )
}
