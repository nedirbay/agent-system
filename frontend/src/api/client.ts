/**
 * Thin fetch wrapper around the backend REST API.
 *
 * - Base URL comes from `VITE_API_BASE` (defaults to the local dev backend).
 * - The stored JWT is attached as a Bearer token on every request, so the UI
 *   is ready the moment the backend turns on its auth guards.
 * - Backend errors (`{ error: { code, message } }`) and FastAPI validation
 *   errors (`{ detail }`) are normalised into a single `ApiError`.
 */

const BASE_URL =
  (import.meta.env.VITE_API_BASE as string | undefined) ??
  'http://localhost:8000/api/v1'

const TOKEN_KEY = 'agentos-token'

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string | null): void {
  if (token) localStorage.setItem(TOKEN_KEY, token)
  else localStorage.removeItem(TOKEN_KEY)
}

export class ApiError extends Error {
  status: number
  code?: string

  constructor(status: number, message: string, code?: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
  }
}

interface RequestOptions {
  method?: string
  body?: unknown
  query?: Record<string, string | number | boolean | undefined>
  form?: FormData
}

function buildQuery(query?: RequestOptions['query']): string {
  if (!query) return ''
  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(query)) {
    if (value !== undefined) params.append(key, String(value))
  }
  const qs = params.toString()
  return qs ? `?${qs}` : ''
}

export async function request<T>(
  path: string,
  opts: RequestOptions = {},
): Promise<T> {
  const { method = 'GET', body, query, form } = opts
  const headers: Record<string, string> = {}

  const token = getToken()
  if (token) headers['Authorization'] = `Bearer ${token}`

  let payload: BodyInit | undefined
  if (form) {
    payload = form // let the browser set the multipart boundary
  } else if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
    payload = JSON.stringify(body)
  }

  let res: Response
  try {
    res = await fetch(`${BASE_URL}${path}${buildQuery(query)}`, {
      method,
      headers,
      body: payload,
    })
  } catch {
    throw new ApiError(0, 'Cannot reach the API server. Is the backend running?')
  }

  if (!res.ok) {
    let message = res.statusText
    let code: string | undefined
    try {
      const data = await res.json()
      message = data?.error?.message ?? data?.detail ?? message
      code = data?.error?.code
      if (Array.isArray(data?.detail) && data.detail[0]?.msg) {
        message = data.detail[0].msg
      }
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(res.status, message, code)
  }

  if (res.status === 204) return undefined as T
  const contentType = res.headers.get('content-type') ?? ''
  return contentType.includes('application/json')
    ? ((await res.json()) as T)
    : (undefined as T)
}

/**
 * POST a JSON body and consume a Server-Sent Events stream, invoking `onEvent`
 * for every `data: {json}` line as it arrives. Resolves when the stream closes.
 * Used for real-time workflow execution (`EventSource` can't POST or send the
 * Authorization header, so we read the stream off `fetch` directly).
 */
export async function streamRequest<E>(
  path: string,
  body: unknown,
  onEvent: (event: E) => void,
  signal?: AbortSignal,
): Promise<void> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  const token = getToken()
  if (token) headers['Authorization'] = `Bearer ${token}`

  let res: Response
  try {
    res = await fetch(`${BASE_URL}${path}`, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
      signal,
    })
  } catch {
    throw new ApiError(0, 'Cannot reach the API server. Is the backend running?')
  }

  if (!res.ok || !res.body) {
    throw new ApiError(res.status || 0, res.statusText || 'Stream failed')
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  for (;;) {
    const { value, done } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    // SSE frames are separated by a blank line.
    let sep: number
    while ((sep = buffer.indexOf('\n\n')) !== -1) {
      const frame = buffer.slice(0, sep)
      buffer = buffer.slice(sep + 2)
      for (const line of frame.split('\n')) {
        const trimmed = line.trimStart()
        if (!trimmed.startsWith('data:')) continue
        const payload = trimmed.slice(5).trim()
        if (!payload) continue
        try {
          onEvent(JSON.parse(payload) as E)
        } catch {
          /* ignore malformed frame */
        }
      }
    }
  }
}
