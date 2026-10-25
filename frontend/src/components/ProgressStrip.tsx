type Props = {
  sections: string[]
  activeIndex: number
}

/** Household -> Needs -> Pets -> Location -> What you already have. */
export function ProgressStrip({ sections, activeIndex }: Props) {
  if (sections.length === 0) return null

  return (
    <nav className="strip" aria-label="Survey progress">
      {sections.map((section, index) => {
        const state = index < activeIndex ? 'complete' : index === activeIndex ? 'active' : 'upcoming'
        return (
          <div key={section} className={`strip-step ${state}`}>
            <div
              className="strip-bar"
              role="img"
              aria-label={`${section}: ${state}`}
              style={{ opacity: state === 'upcoming' ? 0.5 : 1 }}
            />
            <span className="strip-label">{section}</span>
          </div>
        )
      })}
    </nav>
  )
}
