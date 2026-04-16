<script setup lang="ts">
import { ref, watch } from 'vue'
import AppSidebar from '../components/AppSidebar.vue'
import PatientContextBar from '../components/PatientContextBar.vue'
import RoleWorkspaceBanner from '../components/RoleWorkspaceBanner.vue'
import WorkspaceTopbar from '../components/WorkspaceTopbar.vue'
import type { DoctorUser, HealthResponse, PatientCase } from '../services/types'
import type { AppSection } from '../types/workspace'

const props = defineProps<{
  doctor: DoctorUser
  activeSection: AppSection
  health: HealthResponse | null
  patientCount: number
  followupCount: number
  selectedPatient: PatientCase | null
  errorMessage: string
  successMessage: string
  loading: boolean
}>()

const emit = defineEmits<{
  (e: 'select', section: AppSection): void
  (e: 'logout'): void
  (e: 'open-archive', payload: { patientId: string; focus?: 'overview' | 'events' }): void
  (e: 'open-followup', payload: { patientId: string; section?: 'tasks' | 'contacts' | 'flow' }): void
  (e: 'back-to-list'): void
}>()

// 本地状态：用于控制提示的显示和自动消失
const showError = ref(false)
const showSuccess = ref(false)

// 监听 errorMessage 变化，显示错误提示
watch(() => props.errorMessage, (newVal) => {
  if (newVal) {
    showError.value = true
    // 5秒后自动隐藏
    setTimeout(() => {
      showError.value = false
    }, 5000)
  }
})

// 监听 successMessage 变化，显示成功提示
watch(() => props.successMessage, (newVal) => {
  if (newVal) {
    showSuccess.value = true
    // 3秒后自动隐藏
    setTimeout(() => {
      showSuccess.value = false
    }, 3000)
  }
})
</script>

<template>
  <div class="app-shell" :class="`app-role-${doctor.role}`">
    <AppSidebar
      :active-section="activeSection"
      :doctor="doctor"
      :health="health"
      :patient-count="patientCount"
      :followup-count="followupCount"
      @select="emit('select', $event)"
      @logout="emit('logout')"
    />

    <main class="main-shell">
      <p v-if="loading" class="workspace-status-pill">正在加载工作台数据...</p>
      
      <!-- 增强错误提示：红色背景，图标，自动消失 -->
      <transition name="slide-fade">
        <div v-if="showError && errorMessage" class="error-banner-enhanced">
          <span class="banner-icon">⚠️</span>
          <span class="banner-text">{{ errorMessage }}</span>
          <button class="banner-close" @click="showError = false">✕</button>
        </div>
      </transition>
      
      <!-- 增强成功提示：绿色背景，图标，自动消失 -->
      <transition name="slide-fade">
        <div v-if="showSuccess && successMessage" class="success-banner-enhanced">
          <span class="banner-icon">✓</span>
          <span class="banner-text">{{ successMessage }}</span>
          <button class="banner-close" @click="showSuccess = false">✕</button>
        </div>
      </transition>

      <WorkspaceTopbar :doctor="doctor" :section="activeSection" :health="health" />
      <RoleWorkspaceBanner
        :doctor="doctor"
        :section="activeSection"
        :patient-count="patientCount"
        :followup-count="followupCount"
      />

      <PatientContextBar
        v-if="props.selectedPatient"
        :patient="props.selectedPatient"
        @open-archive="emit('open-archive', $event)"
        @open-followup="emit('open-followup', $event)"
        @back-to-list="emit('back-to-list')"
      />

      <slot name="workspace" />

      <slot v-if="$slots['bottom-panel']" name="bottom-panel" />
    </main>
  </div>
</template>

<style scoped>
/* 增强错误提示样式 */
.error-banner-enhanced {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  border-radius: 10px;
  background: linear-gradient(135deg, #fff5f5 0%, #fed7d7 100%);
  border: 1px solid #fc8181;
  box-shadow: 0 2px 8px rgba(193, 74, 60, 0.15);
  margin-bottom: 16px;
}

.banner-icon {
  font-size: 18px;
  flex-shrink: 0;
}

.banner-text {
  flex: 1;
  color: #c53030;
  font-weight: 600;
  font-size: 14px;
}

.banner-close {
  background: transparent;
  border: none;
  color: #c53030;
  font-size: 16px;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: background 0.2s;
}

.banner-close:hover {
  background: rgba(193, 74, 60, 0.1);
}

/* 增强成功提示样式 */
.success-banner-enhanced {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  border-radius: 10px;
  background: linear-gradient(135deg, #f0fff4 0%, #c6f6d5 100%);
  border: 1px solid #68d391;
  box-shadow: 0 2px 8px rgba(56, 161, 105, 0.15);
  margin-bottom: 16px;
}

.success-banner-enhanced .banner-icon {
  color: #38a169;
  font-weight: bold;
}

.success-banner-enhanced .banner-text {
  color: #276749;
  font-weight: 600;
  font-size: 14px;
}

.success-banner-enhanced .banner-close {
  color: #38a169;
}

.success-banner-enhanced .banner-close:hover {
  background: rgba(56, 161, 105, 0.1);
}

/* 过渡动画 */
.slide-fade-enter-active {
  transition: all 0.3s ease;
}

.slide-fade-leave-active {
  transition: all 0.2s ease;
}

.slide-fade-enter-from {
  transform: translateY(-10px);
  opacity: 0;
}

.slide-fade-leave-to {
  transform: translateY(-10px);
  opacity: 0;
}
</style>

