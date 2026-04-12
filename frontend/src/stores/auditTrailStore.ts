import { computed, reactive } from 'vue'
import type { AuditActor, AuditLogCreateInput, AuditLogEntry } from '../audit/types'

const STORAGE_KEY = 'ctpath.audit.logs'
const AUTH_STORAGE_KEY = 'ctpath.auth.session'
const MAX_LOGS = 500

const state = reactive<{ logs: AuditLogEntry[]; loaded: boolean }>({
  logs: [],
  loaded: false,
})

function loadLogs() {
  if (state.loaded) return
  state.loaded = true
  try {
    const raw = window?.localStorage?.getItem(STORAGE_KEY)
    if (!raw) return
    const parsed = JSON.parse(raw) as AuditLogEntry[]
    state.logs = Array.isArray(parsed) ? parsed : []
  } catch {
    state.logs = []
  }
}

function persistLogs() {
  try {
    window?.localStorage?.setItem(STORAGE_KEY, JSON.stringify(state.logs.slice(0, MAX_LOGS)))
  } catch {
    // ignore localStorage failures
  }
}

function resolveActor(actor?: Partial<AuditActor>): AuditActor {
  if (actor?.username || actor?.name) {
    return {
      username: actor.username || 'unknown',
      name: actor.name || actor.username || 'Unknown User',
      role: actor.role || 'unknown',
    }
  }

  try {
    const raw = window?.localStorage?.getItem(AUTH_STORAGE_KEY)
    if (!raw) throw new Error('missing auth')
    const parsed = JSON.parse(raw) as { doctor?: { username?: string; name?: string; role?: AuditActor['role'] } }
    const doctor = parsed?.doctor
    return {
      username: doctor?.username || 'unknown',
      name: doctor?.name || doctor?.username || 'Unknown User',
      role: doctor?.role || 'unknown',
    }
  } catch {
    return {
      username: 'unknown',
      name: 'Unknown User',
      role: 'unknown',
    }
  }
}

function addAuditLog(input: AuditLogCreateInput): AuditLogEntry {
  loadLogs()
  const entry: AuditLogEntry = {
    id: `audit-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    actor: resolveActor(input.actor),
    action: input.action,
    target: input.target,
    time: input.time || new Date().toISOString(),
    result: input.result,
    detail: input.detail,
  }
  state.logs.unshift(entry)
  if (state.logs.length > MAX_LOGS) {
    state.logs = state.logs.slice(0, MAX_LOGS)
  }
  persistLogs()
  return entry
}

function clearAuditLogs() {
  state.logs = []
  persistLogs()
}

export function useAuditTrailStore() {
  loadLogs()

  const recentLogs = computed(() => state.logs)

  function getRecent(limit = 20): AuditLogEntry[] {
    return recentLogs.value.slice(0, limit)
  }

  return {
    logs: recentLogs,
    getRecent,
    addAuditLog,
    clearAuditLogs,
  }
}