import type { Directive } from 'vue'

interface RevealOptions {
  /** Delay before the reveal transition starts, in milliseconds. */
  delay?: number
  /** Visibility ratio (0–1) that triggers the reveal. Default 0.15. */
  threshold?: number
  /** Reveal once and stop observing (default), or re-run every time it enters. */
  once?: boolean
}

/**
 * v-reveal — fades + slides an element into view as it enters the viewport,
 * using IntersectionObserver. Usage:
 *
 *   <div v-reveal>…</div>
 *   <div v-reveal="{ delay: 120 }">…</div>
 *   <div v-reveal="200">…</div>   // shorthand for { delay: 200 }
 *
 * Honors prefers-reduced-motion (the .reveal base style disables motion there).
 */
export const reveal: Directive<HTMLElement, RevealOptions | number | undefined> = {
  mounted(el, binding) {
    const opts: RevealOptions =
      typeof binding.value === 'number'
        ? { delay: binding.value }
        : binding.value ?? {}

    el.classList.add('reveal')
    if (opts.delay) el.style.transitionDelay = `${opts.delay}ms`

    const once = opts.once ?? true

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            el.classList.add('reveal-visible')
            if (once) observer.unobserve(el)
          } else if (!once) {
            el.classList.remove('reveal-visible')
          }
        }
      },
      { threshold: opts.threshold ?? 0.15 },
    )

    observer.observe(el)
    // Stash so we can disconnect on unmount.
    ;(el as HTMLElement & { _revealObserver?: IntersectionObserver })._revealObserver =
      observer
  },
  unmounted(el) {
    ;(el as HTMLElement & { _revealObserver?: IntersectionObserver })._revealObserver?.disconnect()
  },
}
