<script setup lang="ts">
import { computed, ref } from 'vue'
import { useScrollProgress } from '@/composables/useScrollProgress'
import { useTheme } from '@/composables/useTheme'

const { scrollY } = useScrollProgress()
const { isDark, toggle: toggleTheme } = useTheme()
const scrolled = computed(() => scrollY.value > 24)
const mobileOpen = ref(false)

const links = [
  { to: '/', label: 'Home' },
  { to: '/features', label: 'Features' },
  { to: '/about', label: 'About' },
]
</script>

<template>
  <header
    class="fixed inset-x-0 top-0 z-50 transition-all duration-300"
    :class="
      scrolled
        ? 'border-b border-slate-200/70 bg-white/80 shadow-sm backdrop-blur-xl dark:border-slate-800/70 dark:bg-slate-950/80'
        : 'border-b border-transparent bg-transparent'
    "
  >
    <nav class="mx-auto flex max-w-6xl items-center gap-3 px-6 py-4">
      <RouterLink to="/" class="flex items-center gap-2.5">
        <span
          class="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 text-white shadow-lg shadow-indigo-500/30"
        >
          <el-icon :size="20"><Cpu /></el-icon>
        </span>
        <span class="text-base font-semibold tracking-tight text-slate-900 dark:text-white">
          Agent<span class="text-indigo-600 dark:text-indigo-400">OS</span>
        </span>
      </RouterLink>

      <!-- Desktop links -->
      <ul class="ml-auto hidden items-center gap-1 md:flex">
        <li v-for="link in links" :key="link.to">
          <RouterLink
            :to="link.to"
            class="rounded-lg px-4 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-100 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white"
            active-class="!text-indigo-600 dark:!text-indigo-400"
          >
            {{ link.label }}
          </RouterLink>
        </li>
        <li>
          <button
            class="ml-1 grid h-10 w-10 place-items-center rounded-lg text-slate-600 transition-colors hover:bg-slate-100 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white"
            :aria-label="isDark ? 'Switch to light mode' : 'Switch to dark mode'"
            @click="toggleTheme"
          >
            <el-icon :size="20">
              <Sunny v-if="isDark" />
              <Moon v-else />
            </el-icon>
          </button>
        </li>
        <li>
          <el-button type="primary" round class="ml-1">Get Started</el-button>
        </li>
      </ul>

      <!-- Mobile actions -->
      <div class="ml-auto flex items-center gap-1 md:hidden">
        <button
          class="grid h-10 w-10 place-items-center rounded-lg text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
          :aria-label="isDark ? 'Switch to light mode' : 'Switch to dark mode'"
          @click="toggleTheme"
        >
          <el-icon :size="20">
            <Sunny v-if="isDark" />
            <Moon v-else />
          </el-icon>
        </button>
        <button
          class="grid h-10 w-10 place-items-center rounded-lg text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800"
          aria-label="Toggle menu"
          @click="mobileOpen = !mobileOpen"
        >
          <el-icon :size="22">
            <Close v-if="mobileOpen" />
            <Menu v-else />
          </el-icon>
        </button>
      </div>
    </nav>

    <!-- Mobile menu -->
    <Transition name="slide-down">
      <div
        v-if="mobileOpen"
        class="border-t border-slate-200 bg-white/95 px-6 py-4 backdrop-blur-xl dark:border-slate-800 dark:bg-slate-950/95 md:hidden"
      >
        <ul class="flex flex-col gap-1">
          <li v-for="link in links" :key="link.to">
            <RouterLink
              :to="link.to"
              class="block rounded-lg px-4 py-3 text-sm font-medium text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800"
              active-class="!text-indigo-600 dark:!text-indigo-400"
              @click="mobileOpen = false"
            >
              {{ link.label }}
            </RouterLink>
          </li>
          <li class="mt-2">
            <el-button type="primary" round class="w-full">Get Started</el-button>
          </li>
        </ul>
      </div>
    </Transition>
  </header>
</template>

<style scoped>
.slide-down-enter-active,
.slide-down-leave-active {
  transition:
    opacity 0.25s ease,
    transform 0.25s ease;
}
.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
