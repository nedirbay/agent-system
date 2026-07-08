/** Typed backend API surface used by the app views. */
import { request, streamRequest } from './client'
import type {
  AgentRecord,
  AgentSpec,
  ConnectorConnection,
  ConnectorSpec,
  DocumentRecord,
  ParseResult,
  QaAnswer,
  RegisterPayload,
  TokenResponse,
  User,
  WorkflowEvent,
  WorkflowRecord,
} from './types'

export * from './types'
export { ApiError, getToken, setToken } from './client'

// --- Auth (Frontend → Backend connection) ---

export const authApi = {
  login: (username: string, password: string) =>
    request<TokenResponse>('/auth/login', {
      method: 'POST',
      body: { username, password },
    }),
  register: (payload: RegisterPayload) =>
    request<User>('/auth/register', { method: 'POST', body: payload }),
  listUsers: () => request<User[]>('/auth/users', { query: { limit: 100 } }),
}

// --- Chat / Q&A (Task 24) ---

export const qaApi = {
  ask: (question: string, opts: { top_k?: number; document_id?: string } = {}) =>
    request<QaAnswer>('/qa/ask', {
      method: 'POST',
      body: {
        question,
        top_k: opts.top_k ?? 5,
        document_id: opts.document_id ?? null,
      },
    }),
}

// --- Documents / Workspace (Task 25) ---

export const documentsApi = {
  list: (limit = 100) =>
    request<DocumentRecord[]>('/documents', { query: { limit } }),
  get: (id: string) => request<DocumentRecord>(`/documents/${id}`),
  upload: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return request<DocumentRecord>('/documents/upload', { method: 'POST', form })
  },
  parse: (id: string) =>
    request<ParseResult>(`/documents/${id}/parse`, { method: 'POST' }),
}

// --- Dashboard (Task 26) ---

export const dashboardApi = {
  agents: () => request<AgentRecord[]>('/agents', { query: { limit: 100 } }),
  workflows: () =>
    request<WorkflowRecord[]>('/workflows', { query: { limit: 100 } }),
}

// --- Multi-agent task execution (real-time orchestration) ---

export const workflowsApi = {
  /** Submit a task and stream each agent step as it runs (SSE). */
  runStream: (
    requestText: string,
    onEvent: (event: WorkflowEvent) => void,
    opts: { context?: Record<string, unknown>; signal?: AbortSignal } = {},
  ) =>
    streamRequest<WorkflowEvent>(
      '/workflows/run/stream',
      { request: requestText, context: opts.context ?? {} },
      onEvent,
      opts.signal,
    ),
}

// --- Agent registry catalogue ---

export const agentsApi = {
  /** The catalogue of agent types the orchestrator can plan and route to. */
  registry: () => request<AgentSpec[]>('/agents/registry'),
}

// --- Connectors (external systems / MCP integrations) ---

export const connectorsApi = {
  /** Catalogue of external systems available to connect. */
  catalog: () => request<ConnectorSpec[]>('/connectors/catalog'),
  /** The current user's stored connections (no plaintext secrets). */
  list: () => request<ConnectorConnection[]>('/connectors'),
  /** Add a connection; `values` holds the submitted field values (incl. secrets). */
  add: (connector_type: string, label: string | null, values: Record<string, unknown>) =>
    request<ConnectorConnection>('/connectors', {
      method: 'POST',
      body: { connector_type, label, values },
    }),
  remove: (id: string) => request<void>(`/connectors/${id}`, { method: 'DELETE' }),
}
