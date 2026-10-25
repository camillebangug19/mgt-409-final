import { useState } from 'react'
import { clearSession, getSessionId } from './api'
import { Chat } from './components/Chat'
import { Landing } from './components/Landing'
import { ScoreReveal } from './components/ScoreReveal'

type Screen = 'landing' | 'survey' | 'score'

export default function App() {
  const [screen, setScreen] = useState<Screen>('landing')
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [starting, setStarting] = useState(false)
  const [error, setError] = useState<string | null>(null)

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

  function restart() {
    clearSession()
    setSessionId(null)
    setScreen('landing')
  }

  if (screen === 'landing' || !sessionId) {
    return (
      <>
        <Landing onStart={() => void start()} starting={starting} />
        {error && <p className="error">{error}</p>}
      </>
    )
  }

  if (screen === 'survey') {
    return <Chat sessionId={sessionId} onDone={() => setScreen('score')} />
  }

  return <ScoreReveal sessionId={sessionId} onRestart={restart} />
}
