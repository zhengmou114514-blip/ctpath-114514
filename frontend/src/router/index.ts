import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import AppWorkspacePage from '../pages/AppWorkspacePage.vue'
import GovernancePage from '../pages/GovernancePage.vue'
import ModelDashboardPage from '../pages/ModelDashboardPage.vue'
import ModelInsightPage from '../pages/ModelInsightPage.vue'
import DrugCatalogPage from '../pages/DrugCatalogPage.vue'
import { useAuthStore } from '../stores/auth'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'home',
    component: AppWorkspacePage,
    meta: {
      requiresAuth: true,
    },
    children: [
      {
        path: 'patient-detail/:patientId?',
        name: 'patient-detail',
        component: () => import('../pages/PatientDetailPage.vue'),
      },
      {
        path: 'model-insight',
        name: 'model-insight',
        component: ModelInsightPage,
      },
      {
        path: 'model-dashboard',
        name: 'model-dashboard',
        component: ModelDashboardPage,
      },
      {
        path: 'governance',
        name: 'governance',
        component: GovernancePage,
      },
      {
        path: 'drug-management',
        name: 'drug-management',
        component: DrugCatalogPage,
      },
    ],
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
]

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
