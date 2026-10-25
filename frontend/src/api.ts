import type { ChatTurn } from './types'

// In production FastAPI serves this bundle, so the API is same-origin.
const BASE = import.meta.env.DEV ? 'http://localhost:8000' : ''
const SESSION_KEY = 'readyhome_session_id'

async function post<T>(path: string, body?: unknown): Promise<T> {
  const response = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!response.ok) {
    throw new Error(`${path} failed (${response.status})`)
  }
  return response.json() as Promise<T>
}

/** An anonymous session id, reused across reloads (REQUIREMENTS.md 6.4). */
export async function getSessionId(): Promise<string> {
  const saved = localStorage.getItem(SESSION_KEY)
  if (saved) return saved
  const { session_id } = await post<{ session_id: string }>('/api/session')
  localStorage.setItem(SESSION_KEY, session_id)
  return session_id
}

export function clearSession() {
  localStorage.removeItem(SESSION_KEY)
}

export function sendMessage(sessionId: string, message: string) {
  return post<ChatTurn>('/api/chat', { session_id: sessionId, message })
}
