import { computed, ref } from 'vue'

export type Theme = 'light' | 'dark'

const STORAGE_KEY = 'agentos-theme'

/** Read the current theme from the <html> element (set pre-paint in index.html). */
function currentTheme(): Theme {
  return document.documentElement.classList.contains('dark') ? 'dark' : 'light'
}

// Module-level singleton so every component shares one reactive source of truth.
const theme = ref<Theme>(currentTheme())

function apply(value: Theme) {
  const root = document.documentElement
  root.classList.toggle('dark', value === 'dark')
  root.style.colorScheme = value
  localStorage.setItem(STORAGE_KEY, value)
}

export function useTheme() {
  const isDark = computed(() => theme.value === 'dark')

  function setTheme(value: Theme) {
    theme.value = value
    apply(value)
  }

  function toggle() {
    setTheme(isDark.value ? 'light' : 'dark')
  }

  return { theme, isDark, toggle, setTheme }
}
