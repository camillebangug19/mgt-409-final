import { useEffect, useState } from 'react'
import { clearSession, getSessionId, getSessionStatus, savedSessionId } from './api'
import { Chat } from './components/Chat'
import { Landing } from './components/Landing'
import { ScoreReveal } from './components/ScoreReveal'
import type { SessionStatus } from './types'

type Screen = 'landing' | 'survey' | 'score'

export default function App() {
  const [screen, setScreen] = useState<Screen>('landing')
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [returning, setReturning] = useState<SessionStatus | null>(null)
  const [starting, setStarting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // No accounts: the browser remembers an anonymous id, and the server
  // remembers what that id answered.
  useEffect(() => {
    void getSessionStatus().then(setReturning)
  }, [])

  async function start() {
    setStarting(true)
    setError(null)
    try {
      setSessionId(await getSessionId())
      setScreen('survey')
    } catch {
      setError('Could not reach the server. Is the backend running on port 8000?')
    } finally {
      setStarting(false)
    }
  }

  function resume() {
    const saved = savedSessionId()
    if (!saved) return void start()
    setSessionId(saved)
    setScreen(returning?.survey_done ? 'score' : 'survey')
  }

  async function startFresh() {
    clearSession()
    setReturning(null)
    setSessionId(null)
    await start()
  }

  function restart() {
    clearSession()
    setReturning(null)
    setSessionId(null)
    setScreen('landing')
  }

  if (screen === 'landing' || !sessionId) {
    return (
      <>
        <Landing
          onStart={() => void startFresh()}
          onResume={resume}
          onFresh={() => void startFresh()}
          starting={starting}
          returning={returning}
        />
        {error && <p className="error">{error}</p>}
      </>
    )
  }

  if (screen === 'survey') {
    return <Chat sessionId={sessionId} onDone={() => setScreen('score')} />
  }

  return <ScoreReveal sessionId={sessionId} onRestart={restart} />
}
