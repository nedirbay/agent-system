<script setup lang="ts">
import { features } from '@/data/features'
</script>

<template>
  <div class="bg-white dark:bg-slate-950">
    <!-- Page header -->
    <section class="relative isolate px-6 pb-16 pt-36">
      <div class="absolute inset-0 -z-10 bg-grid [mask-image:radial-gradient(ellipse_at_top,black,transparent_75%)]" />
      <div class="mx-auto max-w-3xl text-center">
        <span
          v-reveal
          class="inline-flex rounded-full border border-indigo-200 bg-indigo-50 px-4 py-1.5 text-sm font-medium text-indigo-700 dark:border-indigo-500/30 dark:bg-indigo-500/10 dark:text-indigo-300"
        >
          Platform Capabilities
        </span>
        <h1
          v-reveal="80"
          class="mt-6 text-4xl font-bold tracking-tight text-slate-900 dark:text-white sm:text-5xl"
        >
          Nine agents,
          <span class="text-indigo-600 dark:text-indigo-400">one coordinated platform</span>
        </h1>
        <p v-reveal="160" class="mx-auto mt-5 max-w-2xl text-lg text-slate-600 dark:text-slate-300">
          Every capability below is a specialized agent. They never call each
          other directly — they collaborate through a durable, ordered event bus,
          so each can scale and recover on its own.
        </p>
      </div>
    </section>

    <!-- Alternating feature rows -->
    <section class="mx-auto max-w-6xl space-y-20 px-6 pb-28">
      <article
        v-for="(feature, i) in features"
        :key="feature.title"
        v-reveal
        class="grid items-center gap-10 md:grid-cols-2"
        :class="i % 2 === 1 ? 'md:[&>*:first-child]:order-2' : ''"
      >
        <!-- Visual -->
        <div
          class="relative flex aspect-[4/3] items-center justify-center overflow-hidden rounded-3xl border border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-slate-900"
        >
          <div
            class="absolute inset-0 bg-gradient-to-br opacity-10 dark:opacity-20"
            :class="feature.accent"
          />
          <div
            class="absolute -inset-8 bg-gradient-to-br opacity-20 blur-3xl dark:opacity-30"
            :class="feature.accent"
          />
          <span
            class="relative grid h-24 w-24 place-items-center rounded-3xl bg-gradient-to-br text-white shadow-2xl"
            :class="feature.accent"
          >
            <el-icon :size="48"><component :is="feature.icon" /></el-icon>
          </span>
        </div>

        <!-- Copy -->
        <div>
          <div
            class="inline-flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-indigo-500 dark:text-indigo-400"
          >
            <span class="text-2xl font-bold tabular-nums opacity-40"
              >{{ String(i + 1).padStart(2, '0') }}</span
            >
          </div>
          <h2 class="mt-2 text-2xl font-bold tracking-tight text-slate-900 dark:text-white sm:text-3xl">
            {{ feature.title }}
          </h2>
          <p class="mt-3 text-lg font-medium text-slate-700 dark:text-slate-200">
            {{ feature.summary }}
          </p>
          <p class="mt-4 leading-relaxed text-slate-600 dark:text-slate-400">
            {{ feature.details }}
          </p>
        </div>
      </article>
    </section>

    <!-- CTA strip -->
    <section class="border-t border-slate-200 bg-slate-50 px-6 py-20 dark:border-slate-800 dark:bg-slate-900">
      <div v-reveal class="mx-auto max-w-3xl text-center">
        <h2 class="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
          See it on your own documents
        </h2>
        <p class="mx-auto mt-3 max-w-xl text-lg text-slate-600 dark:text-slate-300">
          Upload a folder and watch the agents ingest, index, and answer.
        </p>
        <div class="mt-8">
          <el-button type="primary" size="large" round class="!px-8">
            <el-icon class="mr-1"><Promotion /></el-icon>
            Get Started
          </el-button>
        </div>
      </div>
    </section>
  </div>
</template>
