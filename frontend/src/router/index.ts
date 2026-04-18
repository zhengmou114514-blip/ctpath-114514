import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import AppWorkspacePage from '../pages/AppWorkspacePage.vue'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/',
    name: 'home',
    component: AppWorkspacePage,
    meta: {
      requiresAuth: true,
    },
  },
  {
    path: '/login',
    name: 'login',
    component: AppWorkspacePage,
    meta: {
      requiresAuth: false,
    },
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/',
  },
] as unknown as RouteRecordRaw[]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const authStore = useAuthStore()
  if (!authStore.session) {
    authStore.restoreSession()
  }

  const authenticated = authStore.isAuthenticated
  const requiresAuth = to.meta.requiresAuth !== false

  if (requiresAuth && !authenticated && to.path !== '/login') {
    return {
      path: '/login',
      query: {
        redirect: to.fullPath,
      },
    }
  }

  if (authenticated && to.path === '/login') {
    return { path: '/' }
  }

  return true
})

export default router
