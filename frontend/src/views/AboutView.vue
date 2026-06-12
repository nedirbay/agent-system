<script setup lang="ts">
const values = [
  {
    icon: 'Aim',
    title: 'Grounded by default',
    text: 'Every answer cites its source. A dedicated Critic agent screens output for hallucinations before it reaches you.',
  },
  {
    icon: 'Lock',
    title: 'Secure by design',
    text: 'Role-based access, encryption everywhere, sandboxed execution, and an immutable audit trail — not afterthoughts.',
  },
  {
    icon: 'Connection',
    title: 'Built to scale',
    text: 'An event-driven core lets every agent scale and recover independently, from a laptop to a cluster.',
  },
  {
    icon: 'MagicStick',
    title: 'Better with use',
    text: 'Persistent memory means the platform compounds what it learns across sessions and tasks.',
  },
]

const timeline = [
  { year: 'Phase 1', title: 'Foundation', text: 'Requirements, architecture, and project structure defined.' },
  { year: 'Phase 3', title: 'Knowledge Layer', text: 'Chunking, embeddings, and vector storage built for millions of documents.' },
  { year: 'Phase 4', title: 'Orchestrator', text: 'Task planning, agent routing, and the workflow engine come online.' },
  { year: 'Phase 8', title: 'Experience', text: 'Chat, workspace, and dashboard — the platform people actually touch.' },
]

const team = [
  { name: 'Orchestrator', role: 'Plans & routes every task', initials: 'OR', accent: 'from-indigo-500 to-violet-500' },
  { name: 'Knowledge', role: 'Retrieval & semantic search', initials: 'KN', accent: 'from-emerald-500 to-teal-500' },
  { name: 'QA', role: 'Grounded answers with citations', initials: 'QA', accent: 'from-violet-500 to-fuchsia-500' },
  { name: 'Critic', role: 'Validates & guards quality', initials: 'CR', accent: 'from-rose-500 to-pink-500' },
]
</script>

<template>
  <div>
    <!-- Hero -->
    <section class="relative isolate px-6 pb-20 pt-36">
      <div class="absolute inset-0 -z-10 bg-grid [mask-image:radial-gradient(ellipse_at_top,black,transparent_75%)]" />
      <div class="mx-auto max-w-3xl text-center">
        <span
          v-reveal
          class="inline-flex rounded-full border border-indigo-200 bg-indigo-50 px-4 py-1.5 text-sm font-medium text-indigo-700"
        >
          About Us
        </span>
        <h1
          v-reveal="80"
          class="mt-6 text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl"
        >
          We build software that
          <span class="text-indigo-600">reads, reasons, and acts</span>
        </h1>
        <p v-reveal="160" class="mx-auto mt-5 max-w-2xl text-lg text-slate-600">
          Knowledge work shouldn't mean drowning in files. We set out to build a
          platform where a team of AI agents handles the reading, the searching,
          and the routine — so people focus on the decisions that matter.
        </p>
      </div>
    </section>

    <!-- Mission -->
    <section class="mx-auto max-w-5xl px-6 pb-24">
      <div
        v-reveal
        class="rounded-3xl border border-slate-200 bg-gradient-to-br from-slate-50 to-white p-10 sm:p-14"
      >
        <h2 class="text-sm font-semibold uppercase tracking-wide text-indigo-500">
          Our mission
        </h2>
        <p class="mt-4 text-2xl font-medium leading-snug text-slate-800 sm:text-3xl">
          To turn any organization's documents, databases, and data sources into a
          living knowledge base — one that answers questions, produces insight, and
          automates the work around it,
          <span class="text-indigo-600">securely and at scale</span>.
        </p>
      </div>
    </section>

    <!-- Values -->
    <section class="border-y border-slate-200 bg-slate-50 px-6 py-24">
      <div class="mx-auto max-w-6xl">
        <div class="mx-auto max-w-2xl text-center">
          <h2 v-reveal class="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            What we stand for
          </h2>
          <p v-reveal="100" class="mt-4 text-lg text-slate-600">
            The principles baked into every layer of the platform.
          </p>
        </div>
        <div class="mt-14 grid gap-6 sm:grid-cols-2">
          <div
            v-for="(value, i) in values"
            :key="value.title"
            v-reveal="(i % 2) * 120"
            class="flex gap-5 rounded-2xl border border-slate-200 bg-white p-7"
          >
            <span
              class="grid h-12 w-12 shrink-0 place-items-center rounded-xl bg-indigo-50 text-indigo-600"
            >
              <el-icon :size="24"><component :is="value.icon" /></el-icon>
            </span>
            <div>
              <h3 class="text-lg font-semibold text-slate-900">{{ value.title }}</h3>
              <p class="mt-1.5 text-sm leading-relaxed text-slate-600">
                {{ value.text }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Timeline -->
    <section class="mx-auto max-w-4xl px-6 py-24">
      <div class="mx-auto max-w-2xl text-center">
        <h2 v-reveal class="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
          How we're building it
        </h2>
        <p v-reveal="100" class="mt-4 text-lg text-slate-600">
          A phased roadmap from foundation to production.
        </p>
      </div>

      <div class="relative mt-16 pl-8">
        <div class="absolute bottom-2 left-2 top-2 w-px bg-gradient-to-b from-indigo-300 via-violet-300 to-transparent" />
        <div
          v-for="(item, i) in timeline"
          :key="item.title"
          v-reveal="i * 120"
          class="relative pb-12 last:pb-0"
        >
          <span
            class="absolute -left-[1.6rem] top-1 grid h-4 w-4 place-items-center rounded-full border-2 border-white bg-indigo-500 shadow"
          />
          <div class="text-sm font-semibold text-indigo-500">{{ item.year }}</div>
          <h3 class="mt-1 text-xl font-semibold text-slate-900">{{ item.title }}</h3>
          <p class="mt-1.5 text-slate-600">{{ item.text }}</p>
        </div>
      </div>
    </section>

    <!-- Team (agents) -->
    <section class="border-t border-slate-200 bg-slate-50 px-6 py-24">
      <div class="mx-auto max-w-6xl">
        <div class="mx-auto max-w-2xl text-center">
          <h2 v-reveal class="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            Meet a few of the agents
          </h2>
          <p v-reveal="100" class="mt-4 text-lg text-slate-600">
            Each one is a specialist. Together, they're a team.
          </p>
        </div>
        <div class="mt-14 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          <div
            v-for="(member, i) in team"
            :key="member.name"
            v-reveal="(i % 4) * 100"
            class="rounded-2xl border border-slate-200 bg-white p-7 text-center transition-all duration-300 hover:-translate-y-1 hover:shadow-lg"
          >
            <span
              class="mx-auto grid h-16 w-16 place-items-center rounded-2xl bg-gradient-to-br text-lg font-bold text-white shadow-lg"
              :class="member.accent"
            >
              {{ member.initials }}
            </span>
            <h3 class="mt-4 font-semibold text-slate-900">{{ member.name }} Agent</h3>
            <p class="mt-1 text-sm text-slate-500">{{ member.role }}</p>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>
