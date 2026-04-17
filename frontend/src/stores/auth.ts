import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import type { AuthSession, DoctorUser } from '../services/types'

export const AUTH_STORAGE_KEY = 'ctpath.auth.session'

export function readStoredAuthSession(): AuthSession | null {
  try {
    if (typeof window === 'undefined' || !window.localStorage) return null
    const raw = window.localStorage.getItem(AUTH_STORAGE_KEY)
    if (!raw) return null
    return JSON.parse(raw) as AuthSession
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
  const isAuthenticated = computed(() => Boolean(session.value?.token))

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

