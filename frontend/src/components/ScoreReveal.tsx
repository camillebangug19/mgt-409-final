import { useEffect, useState } from 'react'
import { completeStep, fetchPlan } from '../api'
import type { Plan } from '../types'
import { Breakdown } from './Breakdown'
import { GoBag } from './GoBag'
import { StepCard } from './StepCard'

type Props = {
  sessionId: string
  onRestart: () => void
}

export function ScoreReveal({ sessionId, onRestart }: Props) {
  const [plan, setPlan] = useState<Plan | null>(null)
  const [gain, setGain] = useState<number | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchPlan(sessionId)
      .then(setPlan)
      .catch(() => setError('Could not load your score. Refresh to try again.'))
  }, [sessionId])

  async function onComplete(stepId: string, checked: string[]) {
    setBusy(true)
    setError(null)
    try {
      const next = await completeStep(sessionId, stepId, checked)
      setPlan(next)
      setGain(next.completion?.delta ?? null)
      window.setTimeout(() => setGain(null), 1800)
    } catch {
      setError('Could not save that. Try again.')
    } finally {
      setBusy(false)
    }
  }

  if (error && !plan) return <p className="error">{error}</p>
  if (!plan) return <p className="muted">Working out your score…</p>

  const resources = plan.local_resources.resources

  return (
    <main>
      <GoBag score={plan.score} label={plan.label} gain={gain} />

      <Breakdown breakdown={plan.breakdown} />
      <p className="muted">{plan.rubric_note}</p>

      <section className="steps">
        <h2>{plan.steps.length > 0 ? 'Your next steps' : 'You are done'}</h2>

        {plan.steps.length === 0 ? (
          <div className="done-banner">
            Every step that applies to your household is complete. Ready to go!
          </div>
        ) : (
          <>
            <p className="muted" style={{ marginBottom: '1rem' }}>
              Three at a time, biggest win first. Each one raises your score.
            </p>
            {plan.steps.map((step) => (
              <StepCard key={step.id} step={step} busy={busy} onComplete={onComplete} />
            ))}
          </>
        )}

        {plan.completed_step_ids.length > 0 && (
          <p className="muted">{plan.completed_step_ids.length} step(s) completed so far.</p>
        )}
      </section>

      <section className="resources">
        <h3>{plan.local_resources.is_fallback ? 'National resources' : `Resources in ${plan.local_resources.state}`}</h3>
        <ul>
          {resources.map((resource) => (
            <li key={resource.url}>
              <a href={resource.url} target="_blank" rel="noopener noreferrer">
                {resource.name}
              </a>
            </li>
          ))}
        </ul>
        <p className="muted" style={{ marginTop: '0.6rem' }}>
          For {plan.quantities.people} people you need about {plan.quantities.water_gallons} gallons
          of water for {plan.quantities.days} days.
          {plan.quantities.pets > 0 && ` Add water for your ${plan.quantities.pets} pet(s).`}
        </p>
      </section>

      {error && <p className="error">{error}</p>}

      <p className="disclaimer">{plan.disclaimer}</p>

      <button onClick={onRestart} style={{ marginTop: '0.5rem' }}>
        Start over
      </button>
    </main>
  )
}
