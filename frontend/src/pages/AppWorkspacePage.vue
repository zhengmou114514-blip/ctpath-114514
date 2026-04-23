<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter, type RouteLocationRaw } from 'vue-router'
import { useWorkspaceController } from '../composables/useWorkspaceController'
import { provideWorkspaceContext } from '../composables/workspaceContext'
import AppShell from '../layouts/AppShell.vue'
import DoctorDashboardPage from './DoctorDashboardPage.vue'
import EmrPage from './EmrPage.vue'
import FollowupWorkbenchPage from './FollowupWorkbenchPage.vue'
import RoleWorkspacePage from './RoleWorkspacePage.vue'
import PatientArchivePage from './PatientArchivePage.vue'
import SystemCenterPage from './SystemCenterPage.vue'
import type { AppSection } from '../types/workspace'

const workspace = useWorkspaceController()
provideWorkspaceContext(workspace)

const route = useRoute()
const router = useRouter()
const redirectingToLogin = ref(false)

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
  if (nextSection === 'doctor') return { name: 'home' }

  if (nextSection === 'archive' || nextSection === 'data-quality' || nextSection === 'system') {
    return {
      name: 'home',
      query: {
        module: nextSection,
      },
    }
  }

  if (nextSection === 'emr') {
    return {
      name: 'home',
      query: {
        module: 'emr',
      },
    }
  }

  if (nextSection === 'pharmacy' || nextSection === 'coordination') {
    return {
      name: nextSection,
    }
  }

  if (nextSection === 'role-workspaces') {
    return {
      name: 'role-workspaces',
    }
  }

  if (nextSection === 'tasks' || nextSection === 'contacts' || nextSection === 'flow') {
    return {
      name: 'nurse-followups',
      query: {
        module: nextSection,
      },
    }
  }

  const routeName = sectionToRouteName[nextSection] ?? 'home'
  return { name: routeName }
}

