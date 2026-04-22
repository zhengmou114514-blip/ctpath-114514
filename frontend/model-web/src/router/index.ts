import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { readStoredModelSession } from '../stores/modelSession'
import LoginPage from '../pages/LoginPage.vue'
import ModelLayout from '../layouts/ModelLayout.vue'
import ModelDashboardPage from '../pages/ModelDashboardPage.vue'
import DatasetManagementPage from '../pages/DatasetManagementPage.vue'
import TrainingCenterPage from '../pages/TrainingCenterPage.vue'
import ModelVersionPage from '../pages/ModelVersionPage.vue'
import ModelOperationsPage from '../pages/ModelOperationsPage.vue'

const routes: RouteRecordRaw[] = [
  { path: '/login', name: 'model-login', component: LoginPage },
  {
    path: '/',
    component: ModelLayout,
    meta: { requiresAuth: true },
    children: [
      { path: '', name: 'model-home', component: ModelDashboardPage },
      { path: 'datasets', name: 'model-datasets', component: DatasetManagementPage },
      { path: 'training', name: 'model-training', component: TrainingCenterPage },
      { path: 'versions', name: 'model-versions', component: ModelVersionPage },
      { path: 'operations', name: 'model-operations', component: ModelOperationsPage },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const session = readStoredModelSession()
  const authenticated = Boolean(session?.token && session?.user)
  if (to.meta.requiresAuth !== false && !authenticated && to.path !== '/login') {
    return { path: '/login', query: { redirect: to.fullPath } }
  }
  if (authenticated && to.path === '/login') {
    return { path: '/' }
  }
  return true
})

export default router
