<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useTheme } from '@/composables/useTheme'
import { useAuth } from '@/composables/useAuth'

const router = useRouter()
const { isDark, toggle: toggleTheme } = useTheme()
const { displayName, logout } = useAuth()
const sidebarOpen = ref(false)

const nav = [
  { to: '/app/chat', label: 'Chat', icon: 'ChatDotRound' },
  { to: '/app/agents', label: 'Agents', icon: 'MagicStick' },
  { to: '/app/connectors', label: 'Connectors', icon: 'Connection' },
  { to: '/app/workspace', label: 'Workspace', icon: 'Folder' },
  { to: '/app/dashboard', label: 'Dashboard', icon: 'DataAnalysis' },
]

function onLogout() {
  logout()
  router.push('/login')
}
</script>

<template>
  <div class="flex min-h-screen bg-slate-50 dark:bg-slate-950">
    <!-- Sidebar -->
    <aside
      class="fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-slate-200 bg-white transition-transform duration-300 dark:border-slate-800 dark:bg-slate-900 lg:translate-x-0"
      :class="sidebarOpen ? 'translate-x-0' : '-translate-x-full'"
    >
      <RouterLink to="/" class="flex items-center gap-2.5 px-6 py-5">
        <span
          class="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 text-white shadow-lg shadow-indigo-500/30"
        >
          <el-icon :size="20"><Cpu /></el-icon>
        </span>
        <span class="text-base font-semibold tracking-tight text-slate-900 dark:text-white">
          Agent<span class="text-indigo-600 dark:text-indigo-400">OS</span>
        </span>
      </RouterLink>

      <nav class="flex-1 space-y-1 px-3 py-2">
        <RouterLink
          v-for="item in nav"
          :key="item.to"
          :to="item.to"
          class="flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-100 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white"
          active-class="!bg-indigo-50 !text-indigo-600 dark:!bg-indigo-500/10 dark:!text-indigo-400"
          @click="sidebarOpen = false"
        >
          <el-icon :size="18"><component :is="item.icon" /></el-icon>
          {{ item.label }}
        </RouterLink>
      </nav>

      <div class="border-t border-slate-200 p-4 dark:border-slate-800">
        <div class="flex items-center gap-3 rounded-xl px-2 py-2">
          <el-avatar :size="36" class="!bg-gradient-to-br !from-indigo-500 !to-violet-600">
            {{ displayName.charAt(0).toUpperCase() }}
          </el-avatar>
          <div class="min-w-0 flex-1">
            <p class="truncate text-sm font-medium text-slate-900 dark:text-white">
              {{ displayName }}
            </p>
            <button
              class="text-xs text-slate-500 hover:text-indigo-600 dark:text-slate-400 dark:hover:text-indigo-400"
              @click="onLogout"
            >
              Sign out
            </button>
          </div>
        </div>
      </div>
    </aside>

    <!-- Mobile backdrop -->
    <div
      v-if="sidebarOpen"
      class="fixed inset-0 z-30 bg-slate-900/40 backdrop-blur-sm lg:hidden"
      @click="sidebarOpen = false"
    />

    <!-- Main column -->
    <div class="flex min-w-0 flex-1 flex-col lg:pl-64">
      <header
        class="sticky top-0 z-20 flex items-center gap-3 border-b border-slate-200 bg-white/80 px-4 py-3 backdrop-blur-xl dark:border-slate-800 dark:bg-slate-900/80 sm:px-6"
      >
        <button
          class="grid h-10 w-10 place-items-center rounded-lg text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800 lg:hidden"
          aria-label="Toggle sidebar"
          @click="sidebarOpen = !sidebarOpen"
        >
          <el-icon :size="22"><Menu /></el-icon>
        </button>
        <h1 class="text-sm font-semibold text-slate-900 dark:text-white">
          {{ $route.meta.title ?? 'Console' }}
        </h1>
        <button
          class="ml-auto grid h-10 w-10 place-items-center rounded-lg text-slate-600 transition-colors hover:bg-slate-100 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white"
          :aria-label="isDark ? 'Switch to light mode' : 'Switch to dark mode'"
          @click="toggleTheme"
        >
          <el-icon :size="20">
            <Sunny v-if="isDark" />
            <Moon v-else />
          </el-icon>
        </button>
      </header>

      <main class="flex-1 px-4 py-6 sm:px-6 lg:px-8">
        <RouterView v-slot="{ Component }">
          <Transition name="page" mode="out-in">
            <component :is="Component" />
          </Transition>
        </RouterView>
      </main>
    </div>
  </div>
</template>
