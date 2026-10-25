import { useEffect, useRef, useState } from 'react'

type Props = {
  score: number
  label: string
  gain: number | null
}

const MIN = 1
const MAX = 10

function prefersReducedMotion() {
  return window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false
}

/** Counts up to the score, unless the user asked for reduced motion. */
function useCountUp(target: number) {
  const [shown, setShown] = useState(target)
  const previous = useRef(target)

  useEffect(() => {
    const from = previous.current
    previous.current = target
    if (from === target || prefersReducedMotion()) {
      setShown(target)
      return
    }
    const start = performance.now()
    const duration = 900
    let frame = 0
    const tick = (now: number) => {
      const t = Math.min((now - start) / duration, 1)
      const eased = 1 - Math.pow(1 - t, 3)
      setShown(Math.round((from + (target - from) * eased) * 2) / 2)
      if (t < 1) frame = requestAnimationFrame(tick)
    }
    frame = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(frame)
  }, [target])

  return shown
}

/**
 * A backpack that fills as the score rises. Ten levels, CSS transitions only.
 * The number beside it is the real value; the drawing is the encouragement.
 */
export function GoBag({ score, label, gain }: Props) {
  const shown = useCountUp(score)

  // Fill level 0-10 mapped onto the inner cavity of the bag.
  const level = Math.max(0, Math.min((score - MIN) / (MAX - MIN), 1))
  const cavityTop = 46
  const cavityHeight = 78
  const fillHeight = cavityHeight * level
  const fillY = cavityTop + (cavityHeight - fillHeight)

  const full = score >= MAX

  return (
    <div className="reveal">
      <div className="bag-wrap">
        <svg
          width="150"
          height="160"
          viewBox="0 0 150 160"
          role="img"
          aria-label={`Readiness ${score} out of 10: ${label}`}
        >
          <defs>
            <clipPath id="bag-cavity">
              <rect x="30" y={cavityTop} width="90" height={cavityHeight} rx="12" />
            </clipPath>
          </defs>

          {/* handle */}
          <path
            d="M58 40 C58 20, 92 20, 92 40"
            fill="none"
            stroke="var(--accent-ink)"
            strokeWidth="5"
            strokeLinecap="round"
          />
          {/* body */}
          <rect x="26" y="38" width="98" height="94" rx="18" fill="#fff" stroke="var(--accent-ink)" strokeWidth="3" />
          {/* contents rising like water */}
          <g clipPath="url(#bag-cavity)">
            <rect
              className="bag-fill"
              x="30"
              y={fillY}
              width="90"
              height={fillHeight}
              fill="var(--accent)"
              opacity="0.9"
            />
          </g>
          {/* front pocket, drawn over the fill */}
          <rect x="46" y="96" width="58" height="30" rx="8" fill="none" stroke="var(--accent-ink)" strokeWidth="3" />
          {/* straps */}
          <path d="M40 132 L40 142" stroke="var(--accent-ink)" strokeWidth="5" strokeLinecap="round" />
          <path d="M110 132 L110 142" stroke="var(--accent-ink)" strokeWidth="5" strokeLinecap="round" />
        </svg>

        {gain !== null && gain > 0 && (
          <span className="float-gain" aria-hidden="true">
            +{gain}
          </span>
        )}
      </div>

      <div className="bag-score">
        {shown}
        <span className="outof"> / 10</span>
      </div>
      <p className="bag-label">{full ? 'Ready to go!' : label}</p>
    </div>
  )
}
