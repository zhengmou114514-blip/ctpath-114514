import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import AppWorkspacePage from '../pages/AppWorkspacePage.vue'
import LoginPage from '../pages/LoginPage.vue'
import ModelDashboardPage from '../pages/ModelDashboardPage.vue'
import ModelInsightPage from '../pages/ModelInsightPage.vue'
import RoleWorkspacePage from '../pages/RoleWorkspacePage.vue'
import PatientArchivePrintPage from '../pages/PatientArchivePrintPage.vue'
import GovernancePage from '../pages/GovernancePage.vue'
import NurseFollowupsPage from '../pages/NurseFollowupsPage.vue'
import PharmacyWarehousePage from '../pages/PharmacyWarehousePage.vue'
import DoctorWorkbenchRoutePage from '../pages/DoctorWorkbenchRoutePage.vue'
import PatientArchiveRoutePage from '../pages/PatientArchiveRoutePage.vue'
import AdminAuditRoutePage from '../pages/AdminAuditRoutePage.vue'
import DrugCatalogPage from '../pages/medication/DrugCatalogPage.vue'
import DrugPermissionManagementPage from '../pages/medication/permissions/DrugPermissionManagementPage.vue'
import NoAccessPage from '../pages/NoAccessPage.vue'
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
  'doctor-workbench': 'doctor',
  'doctor-patients': 'archive',
  'doctor-risk': 'insights',
  'patient-overview': 'archive',
  'patient-profile': 'archive',
  'patient-contacts': 'archive',
  'patient-timeline': 'archive',
  'patient-attachments': 'archive',
  'patient-medications': 'archive',
  'patient-risk': 'insights',
  'patient-followups': 'archive',
  'nurse-followups-today': 'flow',
  'nurse-followups-missed': 'contacts',
  'nurse-followups-records': 'contacts',
  'nurse-followups-review': 'coordination',
  'nurse-followups-stats': 'tasks',
  'pharmacy-drug-catalog': 'drug-management',
  'pharmacy-drug-status': 'drug-management',
  'pharmacy-medication-review': 'pharmacy',
  'admin-permissions': 'role-workspaces',
  'admin-drug-permissions': 'drug-permission-management',
  'admin-model-dashboard': 'model-dashboard',
  'admin-governance': 'governance',
  'admin-governance-issues': 'governance',
  'admin-audit': 'system',
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
        path: '/doctor/workbench',
        name: 'doctor-workbench',
        component: DoctorWorkbenchRoutePage,
        meta: { section: 'doctor', roles: ['doctor'], breadcrumb: ['慢病管理门诊', '医生站', '医生工作台'] },
      },
      {
        path: '/doctor/patients',
        name: 'doctor-patients',
        component: PatientArchiveRoutePage,
        meta: { section: 'archive', roles: ['doctor'], breadcrumb: ['慢病管理门诊', '医生站', '患者档案'] },
      },
      {
        path: '/doctor/risk',
        name: 'doctor-risk',
        component: ModelInsightPage,
        meta: { section: 'insights', roles: ['doctor'], breadcrumb: ['慢病管理门诊', '医生站', '风险评估'] },
      },
      {
        path: '/doctor/patients/:patientId',
        component: () => import('../pages/patient/PatientDetailLayout.vue'),
        meta: { section: 'archive', roles: ['doctor'], breadcrumb: ['慢病管理门诊', '医生站', '患者档案'] },
        children: [
          { path: '', redirect: { name: 'patient-overview' } },
          {
            path: 'overview',
            name: 'patient-overview',
            component: () => import('../pages/patient/PatientOverviewPage.vue'),
            meta: { section: 'archive', roles: ['doctor'], breadcrumb: ['慢病管理门诊', '医生站', '患者档案', '总览'] },
          },
          {
            path: 'profile',
            name: 'patient-profile',
            component: () => import('../pages/patient/PatientProfilePage.vue'),
            meta: { section: 'archive', roles: ['doctor'], breadcrumb: ['慢病管理门诊', '医生站', '患者档案', '基本档案'] },
          },
          {
            path: 'contacts',
            name: 'patient-contacts',
            component: () => import('../pages/patient/PatientContactPage.vue'),
            meta: { section: 'archive', roles: ['doctor'], breadcrumb: ['慢病管理门诊', '医生站', '患者档案', '联系记录'] },
          },
          {
            path: 'timeline',
            name: 'patient-timeline',
            component: () => import('../pages/patient/PatientTimelinePage.vue'),
            meta: { section: 'archive', roles: ['doctor'], breadcrumb: ['慢病管理门诊', '医生站', '患者档案', '病程时间线'] },
          },
          {
            path: 'attachments',
            name: 'patient-attachments',
            component: () => import('../pages/patient/PatientAttachmentsPage.vue'),
            meta: { section: 'archive', roles: ['doctor'], breadcrumb: ['慢病管理门诊', '医生站', '患者档案', '附件资料'] },
          },
          {
            path: 'medications',
            name: 'patient-medications',
            component: () => import('../pages/patient/PatientMedicationsPage.vue'),
            meta: { section: 'archive', roles: ['doctor'], breadcrumb: ['慢病管理门诊', '医生站', '患者档案', '当前用药'] },
          },
          {
            path: 'risk',
            name: 'patient-risk',
            component: () => import('../pages/patient/PatientRiskPage.vue'),
            meta: { section: 'insights', roles: ['doctor'], breadcrumb: ['慢病管理门诊', '医生站', '患者档案', '风险评估'] },
          },
          {
            path: 'followups',
            name: 'patient-followups',
            component: () => import('../pages/patient/PatientFollowupsPage.vue'),
            meta: { section: 'archive', roles: ['doctor'], breadcrumb: ['慢病管理门诊', '医生站', '患者档案', '随访记录'] },
          },
        ],
      },
      {
        path: '/nurse/followups/today',
        name: 'nurse-followups-today',
        component: NurseFollowupsPage,
        meta: { section: 'flow', roles: ['nurse'], breadcrumb: ['慢病管理门诊', '护士站', '今日随访'] },
      },
      {
        path: '/nurse/followups/missed',
        name: 'nurse-followups-missed',
        component: NurseFollowupsPage,
        meta: { section: 'contacts', roles: ['nurse'], breadcrumb: ['慢病管理门诊', '护士站', '未接通任务'] },
      },
      {
        path: '/nurse/followups/records',
        name: 'nurse-followups-records',
        component: NurseFollowupsPage,
        meta: { section: 'contacts', roles: ['nurse'], breadcrumb: ['慢病管理门诊', '护士站', '联系记录'] },
      },
      {
        path: '/nurse/followups/review',
        name: 'nurse-followups-review',
        component: NurseFollowupsPage,
        meta: { section: 'coordination', roles: ['nurse'], breadcrumb: ['慢病管理门诊', '护士站', '医生复核'] },
      },
      {
        path: '/nurse/followups/stats',
        name: 'nurse-followups-stats',
        component: NurseFollowupsPage,
        meta: { section: 'tasks', roles: ['nurse'], breadcrumb: ['慢病管理门诊', '护士站', '随访统计'] },
      },
      {
        path: '/pharmacy/drugs/catalog',
        name: 'pharmacy-drug-catalog',
        component: DrugCatalogPage,
        meta: { section: 'drug-management', roles: ['pharmacist'], breadcrumb: ['药事管理', '药品目录'] },
      },
      {
        path: '/pharmacy/drugs/status',
        name: 'pharmacy-drug-status',
        component: DrugCatalogPage,
        meta: { section: 'drug-management', roles: ['pharmacist'], breadcrumb: ['药事管理', '药品状态'] },
      },
      {
        path: '/pharmacy/medications/review',
        name: 'pharmacy-medication-review',
        component: PharmacyWarehousePage,
        meta: { section: 'pharmacy', roles: ['pharmacist'], breadcrumb: ['药事管理', '用药复核'] },
      },
      {
        path: '/admin/permissions',
        name: 'admin-permissions',
        component: RoleWorkspacePage,
        meta: { section: 'role-workspaces', roles: ['admin'], breadcrumb: ['系统管理', '权限配置'] },
      },
      {
        path: '/admin/drug-permissions',
        name: 'admin-drug-permissions',
        component: DrugPermissionManagementPage,
        meta: { section: 'drug-permission-management', roles: ['admin'], breadcrumb: ['系统管理', '药品权限管理'] },
      },
      {
        path: '/admin/model-dashboard',
        name: 'admin-model-dashboard',
        component: ModelDashboardPage,
        meta: { section: 'model-dashboard', roles: ['admin'], breadcrumb: ['模型与治理', '模型看板'] },
      },
      {
        path: '/admin/governance',
        name: 'admin-governance',
        component: GovernancePage,
        meta: { section: 'governance', roles: ['admin'], breadcrumb: ['模型与治理', '治理中心'] },
      },
      {
        path: '/admin/governance/issues',
        name: 'admin-governance-issues',
        component: GovernancePage,
        meta: { section: 'governance', roles: ['admin'], breadcrumb: ['模型与治理', '异常记录'] },
      },
      {
        path: '/admin/audit',
        name: 'admin-audit',
        component: AdminAuditRoutePage,
        meta: { section: 'system', roles: ['admin'], breadcrumb: ['系统管理', '审计日志'] },
      },
      {
        path: 'patient-detail/:patientId?',
        name: 'patient-detail',
        redirect: (to) => {
          const patientId = typeof to.params.patientId === 'string' ? to.params.patientId : ''
          return patientId ? { name: 'patient-overview', params: { patientId } } : { name: 'doctor-patients' }
        },
      },
      {
        path: '/nurse/followups',
        name: 'nurse-followups',
        component: NurseFollowupsPage,
        meta: { section: 'tasks', roles: ['nurse'], breadcrumb: ['慢病管理门诊', '护士站', '随访工作台'] },
      },
      {
        path: 'model-dashboard',
        name: 'model-dashboard',
        redirect: { name: 'admin-model-dashboard' },
      },
      {
        path: 'training-center',
        name: 'training-center',
        redirect: { name: 'admin-model-dashboard' },
      },
      {
        path: 'model-operations',
        name: 'model-operations',
        redirect: { name: 'admin-model-dashboard' },
      },
      {
        path: 'model-insight',
        name: 'model-insight',
        redirect: { name: 'doctor-risk' },
      },
      {
        path: 'governance',
        name: 'governance',
        redirect: { name: 'admin-governance' },
      },
      {
        path: 'role-workspaces',
        name: 'role-workspaces',
        redirect: { name: 'admin-permissions' },
      },
      {
        path: 'drug-management',
        name: 'drug-management',
        redirect: { name: 'pharmacy-drug-catalog' },
      },
      {
        path: 'drug-permission-management',
        name: 'drug-permission-management',
        redirect: { name: 'admin-drug-permissions' },
      },
      {
        path: 'pharmacy',
        name: 'pharmacy',
        redirect: { name: 'pharmacy-medication-review' },
      },
      {
        path: 'coordination',
        name: 'coordination',
        redirect: { name: 'nurse-followups-review' },
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
    path: '/no-access',
    name: 'no-access',
    component: NoAccessPage,
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
    const section = (to.meta.section as AppSection | undefined) ?? routeSectionMap[to.name]
    const role = authStore.doctor?.role
    const routeRoles = to.meta.roles as string[] | undefined
    if (routeRoles && role && !routeRoles.includes(role)) {
      return { name: 'no-access' }
    }
    if (section && role && !allowedSectionsForRole(role).includes(section)) {
      return { name: 'no-access' }
    }
  }

  return true
})

export default router
