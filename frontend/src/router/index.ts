import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import AppWorkspacePage from '../pages/AppWorkspacePage.vue'
import LoginPage from '../pages/LoginPage.vue'
import ModelDashboardPage from '../pages/ModelDashboardPage.vue'
import ModelInsightPage from '../pages/ModelInsightPage.vue'
import ModelOperationsPage from '../pages/ModelOperationsPage.vue'
import RoleWorkspacePage from '../pages/RoleWorkspacePage.vue'
import PatientArchivePrintPage from '../pages/PatientArchivePrintPage.vue'
import GovernancePage from '../pages/GovernancePage.vue'
import NurseFollowupsPage from '../pages/NurseFollowupsPage.vue'
import PharmacyWarehousePage from '../pages/PharmacyWarehousePage.vue'
import TrainingCenterPage from '../pages/TrainingCenterPage.vue'
import DrugCatalogPage from '../pages/medication/DrugCatalogPage.vue'
import DrugPermissionManagementPage from '../pages/medication/permissions/DrugPermissionManagementPage.vue'
import { useAuthStore } from '../stores/auth'
import { pinia } from '../stores/pinia'
import { allowedSectionsForRole } from '../config/workspaceMenu'
import type { AppSection } from '../types/workspace'

const routeSectionMap: Record<string, AppSection> = {
  'nurse-followups': 'tasks',
  'model-dashboard': 'model-dashboard',
  'training-center': 'training-center',
  'model-operations': 'model-operations',
  'model-insight': 'insights',
  governance: 'governance',
  'role-workspaces': 'role-workspaces',
  'drug-management': 'drug-management',
  'drug-permission-management': 'drug-permission-management',
  pharmacy: 'pharmacy',
  coordination: 'coordination',
  'patient-detail': 'doctor',
}

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
        path: 'model-operations',
        name: 'model-operations',
        component: ModelOperationsPage,
      },
      {
        path: 'model-insight',
        name: 'model-insight',
        component: ModelInsightPage,
      },
      {
        path: 'governance',
        name: 'governance',
        component: GovernancePage,
      },
      {
        path: 'role-workspaces',
        name: 'role-workspaces',
        component: RoleWorkspacePage,
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
      {
        path: 'pharmacy',
        name: 'pharmacy',
        component: PharmacyWarehousePage,
      },
      {
        path: 'coordination',
        name: 'coordination',
        component: NurseFollowupsPage,
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
    path: '/patient-archive-print/:patientId',
    name: 'patient-archive-print',
    component: PatientArchivePrintPage,
    meta: {
      requiresAuth: true,
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

  if (authenticated && typeof to.name === 'string') {
    const section = routeSectionMap[to.name]
    const role = authStore.doctor?.role
    if (section && role && !allowedSectionsForRole(role).includes(section)) {
      return { path: '/', query: { denied: section } }
    }
  }

  return true
})

export default router
