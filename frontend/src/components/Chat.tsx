import { useEffect, useRef, useState } from 'react'
import { sendMessage } from '../api'
import type { ChatTurn, Message } from '../types'
import { ProgressStrip } from './ProgressStrip'

const MAX_CHARS = 500

type Props = {
  sessionId: string
  onDone: (turn: ChatTurn) => void
}

export function Chat({ sessionId, onDone }: Props) {
  const [messages, setMessages] = useState<Message[]>([])
  const [turn, setTurn] = useState<ChatTurn | null>(null)
  const [draft, setDraft] = useState('')
  const [thinking, setThinking] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const started = useRef(false)
  const logEnd = useRef<HTMLDivElement>(null)

  async function send(text: string) {
    setError(null)
    setThinking(true)
    if (text) setMessages((previous) => [...previous, { role: 'user', text }])
    try {
      const next = await sendMessage(sessionId, text)
      setMessages((previous) => [...previous, { role: 'bot', text: next.message }])
      setTurn(next)
      if (next.done) onDone(next)
    } catch {
      setError('Something went wrong reaching the server. Try again.')
    } finally {
      setThinking(false)
    }
  }

  // Kick off the conversation once.
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

  const answered = turn ? `${turn.filled} of ${turn.total} answered` : ''

  return (
    <main>
      <ProgressStrip sections={turn?.sections ?? []} activeIndex={turn?.section_index ?? 0} />

      <section className="chat">
        <div className="log" role="log" aria-live="polite" aria-label="Survey conversation">
          {messages.map((message, index) => (
            <div key={index} className={`bubble ${message.role}`}>
              {message.text}
            </div>
          ))}
          {thinking && (
            <div className="bubble bot" aria-label="ReadyHome is thinking">
              <span className="typing" aria-hidden="true">
                <span />
                <span />
                <span />
              </span>
            </div>
          )}
          <div ref={logEnd} />
        </div>

        {turn && turn.quick_replies.length > 0 && !thinking && (
          <div className="chips">
            {turn.quick_replies.map((reply) => (
              <button key={reply} onClick={() => void send(reply)}>
                {reply}
              </button>
            ))}
          </div>
        )}

        <form className="composer" onSubmit={submit}>
          <label htmlFor="answer" className="sr-only" style={{ position: 'absolute', left: '-9999px' }}>
            Your answer
          </label>
          <input
            id="answer"
            value={draft}
            maxLength={MAX_CHARS}
            placeholder="Type your answer…"
            onChange={(event) => setDraft(event.target.value)}
            disabled={thinking}
            autoComplete="off"
          />
          <button type="submit" className="primary" disabled={thinking || !draft.trim()}>
            Send
          </button>
        </form>

        {error && <p className="error">{error}</p>}
        <p className="muted" style={{ marginTop: '0.7rem', marginBottom: 0 }}>
          {answered}
        </p>
      </section>

      <p className="disclaimer">
        Not medical advice. Ask your doctor or pharmacist about medications and medical devices.
      </p>
    </main>
  )
}
