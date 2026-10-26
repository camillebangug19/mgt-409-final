/**
 * Sunny, the ReadyHome mascot (REQUIREMENTS.md 18.1).
 *
 * Traced from Camille's sunny_mascot.svg, which holds four poses sharing one
 * set of <defs>. Here each piece is a small component instead, so several
 * Sunnys can sit on the same page without duplicate SVG ids.
 *
 * The face is centred on 0,0; the viewBox leaves room for the waving hand,
 * the thought bubbles and the cheer sparkles.
 */

export type SunnyMood = 'hi' | 'thinking' | 'cheer' | 'calm'

type Props = {
  mood?: SunnyMood
  size?: number
  /** Decorative Sunnys sit beside text that already says the same thing. */
  title?: string | null
  className?: string
}

const BODY = '#FFC93C'
const EDGE = '#F29E1F'
const RAY = '#FFA62B'
const INK = '#1F2A44'
const MOUTH = '#8A4B08'
const BLUSH = '#FF8A7A'

const RAY_ANGLES = [0, 45, 90, 135, 180, 225, 270, 315]

function Rays() {
  return (
    <g className="sunny-rays" fill={RAY}>
      {RAY_ANGLES.map((angle) => (
        <rect key={angle} x="-7" y="-92" width="14" height="26" rx="7" transform={`rotate(${angle})`} />
      ))}
    </g>
  )
}

function Face() {
  return (
    <g>
      <circle r="58" fill={BODY} />
      <circle r="58" fill="none" stroke={EDGE} strokeWidth="3" />
      <ellipse cx="-34" cy="18" rx="10" ry="6" fill={BLUSH} opacity="0.55" />
      <ellipse cx="34" cy="18" rx="10" ry="6" fill={BLUSH} opacity="0.55" />
    </g>
  )
}

function Shades() {
  return (
    <g>
      <path d="M-44 -12 H-6 V0 Q-6 16 -25 16 Q-44 16 -44 0 Z" fill={INK} />
      <path d="M6 -12 H44 V0 Q44 16 25 16 Q6 16 6 0 Z" fill={INK} />
      <rect x="-8" y="-10" width="16" height="4" rx="2" fill={INK} />
      <path d="M-38 -7 L-28 -7 L-36 6 Z" fill="#7FB3FF" opacity="0.7" />
      <path d="M12 -7 L22 -7 L14 6 Z" fill="#7FB3FF" opacity="0.7" />
    </g>
  )
}

function Stroke({ d }: { d: string }) {
  return <path d={d} fill="none" stroke={MOUTH} strokeWidth="4" strokeLinecap="round" />
}

function Pose({ mood }: { mood: SunnyMood }) {
  if (mood === 'thinking') {
    return (
      <>
        <g transform="rotate(-6)">
          <Shades />
        </g>
        <Stroke d="M-10 30 Q4 34 16 26" />
        <g fill={INK} className="sunny-think">
          <circle cx="58" cy="-62" r="5" />
          <circle cx="74" cy="-74" r="6" />
          <circle cx="92" cy="-86" r="7" />
        </g>
      </>
    )
  }

  if (mood === 'cheer') {
    return (
      <>
        <Shades />
        <path d="M-22 22 Q0 50 22 22 Z" fill={MOUTH} />
        <path d="M-12 32 Q0 42 12 32" fill={BLUSH} />
        <g fill={RAY} className="sunny-sparkle">
          <path d="M-82 -60 l4 10 10 4 -10 4 -4 10 -4 -10 -10 -4 10 -4z" />
          <path d="M80 -50 l3 8 8 3 -8 3 -3 8 -3 -8 -8 -3 8 -3z" />
          <path d="M76 50 l3 7 7 3 -7 3 -3 7 -3 -7 -7 -3 7 -3z" />
        </g>
      </>
    )
  }

  if (mood === 'calm') {
    // Sunglasses pushed up, kind eyes. For sensitive questions.
    return (
      <>
        <g transform="translate(0,-30) scale(0.85)">
          <Shades />
        </g>
        <Stroke d="M-30 4 Q-22 -4 -14 4" />
        <Stroke d="M14 4 Q22 -4 30 4" />
        <Stroke d="M-14 28 Q0 36 14 28" />
      </>
    )
  }

  // hi, the default: waving.
  return (
    <>
      <Shades />
      <Stroke d="M-20 26 Q0 42 20 26" />
      <g className="sunny-wave" transform="translate(60,20) rotate(40)">
        <rect x="-8" y="-38" width="16" height="40" rx="8" fill={BODY} stroke={EDGE} strokeWidth="3" />
        <circle cx="0" cy="-42" r="11" fill={BODY} stroke={EDGE} strokeWidth="3" />
      </g>
    </>
  )
}

export function Sunny({ mood = 'hi', size = 72, title = null, className }: Props) {
  const classes = ['sunny', `sunny-${mood}`, className].filter(Boolean).join(' ')

  return (
    <svg
      className={classes}
      width={size}
      height={size}
      viewBox="-110 -110 220 220"
      role={title ? 'img' : 'presentation'}
      aria-label={title ?? undefined}
      aria-hidden={title ? undefined : true}
      focusable="false"
    >
      {title && <title>{title}</title>}
      <Rays />
      <Face />
      <Pose mood={mood} />
    </svg>
  )
}
