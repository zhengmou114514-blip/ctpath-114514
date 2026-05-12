<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter, type RouteLocationRaw } from 'vue-router'
import { useWorkspaceController } from '../composables/useWorkspaceController'
import { provideWorkspaceContext } from '../composables/workspaceContext'
import AppShell from '../layouts/AppShell.vue'
import { allowedSectionsForRole } from '../config/workspaceMenu'
import { useAuthStore } from '../stores/auth'
import { pinia } from '../stores/pinia'
import type { AppSection } from '../types/workspace'

const workspace = useWorkspaceController()
provideWorkspaceContext(workspace)

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore(pinia)
const redirectingToLogin = ref(false)

const allowedSections = computed(() =>
  workspace.currentDoctor ? allowedSectionsForRole(workspace.currentDoctor.role) : []
)
const hasSectionAccess = computed(() =>
  workspace.currentDoctor ? allowedSections.value.includes(workspace.section) : true
)

function defaultSectionForCurrentRole(): AppSection {
  return allowedSections.value[0] ?? 'doctor'
}

const splitRouteSections: Record<string, AppSection> = {
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
}

const sectionToRouteName: Partial<Record<AppSection, string>> = {
  tasks: 'nurse-followups',
  contacts: 'nurse-followups',
  flow: 'nurse-followups',
  'model-dashboard': 'model-dashboard',
  'training-center': 'training-center',
  'model-operations': 'model-operations',
  insights: 'model-insight',
  governance: 'governance',
  'role-workspaces': 'role-workspaces',
  'drug-management': 'drug-management',
  'drug-permission-management': 'drug-permission-management',
  pharmacy: 'pharmacy',
  coordination: 'coordination',
}

function buildRouteForSection(nextSection: AppSection): RouteLocationRaw {
  if (nextSection === 'doctor') return { name: 'doctor-workbench' }

  if (nextSection === 'archive' || nextSection === 'data-quality' || nextSection === 'system') {
    if (nextSection === 'archive') return { name: 'doctor-patients' }
    if (nextSection === 'system') return { path: '/admin/audit' }
    return { name: 'home', query: { module: nextSection } }
  }

  if (nextSection === 'emr') {
    return {
      name: 'home',
      query: {
        module: 'emr',
      },
    }
  }

  if (nextSection === 'pharmacy') {
    return { name: 'pharmacy-medication-review' }
  }

  if (nextSection === 'coordination') {
    return workspace.currentDoctor?.role === 'nurse' ? { name: 'nurse-followups-review' } : { name: 'coordination' }
  }

  if (nextSection === 'role-workspaces') {
    return { name: 'admin-permissions' }
  }

  if (nextSection === 'tasks' || nextSection === 'contacts' || nextSection === 'flow') {
    if (nextSection === 'flow') return { name: 'nurse-followups-today' }
    if (nextSection === 'contacts') return { name: 'nurse-followups-records' }
    return { name: 'nurse-followups' }
  }

  if (nextSection === 'drug-management') return { name: 'pharmacy-drug-catalog' }
  if (nextSection === 'drug-permission-management') return { name: 'admin-drug-permissions' }
  if (nextSection === 'model-dashboard') return { name: 'admin-model-dashboard' }
  if (nextSection === 'governance') return { name: 'admin-governance' }
  if (nextSection === 'insights') return { name: 'doctor-risk' }

  const routeName = sectionToRouteName[nextSection] ?? 'home'
  return { name: routeName }
}

const isSplitWorkspaceRoute = computed(() => {
  const routeName = typeof route.name === 'string' ? route.name : ''
  return (
    Boolean(route.meta.section) ||
    Object.prototype.hasOwnProperty.call(splitRouteSections, routeName) ||
    routeName === 'patient-detail' ||
    routeName === 'nurse-followups' ||
    workspace.currentWorkspace === 'governance' ||
    workspace.currentWorkspace === 'followup' ||
    workspace.currentWorkspace === 'model-dashboard' ||
    workspace.currentWorkspace === 'model-operations' ||
    workspace.currentWorkspace === 'training-center' ||
    workspace.currentWorkspace === 'model-insight' ||
    workspace.currentWorkspace === 'role-workspaces' ||
    workspace.currentWorkspace === 'pharmacy' ||
    workspace.currentWorkspace === 'coordination' ||
    workspace.currentWorkspace === 'drug-management' ||
    workspace.currentWorkspace === 'drug-permission-management'
  )
})

