/**
 * Shared state machine for a live multi-agent run, plus agent display metadata.
 * Consumed by AgentsView (full timeline) and ChatView (inline orchestration),
 * so the event→state logic lives in exactly one place.
 */
import type { WorkflowEvent } from '@/api'

export type StepState = 'pending' | 'running' | 'completed' | 'failed' | 'awaiting'
export type Phase = 'idle' | 'planning' | 'running' | 'completed' | 'failed'

export interface LiveStep {
  order: number
  agent_type: string
  objective: string
  requires_approval: boolean
  status: StepState
  executed_by?: string
  result?: string
  attempts?: number
  error?: string | null
}

export interface RunState {
  phase: Phase
  summary: string
  fallback: boolean
  steps: LiveStep[]
  finalAnswer: string
  error: string
}

export function newRunState(): RunState {
  return { phase: 'idle', summary: '', fallback: false, steps: [], finalAnswer: '', error: '' }
}

/** Mutate `state` in place for one streamed event (works on a Vue reactive proxy). */
export function applyEvent(state: RunState, event: WorkflowEvent): void {
  switch (event.type) {
    case 'planning':
      state.phase = 'planning'
      break
    case 'plan':
      state.summary = event.summary
      state.fallback = event.fallback
      state.steps = event.steps.map((s): LiveStep => ({ ...s, status: 'pending' }))
      state.phase = 'running'
      break
    case 'step_started':
      patch(state, event.order, { status: 'running' })
      break
    case 'step_completed':
      patch(state, event.order, {
        status: 'completed',
        executed_by: event.executed_by,
        result: event.result,
        attempts: event.attempts,
      })
      break
    case 'step_failed':
      patch(state, event.order, { status: 'failed', error: event.error, attempts: event.attempts })
      break
    case 'awaiting_approval':
      patch(state, event.order, { status: 'awaiting' })
      break
    case 'completed':
      state.phase = 'completed'
      state.finalAnswer = deriveAnswer(state.steps)
      break
    case 'failed':
      state.phase = 'failed'
      break
    case 'error':
      state.error = event.message
      state.phase = 'failed'
      break
  }
}

function patch(state: RunState, order: number, partial: Partial<LiveStep>): void {
  const step = state.steps.find((s) => s.order === order)
  if (step) Object.assign(step, partial)
}

/** Pick the user-facing answer: prefer the last QAAgent result, else the last result. */
function deriveAnswer(steps: LiveStep[]): string {
  const done = steps.filter((s) => s.status === 'completed' && s.result)
  const qa = [...done].reverse().find((s) => s.agent_type === 'QAAgent')
  return (qa ?? done[done.length - 1])?.result ?? ''
}

export function isRealAgent(step: LiveStep): boolean {
  return !!step.executed_by && step.executed_by !== 'llm-roleplay'
}

export function phaseLabel(phase: Phase): string {
  switch (phase) {
    case 'planning':
      return 'The orchestrator is planning the task…'
    case 'running':
      return 'Agents are working…'
    case 'completed':
      return 'Task completed'
    case 'failed':
      return 'Task failed'
    default:
      return ''
  }
}

// --- Agent display metadata (icon + accent), shared by all views ---

interface AgentMeta {
  icon: string
  tint: string
}

const AGENT_META: Record<string, AgentMeta> = {
  DocumentAgent: { icon: 'Document', tint: 'text-sky-500' },
  KnowledgeAgent: { icon: 'Search', tint: 'text-violet-500' },
  AnalysisAgent: { icon: 'DataAnalysis', tint: 'text-amber-500' },
  QAAgent: { icon: 'ChatLineRound', tint: 'text-indigo-500' },
  ReportAgent: { icon: 'Tickets', tint: 'text-emerald-500' },
  ResearchAgent: { icon: 'Compass', tint: 'text-cyan-500' },
  ExecutionAgent: { icon: 'Monitor', tint: 'text-rose-500' },
  MemoryAgent: { icon: 'Connection', tint: 'text-teal-500' },
  CriticAgent: { icon: 'MagicStick', tint: 'text-fuchsia-500' },
}

export function agentMeta(agentType: string): AgentMeta {
  return AGENT_META[agentType] ?? { icon: 'Cpu', tint: 'text-slate-500' }
}
