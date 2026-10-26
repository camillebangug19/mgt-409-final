import { useEffect, useState } from 'react'
import { fetchUsage } from '../api'
import type { UsageSummary } from '../types'

/** What this session cost to run (REQUIREMENTS.md 8). Collapsed by default. */
export function CostPanel({ sessionId, refreshKey }: { sessionId: string; refreshKey: number }) {
  const [usage, setUsage] = useState<UsageSummary | null>(null)
  const [open, setOpen] = useState(false)

  useEffect(() => {
    if (!open) return
    fetchUsage(sessionId).then(setUsage).catch(() => setUsage(null))
  }, [sessionId, open, refreshKey])

  const money = (n: number) => (n < 0.01 ? `$${n.toFixed(4)}` : `$${n.toFixed(2)}`)

  return (
    <section className="cost-panel">
      <button className="cost-toggle" aria-expanded={open} onClick={() => setOpen((v) => !v)}>
        {open ? '▾' : '▸'} What did this cost to run?
      </button>

      {open && !usage && <p className="muted">Adding it up…</p>}

      {open && usage && (
        <div className="cost-body">
          <table className="cost-table">
            <caption className="muted">Tokens used by each agent in this session</caption>
            <thead>
              <tr>
                <th scope="col">Agent</th>
                <th scope="col">Input</th>
                <th scope="col">Cached</th>
                <th scope="col">Output</th>
                <th scope="col">Est. cost</th>
              </tr>
            </thead>
            <tbody>
              {usage.agents.map((row) => (
                <tr key={row.agent}>
                  <th scope="row">{row.agent.replace('_', ' ')}</th>
                  <td>{row.input_tokens.toLocaleString()}</td>
                  <td>{row.cached_tokens.toLocaleString()}</td>
                  <td>{row.output_tokens.toLocaleString()}</td>
                  <td>{money(row.cost_usd)}</td>
                </tr>
              ))}
              {usage.agents.length === 0 && (
                <tr>
                  <td colSpan={5} className="muted">
                    Nothing recorded yet.
                  </td>
                </tr>
              )}
            </tbody>
            <tfoot>
              <tr>
                <th scope="row">Total</th>
                <td>{usage.totals.input_tokens.toLocaleString()}</td>
                <td>{usage.totals.cached_tokens.toLocaleString()}</td>
                <td>{usage.totals.output_tokens.toLocaleString()}</td>
                <td>{money(usage.totals.cost_usd)}</td>
              </tr>
            </tfoot>
          </table>

          <p className="muted">
            At one session per user per month: <strong>{money(usage.projections.per_100_users)}</strong>{' '}
            for 100 users, <strong>{money(usage.projections.per_10000_users)}</strong> for 10,000.
          </p>
          <p className="muted">
            Model: {usage.model}. Token counts are measured.{' '}
            {usage.rates.are_estimates && 'Dollar rates are an estimate — see pricing.py.'}
          </p>
        </div>
      )}
    </section>
  )
}
