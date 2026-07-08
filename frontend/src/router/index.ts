import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '@/views/HomeView.vue'
import { useAuth } from '@/composables/useAuth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    // --- Public marketing site ---
    { path: '/', name: 'home', component: HomeView, meta: { title: 'Home' } },
    {
      path: '/features',
      name: 'features',
      component: () => import('@/views/FeaturesView.vue'),
      meta: { title: 'Features' },
    },
    {
      path: '/about',
      name: 'about',
      component: () => import('@/views/AboutView.vue'),
      meta: { title: 'About Us' },
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { title: 'Sign in', guestOnly: true },
    },

    // --- Authenticated application console ---
    {
      path: '/app',
      component: () => import('@/layouts/AppLayout.vue'),
      meta: { requiresAuth: true },
      redirect: { name: 'chat' },
      children: [
        {
          path: 'chat',
          name: 'chat',
          component: () => import('@/views/app/ChatView.vue'),
          meta: { title: 'Chat', requiresAuth: true },
        },
        {
          path: 'agents',
          name: 'agents',
          component: () => import('@/views/app/AgentsView.vue'),
          meta: { title: 'Agents', requiresAuth: true },
        },
        {
          path: 'connectors',
          name: 'connectors',
          component: () => import('@/views/app/ConnectorsView.vue'),
          meta: { title: 'Connectors', requiresAuth: true },
        },
        {
          path: 'workspace',
          name: 'workspace',
          component: () => import('@/views/app/WorkspaceView.vue'),
          meta: { title: 'Workspace', requiresAuth: true },
        },
        {
          path: 'dashboard',
          name: 'dashboard',
          component: () => import('@/views/app/DashboardView.vue'),
          meta: { title: 'Dashboard', requiresAuth: true },
        },
      ],
    },
  ],
  // Scroll to top on navigation; respect back/forward saved positions.
  scrollBehavior(_to, _from, savedPosition) {
    return savedPosition ?? { top: 0, behavior: 'smooth' }
  },
})

// Route guard: protect the console, keep authed users out of /login.
router.beforeEach((to) => {
  const { isAuthenticated } = useAuth()
  if (to.meta.requiresAuth && !isAuthenticated.value) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.meta.guestOnly && isAuthenticated.value) {
    return { name: 'chat' }
  }
  return true
})

router.afterEach((to) => {
  const title = to.meta.title as string | undefined
  document.title = title ? `${title} · AI Multi-Agent Platform` : 'AI Multi-Agent Platform'
})

export default router
