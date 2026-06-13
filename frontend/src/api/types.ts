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

export interface WorkflowRecord {
  id: string
  created_at: string
  name: string | null
  status: string | null
}
