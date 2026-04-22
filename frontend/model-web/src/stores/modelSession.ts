import type { ModelUser } from '../services/modelApi'

const STORAGE_KEY = 'ctpath.model.session'

export interface ModelSession {
  token: string
  user: ModelUser
}

export function readStoredModelSession(): ModelSession | null {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw) as ModelSession
    if (!parsed?.token || !parsed?.user?.username) return null
    return parsed
  } catch {
    return null
  }
}

export function saveModelSession(session: ModelSession) {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(session))
}

export function clearModelSession() {
  window.localStorage.removeItem(STORAGE_KEY)
}
