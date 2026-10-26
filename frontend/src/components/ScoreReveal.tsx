import { useEffect, useState } from 'react'
import { completeStep, fetchPlan } from '../api'
import type { Plan } from '../types'
import { Breakdown } from './Breakdown'
import { GoBag } from './GoBag'
import { StepCard } from './StepCard'
import { CostPanel } from './CostPanel'
import { Sunny } from './Sunny'

type Props = {
  sessionId: string
  onRestart: () => void
}

/** Short names for the trophy chips, so they stay on one line. */
const STEP_NAMES: Record<string, string> = {
  'kit-phases': 'Kit started',
  'family-plan': 'Family plan',
  'evacuation-routes': 'Evacuation routes',
  'transportation-plan': 'Transport plan',
  'alerts-on': 'Alerts on',
  'meds-7day': '7-day meds',
  'backup-power': 'Backup power',
  'infant-feeding-kit': 'Infant feeding kit',
  'evacuation-helper': 'Evacuation helper',
  'pet-kit-lodging': 'Pet go-kit',
}

/** One short line from Sunny beside the go-bag. Fixed copy, no model call. */
function sunnyLine(plan: Plan): string {
  if (plan.score >= 10) return "You did it — 10 out of 10. Your family is ready to go!"
  if (plan.completed_step_ids.length > 0) return "Look how far you've come!"
  if (plan.score >= 7) return "You're already further along than you think."
  if (plan.score >= 4) return "A solid start. Three small steps and it climbs."
  return "Everyone starts somewhere. Let's take the first small step together."
}

function cheerFor(plan: Plan, earned: number): string {
  if (plan.score >= 10) return "That is 10 out of 10. Your household is ready to go!"
  if (plan.steps.length === 0) return 'Every step that applies to you is done. Brilliant.'
  const done = plan.completed_step_ids.length
  if (earned <= 0) return 'Logged. Finish the rest of that step and the score ticks up.'
  if (done === 1) return `Nice one — first step done, +${earned} points.`
  if (plan.score >= 8) return `+${earned}. You are nearly there.`
  return `+${earned} points. ${done} steps done — keep going.`
}

export function ScoreReveal({ sessionId, onRestart }: Props) {
  const [plan, setPlan] = useState<Plan | null>(null)
  const [gain, setGain] = useState<number | null>(null)
  const [cheer, setCheer] = useState<string | null>(null)
  const [justDone, setJustDone] = useState<string | null>(null)
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
      const earned = next.completion?.delta ?? 0
      setPlan(next)
      setGain(earned > 0 ? earned : null)
      setCheer(cheerFor(next, earned))
      setJustDone(stepId)
      window.setTimeout(() => setGain(null), 2000)
      window.setTimeout(() => setCheer(null), 5000)
      window.setTimeout(() => setJustDone(null), 2500)
    } catch {
      setError('Could not save that. Try again.')
    } finally {
      setBusy(false)
    }
  }

  if (error && !plan)
    return (
      <div className="reveal-sunny">
        <Sunny mood="calm" size={64} />
        <p className="error">{error}</p>
      </div>
    )
  if (!plan)
    return (
      <div className="reveal-sunny">
        <Sunny mood="thinking" size={72} title="Sunny, your helper" />
        <p className="speech">Working out your score…</p>
      </div>
    )

  const resources = plan.local_resources.resources

  return (
    <main>
      <GoBag score={plan.score} label={plan.label} gain={gain} cheer={cheer} />

      <div className="reveal-sunny">
        <Sunny mood={gain ? 'cheer' : 'hi'} size={68} title="Sunny, your helper" />
        <p className="speech">{sunnyLine(plan)}</p>
      </div>

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
              <StepCard
                key={step.id}
                step={step}
                busy={busy}
                justDone={justDone === step.id}
                onComplete={onComplete}
              />
            ))}
          </>
        )}

        {plan.completed_step_ids.length > 0 && (
          <div className="trophy-row" aria-label="Steps you have completed">
            {plan.completed_step_ids.map((id) => (
              <span className="trophy" key={id}>
                ✓ {STEP_NAMES[id] ?? id}
              </span>
            ))}
          </div>
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

      <CostPanel sessionId={sessionId} refreshKey={plan.completed_step_ids.length} />

      <p className="disclaimer">{plan.disclaimer}</p>

      <button onClick={onRestart} style={{ marginTop: '0.5rem' }}>
        Start over
      </button>
    </main>
  )
}
