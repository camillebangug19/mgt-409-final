type Category = {
  category: string
  earned: number
  max_points: number
}

/**
 * One series (points earned), six categories. A single hue throughout:
 * the colour means "earned", so giving each row its own colour would imply
 * a distinction that is not in the data.
 */
export function Breakdown({ breakdown }: { breakdown: Category[] }) {
  if (breakdown.length === 0) return null

  return (
    <section className="breakdown">
      <h3>Where your points come from</h3>
      {breakdown.map((row) => {
        const pct = row.max_points > 0 ? (row.earned / row.max_points) * 100 : 0
        return (
          <div
            key={row.category}
            className="meter-row"
            title={`${row.category}: ${row.earned} of ${row.max_points} points`}
          >
            <div className="meter-head">
              <span className="cat">{row.category}</span>
              <span className="val">
                {row.earned} / {row.max_points}
              </span>
            </div>
            <div
              className="meter-track"
              role="meter"
              aria-valuenow={row.earned}
              aria-valuemin={0}
              aria-valuemax={row.max_points}
              aria-label={row.category}
            >
              <div className="meter-fill" style={{ width: `${Math.max(pct, 0)}%` }} />
            </div>
          </div>
        )
      })}
    </section>
  )
}
