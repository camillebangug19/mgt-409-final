import type { ChatTurn, Plan, SessionStatus, UsageSummary } from './types'

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

/** What we remember about this browser, if anything. */
export async function getSessionStatus(): Promise<SessionStatus | null> {
  const saved = localStorage.getItem(SESSION_KEY)
  if (!saved) return null
  try {
    const response = await fetch(`${BASE}/api/session/${encodeURIComponent(saved)}`)
    if (!response.ok) return null
    const status = (await response.json()) as SessionStatus
    if (!status.found) {
      localStorage.removeItem(SESSION_KEY)
      return null
    }
    return status
  } catch {
    return null
  }
}

export function savedSessionId(): string | null {
  return localStorage.getItem(SESSION_KEY)
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

export async function fetchPlan(sessionId: string): Promise<Plan> {
  const response = await fetch(`${BASE}/api/plan?session_id=${encodeURIComponent(sessionId)}`)
  if (!response.ok) throw new Error(`/api/plan failed (${response.status})`)
  return response.json() as Promise<Plan>
}

export function completeStep(sessionId: string, stepId: string, checked: string[]) {
  return post<Plan>(`/api/steps/${encodeURIComponent(stepId)}/complete`, {
    session_id: sessionId,
    checked,
  })
}

export async function fetchUsage(sessionId: string): Promise<UsageSummary> {
  const response = await fetch(`${BASE}/api/usage?session_id=${encodeURIComponent(sessionId)}`)
  if (!response.ok) throw new Error(`/api/usage failed (${response.status})`)
  return response.json() as Promise<UsageSummary>
}
