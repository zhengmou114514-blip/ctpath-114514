import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import type { AuthSession, DoctorUser } from '../services/types'

export const AUTH_STORAGE_KEY = 'ctpath.auth.session'

function isValidDoctorUser(value: unknown): value is DoctorUser {
  if (!value || typeof value !== 'object') return false

  const doctor = value as Partial<DoctorUser>
  return (
    typeof doctor.username === 'string' &&
    doctor.username.length > 0 &&
    typeof doctor.name === 'string' &&
    doctor.name.length > 0 &&
    (doctor.role === 'doctor' || doctor.role === 'nurse' || doctor.role === 'archivist')
  )
}

function isValidAuthSession(value: unknown): value is AuthSession {
  if (!value || typeof value !== 'object') return false

  const session = value as Partial<AuthSession>
  return typeof session.token === 'string' && session.token.length > 0 && isValidDoctorUser(session.doctor)
}

export function readStoredAuthSession(): AuthSession | null {
  try {
    if (typeof window === 'undefined' || !window.localStorage) return null
    const raw = window.localStorage.getItem(AUTH_STORAGE_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw) as unknown
    if (!isValidAuthSession(parsed)) {
      window.localStorage.removeItem(AUTH_STORAGE_KEY)
      return null
    }
    return parsed
  } catch {
    return null
  }
}

export function persistAuthSession(session: AuthSession | null): void {
  try {
    if (typeof window === 'undefined' || !window.localStorage) return
    if (session) {
      window.localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(session))
      return
    }
    window.localStorage.removeItem(AUTH_STORAGE_KEY)
  } catch {
    // Best-effort local persistence only.
  }
}

export function readStoredAuthToken(): string {
  return readStoredAuthSession()?.token ?? ''
}

export const useAuthStore = defineStore('auth', () => {
  const session = ref<AuthSession | null>(readStoredAuthSession())

  const token = computed(() => session.value?.token ?? '')
  const doctor = computed<DoctorUser | null>(() => session.value?.doctor ?? null)
  const isAuthenticated = computed(() => Boolean(session.value?.token && session.value?.doctor?.username && session.value?.doctor?.role))

  function setSession(nextSession: AuthSession | null) {
    session.value = nextSession
    persistAuthSession(nextSession)
  }

  function restoreSession() {
    session.value = readStoredAuthSession()
    return session.value
  }

  function clearSession() {
    session.value = null
    persistAuthSession(null)
  }

  return {
    session,
    token,
    doctor,
    isAuthenticated,
    setSession,
    restoreSession,
    clearSession,
  }
})