const isSplitWorkspaceRoute = computed(() => {
  const routeName = typeof route.name === 'string' ? route.name : ''
  return (
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
      : routeName === 'nurse-followups'
        ? requestedSection && (requestedSection === 'tasks' || requestedSection === 'contacts' || requestedSection === 'flow')
          ? requestedSection
          : 'tasks'
        : splitRouteSections[routeName] ?? 'doctor'
  if (workspace.section !== nextSection) {
    workspace.selectSection(nextSection)
  }
}

function syncRouteFromWorkspace() {
  if (!workspace.currentDoctor) return
  if (route.name === 'patient-detail') return

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
  workspace.selectSection(nextSection)

  if (currentRouteName === 'patient-detail') {
    void router.push(buildRouteForSection(nextSection))
    return
  }

  if (nextSection === 'doctor') {
    void router.push({ name: 'home' })
  }
}

async function handleOpenPatientDetail(patientId: string) {
  const loaded = await workspace.openPatient(patientId, 'doctor')
  if (loaded) {
    void router.push({ name: 'patient-detail', params: { patientId } })
  }
}

function handleOpenArchive(payload: { patientId: string; focus?: 'overview' | 'events' }) {
  const focus = payload.focus === 'events' ? 'events' : 'overview'
  void workspace.openArchiveInNewTab(payload.patientId, focus)
}

function handleOpenFollowup(payload: { patientId?: string; section?: 'tasks' | 'contacts' | 'flow' }) {
  void workspace.openFollowupModule(payload.patientId || workspace.selectedPatientId || undefined, payload.section ?? 'tasks')
}

function handlePrintArchive(patientId?: string) {
  const targetPatientId = patientId || workspace.selectedPatientId || workspace.allPatients[0]?.patientId
  if (!targetPatientId) {
    return
  }

  void router.push({ name: 'patient-archive-print', params: { patientId: targetPatientId } })
}

function handleDoctorOpenArchive(payload: { patientId: string; focus?: 'overview' | 'events' }) {
  void workspace.openArchiveInNewTab(payload.patientId, payload.focus ?? 'overview')
}

function handleDoctorOpenFollowup(payload: { patientId: string; section?: 'tasks' | 'contacts' | 'flow' }) {
  void workspace.openFollowupModule(payload.patientId, payload.section ?? 'tasks')
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
  () => route.name,
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
      <RouterView v-if="isSplitWorkspaceRoute" />

      <DoctorDashboardPage
        v-else-if="workspace.currentWorkspace === 'doctor'"
        :all-patients="workspace.allPatients"
        :patients="workspace.visiblePendingPatients"
        :selected-patient="workspace.selectedPatient"
        :loading-patients="workspace.loadingPatients"
        :loading-patient="workspace.loadingPatient"
        :no-permission="workspace.doctorNoPermission"
        :search-text="workspace.workspaceSearchText"
        :risk-filter="workspace.workspaceRiskFilter"
        :risk-options="workspace.riskOptions"
        @update:search-text="workspace.workspaceSearchText = $event"
        @update:risk-filter="workspace.workspaceRiskFilter = $event"
        @open="workspace.openPatient($event, 'doctor')"
        @open-detail="handleOpenPatientDetail"
        @open-archive="handleDoctorOpenArchive"
        @open-followup="handleDoctorOpenFollowup"
      />

      <PatientArchivePage
        v-else-if="workspace.currentWorkspace === 'archive'"
        :mode="workspace.archiveMode"
        :all-patients="workspace.allPatients"
        :patients="workspace.archivePagedPatients"
        :loading-patients="workspace.loadingPatients"
        :current-page="workspace.archivePage"
        :total-pages="workspace.archiveTotalPages"
        :patient-count="workspace.allPatients.length"
        :patient-form="workspace.patientForm"
        :selected-patient-id="workspace.selectedPatientId"
        :event-form="workspace.eventForm"
        :relation-options="workspace.relationOptions"
        :saving-patient="workspace.savingPatient"
        :saving-event="workspace.savingEvent"
        :timeline-items="workspace.selectedPatient?.timeline ?? []"
        :selected-patient="workspace.selectedPatient"
        :focus-section="workspace.archiveFocusSection"
        :importing-archive="workspace.importingArchive"
        :import-result-text="workspace.importResultText"
        :doctor-role="workspace.currentDoctor.role"
        :no-permission="workspace.archiveNoPermission"
        :model-unavailable="workspace.modelUnavailable"
        @open="workspace.openPatient($event, 'archive')"
        @create="workspace.openCreateModule"
        @import="workspace.openImportModule"
        @export="handlePrintArchive"
        @prev-page="workspace.prevArchivePage"
        @next-page="workspace.nextArchivePage"
        @submit-archive="workspace.submitArchive"
        @submit-event="workspace.submitEvent"
        @submit-import="workspace.submitImport"
        @prepare-new="workspace.openCreateModule"
        @back="workspace.backToArchiveList"
        @open-followup="handleOpenFollowup"
      />

      <EmrPage
        v-else-if="workspace.currentWorkspace === 'emr'"
        :all-patients="workspace.allPatients"
        :selected-patient="workspace.selectedPatient"
        :followup-items="workspace.followupItems"
        :loading="workspace.loadingPatients || workspace.loadingPatient"
        @open-patient="workspace.openPatient($event, 'doctor')"
        @open-archive="handleOpenArchive"
        @open-followup="handleOpenFollowup"
      />

      <FollowupWorkbenchPage
        v-else-if="workspace.currentWorkspace === 'followup'"
        :loading="workspace.loadingBoards"
        :loading-task-action="workspace.loadingTaskStatus || workspace.loadingEncounterStatus"
        :followup-items="workspace.followupItems"
        :flow-board-items="workspace.flowBoardItems"
        :selected-patient-id="workspace.followupFocusPatientId"
        :saving-contact-log="workspace.savingContactLog"
        :doctor-role="workspace.currentDoctor.role"
        :no-permission="workspace.followupNoPermission"
        :model-unavailable="workspace.modelUnavailable"
        :selected-patient="workspace.selectedPatient"
        @open-patient="workspace.openPatient($event, 'doctor')"
        @open-archive="workspace.openArchiveInNewTab"
        @complete-task="workspace.changeOutpatientTaskStatus($event.patientId, $event.taskId, workspace.taskStatusCompleted)"
        @close-task="workspace.changeOutpatientTaskStatus($event.patientId, $event.taskId, workspace.taskStatusClosed)"
        @submit-contact-log="workspace.submitContactLog"
      />

      <RoleWorkspacePage v-else-if="workspace.currentWorkspace === 'role-workspaces'" />

      <SystemCenterPage
        v-else-if="workspace.currentWorkspace === 'system'"
        :doctor="workspace.currentDoctor"
        :health="workspace.health"
      />

      <section v-else class="empty-state-card">
        <h3>模块正在整理中</h3>
        <p>当前工作区尚未挂载可展示内容，请返回医生工作台、患者档案或随访任务继续操作。</p>
      </section>
    </template>
  </AppShell>

  <section v-else-if="!redirectingToLogin" class="workspace-auth-handoff">
    <p>正在进入登录页...</p>
  </section>
</template>
