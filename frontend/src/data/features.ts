/**
 * Platform feature catalog — the single source of truth shared by the Home and
 * Features pages. `icon` values are globally-registered Element Plus icon names.
 */
export interface Feature {
  icon: string
  title: string
  summary: string
  details: string
  accent: string // tailwind gradient classes
}

export const features: Feature[] = [
  {
    icon: 'Cpu',
    title: 'Multi-Agent Orchestration',
    summary: 'Nine specialized agents plan, route, and recover work as one system.',
    details:
      'An Orchestrator decomposes each request into a plan and routes it to the right specialist agent — Document, Knowledge, Analysis, QA, Report, Research, Execution, Memory, and Critic — coordinated by a recoverable Workflow Engine.',
    accent: 'from-indigo-500 to-violet-500',
  },
  {
    icon: 'Files',
    title: 'Document Ingestion & OCR',
    summary: 'Upload thousands of files; we parse, OCR, and structure them.',
    details:
      'PDF, DOCX, XLSX, CSV, TXT, JSON, and images flow through parsing, OCR for scans, metadata extraction, and chunking — turning raw files into searchable knowledge.',
    accent: 'from-sky-500 to-cyan-500',
  },
  {
    icon: 'Search',
    title: 'Semantic Knowledge Base',
    summary: 'Retrieval-augmented search over millions of documents.',
    details:
      'Hybrid retrieval combines vector similarity with keyword search across a knowledge base built for 10M+ documents, returning the most relevant context in under five seconds.',
    accent: 'from-emerald-500 to-teal-500',
  },
  {
    icon: 'ChatDotRound',
    title: 'Grounded Q&A',
    summary: 'Ask in natural language; get answers with citations.',
    details:
      'The QA agent answers strictly from your documents, every claim backed by a source reference, with a Critic agent screening for hallucinations before you ever see the response.',
    accent: 'from-violet-500 to-fuchsia-500',
  },
  {
    icon: 'DataAnalysis',
    title: 'Analysis & Reports',
    summary: 'Aggregations, trends, and polished PDF / DOCX / XLSX reports.',
    details:
      'The Analysis agent produces statistics, trends, and comparisons; the Report agent renders them into shareable documents — automatically, on demand.',
    accent: 'from-amber-500 to-orange-500',
  },
  {
    icon: 'Monitor',
    title: 'Computer Use Automation',
    summary: 'Agents perform real browser and desktop tasks — safely.',
    details:
      'The Execution agent automates browsing, form-filling, downloads, and file operations inside an isolated sandbox, with human-approval gates on anything sensitive.',
    accent: 'from-rose-500 to-pink-500',
  },
  {
    icon: 'Connection',
    title: 'Event-Driven Core',
    summary: 'Durable, ordered messaging built for 1M+ events per day.',
    details:
      'Every component communicates through an Event Bus with at-least-once delivery, per-task ordering, retries, and a dead-letter queue — so agents scale independently and nothing gets lost.',
    accent: 'from-blue-500 to-indigo-500',
  },
  {
    icon: 'Lock',
    title: 'Enterprise Security',
    summary: 'RBAC, encryption, sandboxing, and a full audit trail.',
    details:
      'JWT auth with role-based access control, encryption in transit and at rest, isolated execution sandboxes, and an immutable audit log of every user, agent, and system action.',
    accent: 'from-slate-600 to-slate-800',
  },
  {
    icon: 'MagicStick',
    title: 'Persistent Memory',
    summary: 'Session, long-term, and knowledge memory across tasks.',
    details:
      'A dedicated Memory agent keeps the others stateless while preserving session context, working memory, and long-term knowledge — so the platform gets smarter with use.',
    accent: 'from-purple-500 to-indigo-500',
  },
]

export interface Stat {
  value: string
  label: string
}

export const stats: Stat[] = [
  { value: '10M+', label: 'Documents indexed' },
  { value: '9', label: 'Specialized agents' },
  { value: '1M+', label: 'Events / day' },
  { value: '99.5%', label: 'Availability target' },
]
