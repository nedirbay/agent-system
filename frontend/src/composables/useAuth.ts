import { computed, ref } from 'vue'
import { authApi, getToken, setToken, type RegisterPayload, type User } from '@/api'

const USER_KEY = 'agentos-user'

function loadUser(): User | null {
  try {
    const raw = localStorage.getItem(USER_KEY)
    return raw ? (JSON.parse(raw) as User) : null
  } catch {
    return null
  }
}

// Module-level singletons — one reactive auth state shared app-wide.
const token = ref<string | null>(getToken())
const user = ref<User | null>(loadUser())

function persistUser(value: User | null) {
  user.value = value
  if (value) localStorage.setItem(USER_KEY, JSON.stringify(value))
  else localStorage.removeItem(USER_KEY)
}

export function useAuth() {
  const isAuthenticated = computed(() => Boolean(token.value))
  const displayName = computed(
    () => user.value?.full_name || user.value?.username || 'Operator',
  )

  async function login(username: string, password: string) {
    const res = await authApi.login(username, password)
    token.value = res.access_token
    setToken(res.access_token)
    // The login response is just a token; remember who we logged in as.
    persistUser({
      id: '',
      created_at: '',
      username,
      email: null,
      full_name: null,
      status: 'active',
    })
  }

  async function register(payload: RegisterPayload) {
    const created = await authApi.register(payload)
    persistUser(created)
    // Auto-login right after a successful registration.
    await login(payload.username, payload.password)
  }

  function logout() {
    token.value = null
    setToken(null)
    persistUser(null)
  }

  return { token, user, isAuthenticated, displayName, login, register, logout }
}
