import axios, { AxiosError, type AxiosInstance, type AxiosRequestConfig, type AxiosRequestHeaders, type AxiosResponse } from 'axios'
import { readStoredAuthSession, persistAuthSession } from '../stores/auth'

const API_BASE = '/api'
const HANDLED_ERROR_STATUSES = new Set([401, 403, 429, 500])

function normalizeApiPath(path: string): string {
  if (!path) return '/'

  let normalized = path
  try {
    const origin = typeof window !== 'undefined' ? window.location.origin : 'http://localhost'
    const parsed = new URL(path, origin)
    normalized = `${parsed.pathname}${parsed.search}${parsed.hash}`
  } catch {
    normalized = path
  }

  if (normalized === API_BASE) return '/'
  if (normalized.startsWith(`${API_BASE}/`)) {
    normalized = normalized.slice(API_BASE.length)
  } else if (normalized === '/api') {
    normalized = '/'
  } else if (normalized.startsWith('/api/')) {
    normalized = normalized.slice('/api'.length)
  }

  if (!normalized.startsWith('/')) {
    normalized = `/${normalized}`
  }

  return normalized
}

function buildTraceId(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID()
  }
  return `trace_${Date.now()}_${Math.random().toString(16).slice(2)}`
}

function normalizeHeaders(headers?: HeadersInit): Record<string, string> {
  const normalized: Record<string, string> = {}
  if (!headers) return normalized
  if (headers instanceof Headers) {
    headers.forEach((value, key) => {
      normalized[key] = value
    })
    return normalized
  }
  if (Array.isArray(headers)) {
    for (const [key, value] of headers) {
      normalized[String(key)] = String(value)
    }
    return normalized
  }
  for (const [key, value] of Object.entries(headers)) {
    normalized[key] = String(value)
  }
  return normalized
}

function isApiUrl(input: RequestInfo | URL): boolean {
  const raw = typeof input === 'string' ? input : input instanceof URL ? input.toString() : input.url
  if (!raw) return false
  try {
    const resolved = new URL(raw, window.location.origin)
    return resolved.pathname.startsWith('/api') || raw.startsWith(API_BASE)
  } catch {
    return raw.startsWith('/api') || raw.startsWith(API_BASE)
  }
}

function isAuthEndpoint(url?: string): boolean {
  if (!url) return false
  return url.includes('/login') || url.includes('/register')
}

function emitHttpStatus(status: number, traceId: string, url?: string) {
  if (typeof window === 'undefined') return
  window.dispatchEvent(
    new CustomEvent('ctpath:http-status', {
      detail: { status, traceId, url: url ?? '' },
    })
  )
}

const originalFetch = typeof window !== 'undefined' && typeof window.fetch === 'function' ? window.fetch.bind(window) : null

const requestClient: AxiosInstance = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  withCredentials: true,
  validateStatus: () => true,
})

requestClient.interceptors.request.use((config) => {
  config.url = normalizeApiPath(String(config.url ?? ''))
  const session = readStoredAuthSession()
  const headers = normalizeHeaders(config.headers as HeadersInit | undefined)
  const traceId = headers['X-Trace-Id'] || headers['x-trace-id'] || buildTraceId()

  headers['X-Trace-Id'] = traceId
  if (session?.token && !headers.Authorization && !headers.authorization) {
    headers.Authorization = `Bearer ${session.token}`
  }

  if (
    config.data &&
    !headers['Content-Type'] &&
    !headers['content-type'] &&
    !(config.data instanceof FormData) &&
    !(config.data instanceof URLSearchParams)
  ) {
    headers['Content-Type'] = 'application/json'
  }

  config.headers = headers as AxiosRequestHeaders
  ;(config as AxiosRequestConfig & { _traceId?: string })._traceId = traceId
  return config
})

requestClient.interceptors.response.use(
  (response: AxiosResponse) => {
    const traceId =
      String(response.headers?.['x-trace-id'] ?? response.headers?.['X-Trace-Id'] ?? (response.config as AxiosRequestConfig & { _traceId?: string })._traceId ?? '')
    if (response.status === 401 && !isAuthEndpoint(response.config.url)) {
      persistAuthSession(null)
    }
    if (HANDLED_ERROR_STATUSES.has(response.status)) {
      emitHttpStatus(response.status, traceId, response.config.url)
    }
    return response
  },
  (error) => {
    const axiosError = error as AxiosError
    const status = axiosError.response?.status ?? 500
    const traceId =
      String(axiosError.response?.headers?.['x-trace-id'] ?? axiosError.response?.headers?.['X-Trace-Id'] ?? (axiosError.config as AxiosRequestConfig & { _traceId?: string } | undefined)?._traceId ?? buildTraceId())

    if (status === 401 && !isAuthEndpoint(axiosError.config?.url)) {
      persistAuthSession(null)
    }
    if (HANDLED_ERROR_STATUSES.has(status)) {
      emitHttpStatus(status, traceId, axiosError.config?.url)
    }
    return Promise.reject(error)
  }
)

function toResponse(response: AxiosResponse): Response {
  const headers = new Headers()
  Object.entries(response.headers ?? {}).forEach(([key, value]) => {
    if (Array.isArray(value)) {
      headers.set(key, value.join(', '))
    } else if (value !== undefined && value !== null) {
      headers.set(key, String(value))
    }
  })

  const payload =
    typeof response.data === 'string'
      ? response.data
      : response.data == null
        ? ''
        : JSON.stringify(response.data)

  if (!headers.has('content-type')) {
    headers.set('content-type', typeof response.data === 'string' ? 'text/plain; charset=utf-8' : 'application/json; charset=utf-8')
  }

  return new Response(payload, {
    status: response.status,
    statusText: response.statusText,
    headers,
  })
}

async function bridgeFetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  if (!isApiUrl(input)) {
    if (!originalFetch) {
      throw new TypeError('Failed to fetch')
    }
    return originalFetch(input as RequestInfo | URL, init)
  }

  const request = input instanceof Request ? input.clone() : null
  const method = (init?.method ?? request?.method ?? 'GET').toUpperCase()
  const headers = normalizeHeaders(init?.headers ?? request?.headers)
  const traceId = headers['X-Trace-Id'] || headers['x-trace-id'] || buildTraceId()
  headers['X-Trace-Id'] = traceId

  const config: AxiosRequestConfig = {
    url: normalizeApiPath(input instanceof URL ? input.toString() : input instanceof Request ? input.url : input),
    method,
    headers,
    data: init?.body ?? (request ? await request.text() : undefined),
    responseType: 'text',
    validateStatus: () => true,
    transformResponse: [(data) => data],
  }

  try {
    const response = await requestClient.request(config)
    return toResponse(response)
  } catch (error) {
    emitHttpStatus(500, traceId, typeof input === 'string' ? input : input.toString())
    throw new TypeError('Failed to fetch')
  }
}

if (typeof window !== 'undefined' && typeof window.fetch === 'function') {
  window.fetch = bridgeFetch as typeof window.fetch
}

export { requestClient }
