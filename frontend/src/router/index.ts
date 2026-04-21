import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import AppWorkspacePage from '../pages/AppWorkspacePage.vue'
import LoginPage from '../pages/LoginPage.vue'
import GovernancePage from '../pages/GovernancePage.vue'
import ModelDashboardPage from '../pages/ModelDashboardPage.vue'
import ModelInsightPage from '../pages/ModelInsightPage.vue'
import TrainingCenterPage from '../pages/TrainingCenterPage.vue'
import NurseFollowupsPage from '../pages/NurseFollowupsPage.vue'
import DrugCatalogPage from '../pages/medication/DrugCatalogPage.vue'
import DrugPermissionManagementPage from '../pages/medication/permissions/DrugPermissionManagementPage.vue'
import { useAuthStore } from '../stores/auth'
import { pinia } from '../stores/pinia'

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
        path: 'nurse-followups',
        name: 'nurse-followups',
        component: NurseFollowupsPage,
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
        path: 'training-center',
        name: 'training-center',
        component: TrainingCenterPage,
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
      {
        path: 'drug-permission-management',
        name: 'drug-permission-management',
        component: DrugPermissionManagementPage,
      },
    ],
  },
  {
    path: '/login',
    name: 'login',
    component: LoginPage,
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

if (typeof window !== 'undefined') {
  window.addEventListener('ctpath:http-status', (event) => {
    const status = (event as CustomEvent<{ status?: number }>).detail?.status
    if (status !== 401) return

    const authStore = useAuthStore(pinia)
    authStore.clearSession()

    const current = router.currentRoute.value
    if (current.path !== '/login') {
      router.push({
        path: '/login',
        query: {
          redirect: current.fullPath,
        },
      })
    }
  })
}

router.beforeEach((to) => {
  const authStore = useAuthStore(pinia)
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