function syncWorkspaceFromRoute() {
  if (!workspace.currentDoctor) return

  if (typeof route.name === 'string' && route.name === 'login') {
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
    window.setTimeout(() => {
      void router.replace(redirect)
    }, 0)
    return
  }

  const routeName = typeof route.name === 'string' ? route.name : ''
  if (routeName === 'patient-detail') return

  const moduleValue = typeof route.query.module === 'string' ? route.query.module : ''
  const requestedSection =
    moduleValue === 'archive' ||
    moduleValue === 'data-quality' ||
    moduleValue === 'system' ||
    moduleValue === 'tasks' ||
    moduleValue === 'contacts' ||
    moduleValue === 'flow' ||
    moduleValue === 'emr' ||
    moduleValue === 'pharmacy' ||
    moduleValue === 'coordination' ||
    moduleValue === 'governance' ||
    moduleValue === 'role-workspaces' ||
    moduleValue === 'drug-management' ||
    moduleValue === 'drug-permission-management'
      ? moduleValue
      : null

  const nextSection =
    routeName === 'home'
      ? requestedSection ?? 'doctor'
      : routeName === 'doctor-workbench'
        ? 'doctor'
        : routeName === 'doctor-patients'
          ? 'archive'
      : routeName === 'nurse-followups'
        ? requestedSection && (requestedSection === 'tasks' || requestedSection === 'contacts' || requestedSection === 'flow')
          ? requestedSection
          : 'tasks'
        : (route.meta.section as AppSection | undefined) ?? splitRouteSections[routeName] ?? 'doctor'
  const safeSection = allowedSections.value.includes(nextSection) ? nextSection : defaultSectionForCurrentRole()
  if (routeName.startsWith('patient-')) {
    if (workspace.section !== safeSection) {
      workspace.section = safeSection
    }
    return
  }

  if (workspace.section !== safeSection) {
    workspace.selectSection(safeSection)
  }
}

function syncRouteFromWorkspace() {
  if (!workspace.currentDoctor) return
  const routeName = typeof route.name === 'string' ? route.name : ''
  if (routeName === 'patient-detail' || routeName.startsWith('patient-')) return
  if (routeName !== 'home' && route.meta.section) return

  const targetRoute = buildRouteForSection(workspace.section)
  if (router.resolve(targetRoute).fullPath !== route.fullPath) {
    void router.replace(targetRoute)
  }
}

function ensureLoginRoute() {
  if (redirectingToLogin.value || workspace.currentDoctor || route.path === '/login') return

  redirectingToLogin.value = true
  void router.replace({
    path: '/login',
    query: {
      redirect: route.fullPath,
    },
  })
}

function handleSelectSection(nextSection: Parameters<typeof workspace.selectSection>[0]) {
  const currentRouteName = typeof route.name === 'string' ? route.name : ''
  if (!allowedSections.value.includes(nextSection)) {
    workspace.selectSection(defaultSectionForCurrentRole())
    return
  }
  workspace.selectSection(nextSection)

  if (currentRouteName === 'patient-detail' || currentRouteName.startsWith('patient-')) {
    void router.push(buildRouteForSection(nextSection))
    return
  }

  if (nextSection === 'doctor') {
    void router.push({ name: 'doctor-workbench' })
  }
}

function handleOpenArchive(payload: { patientId: string; focus?: 'overview' | 'events' }) {
  const focus = payload.focus === 'events' ? 'events' : 'overview'
  void workspace.openArchiveInNewTab(payload.patientId, focus)
}

function handleOpenFollowup(payload: { patientId?: string; section?: 'tasks' | 'contacts' | 'flow' }) {
  void workspace.openFollowupModule(payload.patientId || workspace.selectedPatientId || undefined, payload.section ?? 'tasks')
}

function handleBackToList() {
  if (workspace.currentWorkspace === 'archive') {
    workspace.backToArchiveList()
    return
  }
  workspace.backToDoctorList()
}

async function handleLogout() {
  redirectingToLogin.value = true
  workspace.logout()
  authStore.clearSession()

  try {
    await router.replace('/login')
  } catch (error) {
    redirectingToLogin.value = false
    throw error
  }
}

onMounted(async () => {
  await workspace.initialize()
  ensureLoginRoute()
})

watch(
  () => route.fullPath,
  () => {
    syncWorkspaceFromRoute()
  },
  { immediate: true }
)

watch(
  () => workspace.currentDoctor,
  (doctor) => {
    if (doctor) {
      redirectingToLogin.value = false
      syncWorkspaceFromRoute()
      return
    }

    ensureLoginRoute()
  }
)

watch(
  () => workspace.section,
  () => {
    syncRouteFromWorkspace()
  },
  { immediate: true }
)
</script>

<template>
  <AppShell
    v-if="workspace.currentDoctor"
    :doctor="workspace.currentDoctor"
    :active-section="workspace.section"
    :health="workspace.health"
    :patient-count="workspace.allPatients.length"
    :followup-count="workspace.followupItems.length"
    :selected-patient="workspace.selectedPatient"
    :error-message="workspace.permissionHint || workspace.screenError"
    :success-message="workspace.archiveSuccess"
    :loading="workspace.globalLoading"
    @select="handleSelectSection"
    @logout="handleLogout"
    @open-archive="handleOpenArchive"
    @open-followup="handleOpenFollowup"
    @back-to-list="handleBackToList"
  >
    <template #workspace>
      <section v-if="!hasSectionAccess" class="empty-state-card no-permission-card">
        <h3>无权限访问</h3>
        <p>当前角色暂无该业务权限，请联系管理员。</p>
      </section>

      <RouterView v-else-if="isSplitWorkspaceRoute" />
      <section v-else class="empty-state-card">
        <h3>正在进入工作区</h3>
        <p>系统正在根据当前角色和导航位置切换到对应页面。</p>
      </section>
    </template>
  </AppShell>

  <section v-else-if="!redirectingToLogin" class="workspace-auth-handoff">
    <p>正在进入登录页...</p>
  </section>
</template>
