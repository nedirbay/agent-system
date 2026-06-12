<script setup lang="ts">
import { computed, ref } from 'vue'
import { useScrollProgress } from '@/composables/useScrollProgress'

const { scrollY } = useScrollProgress()
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
        ? 'border-b border-slate-200/70 bg-white/80 backdrop-blur-xl shadow-sm'
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
        <span class="text-base font-semibold tracking-tight text-slate-900">
          Agent<span class="text-indigo-600">OS</span>
        </span>
      </RouterLink>

      <!-- Desktop links -->
      <ul class="ml-auto hidden items-center gap-1 md:flex">
        <li v-for="link in links" :key="link.to">
          <RouterLink
            :to="link.to"
            class="rounded-lg px-4 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-100 hover:text-slate-900"
            active-class="!text-indigo-600"
          >
            {{ link.label }}
          </RouterLink>
        </li>
        <li>
          <el-button type="primary" round class="ml-2">Get Started</el-button>
        </li>
      </ul>

      <!-- Mobile toggle -->
      <button
        class="ml-auto grid h-10 w-10 place-items-center rounded-lg text-slate-700 hover:bg-slate-100 md:hidden"
        aria-label="Toggle menu"
        @click="mobileOpen = !mobileOpen"
      >
        <el-icon :size="22">
          <Close v-if="mobileOpen" />
          <Menu v-else />
        </el-icon>
      </button>
    </nav>

    <!-- Mobile menu -->
    <Transition name="slide-down">
      <div
        v-if="mobileOpen"
        class="border-t border-slate-200 bg-white/95 px-6 py-4 backdrop-blur-xl md:hidden"
      >
        <ul class="flex flex-col gap-1">
          <li v-for="link in links" :key="link.to">
            <RouterLink
              :to="link.to"
              class="block rounded-lg px-4 py-3 text-sm font-medium text-slate-700 hover:bg-slate-100"
              active-class="!text-indigo-600"
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
