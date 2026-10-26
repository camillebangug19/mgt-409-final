import { useEffect, useRef, useState } from 'react'
import { sendMessage } from '../api'
import type { ChatTurn, Message } from '../types'
import { ProgressStrip } from './ProgressStrip'
import { StatePicker } from './StatePicker'
import { Sunny } from './Sunny'

const MAX_CHARS = 500
const OTHER = 'Something different'

type Props = {
  sessionId: string
  onDone: (turn: ChatTurn) => void
}

export function Chat({ sessionId, onDone }: Props) {
  const [messages, setMessages] = useState<Message[]>([])
  const [turn, setTurn] = useState<ChatTurn | null>(null)
  const [draft, setDraft] = useState('')
  const [freeText, setFreeText] = useState(false)
  const [thinking, setThinking] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const started = useRef(false)
  const logEnd = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  async function send(text: string) {
    setError(null)
    setThinking(true)
    setFreeText(false)
    if (text) setMessages((previous) => [...previous, { role: 'user', text }])
    try {
      const next = await sendMessage(sessionId, text)
      setMessages((previous) => [...previous, { role: 'bot', text: next.message, mood: next.mood }])
      setTurn(next)
      if (next.done) onDone(next)
    } catch {
      setError('Something went wrong reaching the server. Try that again.')
    } finally {
      setThinking(false)
    }
  }

  useEffect(() => {
    if (started.current) return
    started.current = true
    void send('')
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    logEnd.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages, thinking])

  function submit(event: React.FormEvent) {
    event.preventDefault()
    const text = draft.trim()
    if (!text || thinking) return
    setDraft('')
    void send(text)
  }

  function openFreeText() {
    setFreeText(true)
    window.setTimeout(() => inputRef.current?.focus(), 0)
  }

  const askingState = turn?.next_slot === 'state'
  const showChips = !!turn && turn.quick_replies.length > 0 && !thinking && !freeText && !askingState
  const pct = turn ? Math.round(turn.progress * 100) : 0

  return (
    <main>
      <ProgressStrip sections={turn?.sections ?? []} activeIndex={turn?.section_index ?? 0} />

      <section className="chat">
        <div className="log" role="log" aria-live="polite" aria-label="Survey conversation">
          {messages.map((message, index) =>
            message.role === 'bot' ? (
              <div className="bot-row" key={index}>
                <Sunny mood={message.mood ?? 'hi'} size={40} />
                <div className="bubble bot">{message.text}</div>
              </div>
            ) : (
              <div key={index} className="bubble user">
                {message.text}
              </div>
            ),
          )}
          {thinking && (
            <div className="bot-row" aria-label="Sunny is thinking">
              <Sunny mood="thinking" size={40} />
              <div className="bubble bot">
                <span className="typing" aria-hidden="true">
                  <span />
                  <span />
                  <span />
                </span>
              </div>
            </div>
          )}
          <div ref={logEnd} />
        </div>

        {askingState && !thinking && (
          <StatePicker disabled={thinking} onPick={(abbr, name) => void send(`${name} (${abbr})`)} />
        )}

        {showChips && (
          <div className="chips">
            {turn!.quick_replies.map((reply) => (
              <button key={reply} onClick={() => void send(reply)}>
                {reply}
              </button>
            ))}
            <button className="other" onClick={openFreeText}>
              {OTHER}…
            </button>
          </div>
        )}

        {(freeText || !showChips) && !askingState && (
          <form className="composer" onSubmit={submit}>
            <label htmlFor="answer" style={{ position: 'absolute', left: '-9999px' }}>
              Your answer
            </label>
            <input
              id="answer"
              ref={inputRef}
              value={draft}
              maxLength={MAX_CHARS}
              placeholder={freeText ? 'Describe your situation in your own words…' : 'Type your answer…'}
              onChange={(event) => setDraft(event.target.value)}
              disabled={thinking}
              autoComplete="off"
            />
            <button type="submit" className="primary" disabled={thinking || !draft.trim()}>
              Send
            </button>
          </form>
        )}

        {freeText && (
          <button className="muted" style={{ marginTop: '0.5rem' }} onClick={() => setFreeText(false)}>
            ← Back to the quick answers
          </button>
        )}

        {error && <p className="error">{error}</p>}

        {turn && (
          <div className="answered-count">
            <div className="answered-bar">
              <div style={{ width: `${pct}%` }} />
            </div>
            <span className="muted">
              {turn.filled} of {turn.total}
            </span>
          </div>
        )}
      </section>

      <p className="disclaimer">
        Not medical advice. Ask your doctor or pharmacist about medications and medical devices.
      </p>
    </main>
  )
}
