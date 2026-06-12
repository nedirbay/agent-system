<script setup lang="ts">
const year = new Date().getFullYear()

const columns = [
  {
    title: 'Product',
    links: [
      { label: 'Features', to: '/features' },
      { label: 'About', to: '/about' },
      { label: 'Get Started', to: '/' },
    ],
  },
  {
    title: 'Platform',
    links: [
      { label: 'Agents', to: '/features' },
      { label: 'Knowledge Base', to: '/features' },
      { label: 'Automation', to: '/features' },
    ],
  },
  {
    title: 'Company',
    links: [
      { label: 'Our Story', to: '/about' },
      { label: 'Mission', to: '/about' },
      { label: 'Team', to: '/about' },
    ],
  },
]
</script>

<template>
  <footer class="border-t border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-slate-950">
    <div class="mx-auto max-w-6xl px-6 py-14">
      <div class="grid gap-10 md:grid-cols-4">
        <div>
          <div class="flex items-center gap-2.5">
            <span
              class="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 text-white"
            >
              <el-icon :size="20"><Cpu /></el-icon>
            </span>
            <span class="text-base font-semibold tracking-tight text-slate-900 dark:text-white">
              Agent<span class="text-indigo-600 dark:text-indigo-400">OS</span>
            </span>
          </div>
          <p class="mt-4 max-w-xs text-sm leading-relaxed text-slate-500 dark:text-slate-400">
            A multi-agent platform that reads your documents, answers your
            questions, and automates the work around them.
          </p>
        </div>

        <div v-for="col in columns" :key="col.title">
          <h3 class="text-sm font-semibold text-slate-900 dark:text-white">{{ col.title }}</h3>
          <ul class="mt-4 space-y-3">
            <li v-for="link in col.links" :key="link.label">
              <RouterLink
                :to="link.to"
                class="text-sm text-slate-500 transition-colors hover:text-indigo-600 dark:text-slate-400 dark:hover:text-indigo-400"
              >
                {{ link.label }}
              </RouterLink>
            </li>
          </ul>
        </div>
      </div>

      <div
        class="mt-12 flex flex-col items-center justify-between gap-4 border-t border-slate-200 pt-8 text-sm text-slate-400 dark:border-slate-800 dark:text-slate-500 sm:flex-row"
      >
        <p>© {{ year }} AgentOS — AI Multi-Agent Knowledge &amp; Automation Platform.</p>
        <p>Built with Vue 3 · Tailwind · Element Plus</p>
      </div>
    </div>
  </footer>
</template>
