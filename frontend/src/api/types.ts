/**
 * TypeScript projections of the backend Pydantic schemas (the
 * presentation/schemas.py modules). Kept intentionally narrow — only
 * the fields the UI consumes.
 */

export interface TokenResponse {
  access_token: string
  token_type: string
}

export interface User {
  id: string
  created_at: string
  username: string | null
  email: string | null
  full_name: string | null
  status: string | null
}

export interface RegisterPayload {
  username: string
  password: string
  email?: string | null
  full_name?: string | null
}

export interface QaCitation {
  index: number
  chunk_id: string
  document_id: string | null
  chunk_index: number | null
  page: number | null
  score: number
  snippet: string
}

export interface QaAnswer {
  question: string
  answer: string
  grounded: boolean
  llm_used: boolean
  citations: QaCitation[]
}

export interface DocumentRecord {
  id: string
  created_at: string
  user_id: string | null
  file_name: string | null
  mime_type: string | null
  size: number | null
  storage_path: string | null
  status: string | null
  page_count: number | null
  doc_metadata: Record<string, unknown> | null
}

export interface ParseResult {
  id: string
  status: string | null
  page_count: number | null
  char_count: number
  ocr_used: boolean
  doc_metadata: Record<string, unknown> | null
  text_preview: string
}

export interface AgentRecord {
  id: string
  created_at: string
  name: string | null
  agent_type: string | null
  status: string | null
}

/** An agent type in the registry catalogue (GET /agents/registry). */
export interface AgentSpec {
  type: string
  description: string
  task_class: string
  tier: string
  capabilities: string[]
  requires_approval: boolean
}

// --- Connectors (external systems / MCP integrations) ---

export interface ConnectorField {
  key: string
  label: string
  kind: 'text' | 'secret'
  required: boolean
  placeholder?: string
  help?: string
}

/** An available external system to connect (GET /connectors/catalog). */
export interface ConnectorSpec {
  type: string
  name: string
  description: string
  category: string
  icon: string
  docs_url?: string
  fields: ConnectorField[]
}

/** A user's stored connection. Never carries a plaintext secret. */
export interface ConnectorConnection {
  id: string
  created_at: string
  connector_type: string
  label: string
  status: string
  config: Record<string, unknown>
  secret_hint: string | null
  has_secret: boolean
}

export interface WorkflowRecord {
  id: string
  created_at: string
  name: string | null
  status: string | null
}

// --- Real-time workflow execution events (SSE from /workflows/run/stream) ---

export interface PlanStep {
  order: number
  agent_type: string
  objective: string
  requires_approval: boolean
}

export type WorkflowEvent =
  | { type: 'planning'; request: string }
  | {
      type: 'plan'
      instance_id: string
      summary: string
      fallback: boolean
      steps: PlanStep[]
    }
  | { type: 'step_started'; order: number; agent_type: string; objective: string }
  | {
      type: 'step_completed'
      order: number
      agent_type: string
      attempts: number
      executed_by: string
      result: string
    }
  | {
      type: 'step_failed'
      order: number
      agent_type: string
      attempts: number
      error: string | null
    }
  | { type: 'awaiting_approval'; order: number; agent_type: string; objective: string }
  | { type: 'completed'; instance_id: string; status: string }
  | { type: 'failed'; instance_id: string; status: string }
  | { type: 'error'; message: string }
