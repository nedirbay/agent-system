import { onMounted, onUnmounted, ref } from 'vue'

/**
 * Tracks the vertical scroll offset of the window, throttled to animation frames.
 * Useful for parallax and "scrolled" navbar states.
 */
export function useScrollProgress() {
  const scrollY = ref(0)
  let ticking = false

  function onScroll() {
    if (ticking) return
    ticking = true
    requestAnimationFrame(() => {
      scrollY.value = window.scrollY
      ticking = false
    })
  }

  onMounted(() => {
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
  })
  onUnmounted(() => window.removeEventListener('scroll', onScroll))

  return { scrollY }
}
