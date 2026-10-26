import { useEffect, useRef, useState } from 'react'
import { searchStates } from '../states'

type Props = {
  onPick: (abbr: string, name: string) => void
  disabled: boolean
}

/**
 * Type to narrow, then pick. Sends the two-letter abbreviation, so the survey
 * always gets a valid state and nobody has to guess the format.
 */
export function StatePicker({ onPick, disabled }: Props) {
  const [query, setQuery] = useState('')
  const [highlight, setHighlight] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)
  const matches = searchStates(query).slice(0, 60)

  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  useEffect(() => {
    setHighlight(0)
  }, [query])

  function choose(index: number) {
    const match = matches[index]
    if (match) onPick(match.abbr, match.name)
  }

  function onKeyDown(event: React.KeyboardEvent) {
    if (event.key === 'ArrowDown') {
      event.preventDefault()
      setHighlight((h) => Math.min(h + 1, matches.length - 1))
    } else if (event.key === 'ArrowUp') {
      event.preventDefault()
      setHighlight((h) => Math.max(h - 1, 0))
    } else if (event.key === 'Enter') {
      event.preventDefault()
      choose(highlight)
    }
  }

  return (
    <div className="state-picker">
      <label htmlFor="state-search" className="muted">
        Start typing your state, then pick it from the list
      </label>
      <input
        id="state-search"
        ref={inputRef}
        value={query}
        disabled={disabled}
        placeholder="e.g. Texas"
        autoComplete="off"
        role="combobox"
        aria-expanded="true"
        aria-controls="state-options"
        aria-autocomplete="list"
        onChange={(event) => setQuery(event.target.value)}
        onKeyDown={onKeyDown}
      />
      {matches.length === 0 ? (
        <p className="muted" style={{ marginTop: '0.5rem' }}>
          No state matches “{query}”.
        </p>
      ) : (
        <ul className="state-list" id="state-options" role="listbox">
          {matches.map((state, index) => (
            <li key={state.abbr} role="option" aria-selected={index === highlight}>
              <button
                type="button"
                className={index === highlight ? 'active' : undefined}
                disabled={disabled}
                onMouseEnter={() => setHighlight(index)}
                onClick={() => choose(index)}
              >
                {state.name}
                <span className="abbr">{state.abbr}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
