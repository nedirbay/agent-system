<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import { useScrollProgress } from '@/composables/useScrollProgress'
import { features, stats } from '@/data/features'

const { scrollY } = useScrollProgress()
// Subtle parallax for the hero artwork.
const heroShift = computed(() => Math.min(scrollY.value * 0.15, 120))
const heroFade = computed(() => Math.max(1 - scrollY.value / 500, 0))

const steps = [
  {
    icon: 'Upload',
    title: 'Ingest',
    text: 'Drop in files, folders, databases, or APIs. We parse, OCR, and index everything.',
  },
  {
    icon: 'Share',
    title: 'Orchestrate',
    text: 'The Orchestrator plans the work and routes each step to the right specialist agent.',
  },
  {
    icon: 'ChatLineRound',
    title: 'Answer & Act',
    text: 'Get grounded answers, automated reports, and real tasks performed — with citations.',
  },
]
</script>

<template>
  <div class="overflow-hidden">
    <!-- ───────────────── Hero ───────────────── -->
    <section
      class="relative isolate flex min-h-screen items-center justify-center px-6 pt-20"
    >
      <!-- animated gradient blobs -->
      <div
        class="pointer-events-none absolute inset-0 -z-10"
        :style="{ transform: `translateY(${heroShift}px)`, opacity: heroFade }"
      >
        <div
          class="blob absolute -top-24 left-1/4 h-96 w-96 rounded-full bg-indigo-400/40 blur-3xl"
        />
        <div
          class="blob absolute top-32 right-1/4 h-[28rem] w-[28rem] rounded-full bg-violet-400/40 blur-3xl"
          style="animation-delay: -6s"
        />
        <div
          class="blob absolute bottom-0 left-1/3 h-80 w-80 rounded-full bg-sky-300/40 blur-3xl"
          style="animation-delay: -12s"
        />
      </div>
      <div class="absolute inset-0 -z-10 bg-grid [mask-image:radial-gradient(ellipse_at_center,black,transparent_70%)]" />

      <div class="mx-auto max-w-4xl text-center">
        <span
          v-reveal
          class="inline-flex items-center gap-2 rounded-full border border-indigo-200 bg-white/70 px-4 py-1.5 text-sm font-medium text-indigo-700 shadow-sm backdrop-blur"
        >
          <span class="relative flex h-2 w-2">
            <span class="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
            <span class="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
          </span>
          Nine agents. One platform.
        </span>

        <h1
          v-reveal="80"
          class="mt-6 text-balance text-5xl font-bold leading-[1.05] tracking-tight text-slate-900 sm:text-6xl md:text-7xl"
        >
          Turn your documents into
          <span
            class="bg-gradient-to-r from-indigo-600 via-violet-600 to-fuchsia-600 bg-clip-text text-transparent"
            >answers and action</span
          >.
        </h1>

        <p
          v-reveal="160"
          class="mx-auto mt-6 max-w-2xl text-pretty text-lg leading-relaxed text-slate-600"
        >
          A multi-agent AI platform that analyzes large volumes of files, builds a
          living knowledge base, answers questions with citations, generates
          reports, and automates real tasks — securely, at scale.
        </p>

        <div
          v-reveal="240"
          class="mt-10 flex flex-col items-center justify-center gap-3 sm:flex-row"
        >
          <el-button type="primary" size="large" round class="!px-8">
            <el-icon class="mr-1"><Promotion /></el-icon>
            Get Started
          </el-button>
          <RouterLink to="/features">
            <el-button size="large" round class="!px-8">
              Explore Features
              <el-icon class="ml-1"><Right /></el-icon>
            </el-button>
          </RouterLink>
        </div>
      </div>

      <!-- scroll cue -->
      <div
        class="absolute bottom-8 left-1/2 -translate-x-1/2 text-slate-400"
        :style="{ opacity: heroFade }"
      >
        <el-icon :size="24" class="animate-bounce"><ArrowDownBold /></el-icon>
      </div>
    </section>

    <!-- ───────────────── Stats ───────────────── -->
    <section class="border-y border-slate-200 bg-white">
      <div class="mx-auto grid max-w-6xl grid-cols-2 gap-px md:grid-cols-4">
        <div
          v-for="(stat, i) in stats"
          :key="stat.label"
          v-reveal="i * 100"
          class="px-6 py-10 text-center"
        >
          <div
            class="bg-gradient-to-br from-indigo-600 to-violet-600 bg-clip-text text-4xl font-bold text-transparent sm:text-5xl"
          >
            {{ stat.value }}
          </div>
          <p class="mt-2 text-sm font-medium text-slate-500">{{ stat.label }}</p>
        </div>
      </div>
    </section>

    <!-- ───────────────── Features ───────────────── -->
    <section class="mx-auto max-w-6xl px-6 py-24">
      <div class="mx-auto max-w-2xl text-center">
        <h2
          v-reveal
          class="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl"
        >
          Everything it takes to
          <span class="text-indigo-600">understand your data</span>
        </h2>
        <p v-reveal="100" class="mt-4 text-lg text-slate-600">
          Each capability is a specialized agent, working together through a
          durable event-driven core.
        </p>
      </div>

      <div class="mt-16 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        <article
          v-for="(feature, i) in features"
          :key="feature.title"
          v-reveal="(i % 3) * 120"
          class="group relative overflow-hidden rounded-2xl border border-slate-200 bg-white p-7 transition-all duration-300 hover:-translate-y-1 hover:border-transparent hover:shadow-xl hover:shadow-indigo-500/10"
        >
          <div
            class="absolute inset-0 -z-10 bg-gradient-to-br opacity-0 transition-opacity duration-300 group-hover:opacity-[0.04]"
            :class="feature.accent"
          />
          <span
            class="grid h-12 w-12 place-items-center rounded-xl bg-gradient-to-br text-white shadow-lg"
            :class="feature.accent"
          >
            <el-icon :size="24"><component :is="feature.icon" /></el-icon>
          </span>
          <h3 class="mt-5 text-lg font-semibold text-slate-900">
            {{ feature.title }}
          </h3>
          <p class="mt-2 text-sm leading-relaxed text-slate-600">
            {{ feature.summary }}
          </p>
        </article>
      </div>
    </section>

    <!-- ───────────────── How it works ───────────────── -->
    <section class="border-t border-slate-200 bg-slate-50">
      <div class="mx-auto max-w-6xl px-6 py-24">
        <div class="mx-auto max-w-2xl text-center">
          <h2
            v-reveal
            class="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl"
          >
            From raw files to real outcomes
          </h2>
          <p v-reveal="100" class="mt-4 text-lg text-slate-600">
            Three stages, fully automated.
          </p>
        </div>

        <div class="relative mt-16 grid gap-8 md:grid-cols-3">
          <!-- connecting line -->
          <div
            class="absolute left-0 right-0 top-9 hidden h-px bg-gradient-to-r from-transparent via-indigo-200 to-transparent md:block"
          />
          <div
            v-for="(step, i) in steps"
            :key="step.title"
            v-reveal="i * 150"
            class="relative text-center"
          >
            <span
              class="relative z-10 mx-auto grid h-[4.5rem] w-[4.5rem] place-items-center rounded-2xl border border-indigo-100 bg-white text-indigo-600 shadow-md"
            >
              <el-icon :size="30"><component :is="step.icon" /></el-icon>
            </span>
            <div class="mt-2 text-sm font-semibold text-indigo-500">
              Step {{ i + 1 }}
            </div>
            <h3 class="mt-1 text-xl font-semibold text-slate-900">
              {{ step.title }}
            </h3>
            <p class="mx-auto mt-2 max-w-xs text-sm leading-relaxed text-slate-600">
              {{ step.text }}
            </p>
          </div>
        </div>
      </div>
    </section>

    <!-- ───────────────── CTA ───────────────── -->
    <section class="mx-auto max-w-6xl px-6 py-24">
      <div
        v-reveal
        class="relative overflow-hidden rounded-3xl bg-gradient-to-br from-indigo-600 via-violet-600 to-fuchsia-600 px-8 py-16 text-center shadow-2xl shadow-indigo-500/30 sm:px-16"
      >
        <div class="absolute inset-0 bg-grid-light opacity-20" />
        <div class="relative">
          <h2 class="text-3xl font-bold tracking-tight text-white sm:text-4xl">
            Ready to put your knowledge to work?
          </h2>
          <p class="mx-auto mt-4 max-w-xl text-lg text-indigo-100">
            Bring your documents. Let nine agents do the reading, reasoning, and
            routine work for you.
          </p>
          <div class="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <el-button size="large" round class="!border-0 !px-8 !text-indigo-700">
              Get Started
            </el-button>
            <RouterLink to="/about">
              <el-button
                size="large"
                round
                class="!border-white/60 !bg-transparent !px-8 !text-white hover:!bg-white/10"
              >
                Learn about us
              </el-button>
            </RouterLink>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>
