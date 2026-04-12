<script setup lang="ts">
import { computed } from 'vue'
import type { PatientSummary } from '../services/types'

interface QualityIssueRow {
  patientId: string
  name: string
  disease: string
  reasons: string[]
}

const props = defineProps<{
  patients: PatientSummary[]
}>()

const emit = defineEmits<{
  (e: 'open', patientId: string): void
}>()

function archiveSourceLabel(value: string) {
  if (value === 'outpatient') return '门诊建档'
  if (value === 'import') return '批量导入'
  if (value === 'inpatient') return '住院转入'
  return value || '未标记来源'
}

const summary = computed(() => ({
  total: props.patients.length,
  missingMrn: props.patients.filter((item) => !item.medicalRecordNumber).length,
  missingPhone: props.patients.filter((item) => !item.phone).length,
  missingEmergency: props.patients.filter((item) => !item.emergencyContactPhone).length,
  pendingConsent: props.patients.filter((item) => item.consentStatus === 'pending').length,
  draftArchives: props.patients.filter((item) => item.archiveStatus === 'draft').length,
}))

const sourceStats = computed(() => {
  const counter = new Map<string, number>()
  for (const item of props.patients) {
    const key = archiveSourceLabel(item.archiveSource)
    counter.set(key, (counter.get(key) ?? 0) + 1)
  }
  return Array.from(counter.entries())
    .map(([label, value]) => ({ label, value }))
    .sort((left, right) => right.value - left.value)
    .slice(0, 4)
})

const qualityIssues = computed<QualityIssueRow[]>(() =>
  props.patients
    .map((item) => {
      const reasons: string[] = []
      if (!item.medicalRecordNumber) reasons.push('缺失 MRN')
      if (!item.phone) reasons.push('缺少联系电话')
      if (!item.emergencyContactPhone) reasons.push('缺少紧急联系人电话')
      if (item.consentStatus === 'pending') reasons.push('待签知情同意')
      if (item.archiveStatus === 'draft') reasons.push('档案仍为草稿')
      return {
        patientId: item.patientId,
        name: item.name,
        disease: item.primaryDisease,
        reasons,
      }
    })
    .filter((item) => item.reasons.length > 0)
    .sort((left, right) => right.reasons.length - left.reasons.length)
    .slice(0, 6)
)
</script>

<template>
  <section class="card archive-quality-board">
    <div class="panel-head">
      <div>
        <p class="eyebrow">MRMS Inspired</p>
        <h3>档案质控治理台</h3>
      </div>
      <span class="panel-meta">参考医院病案管理模块的思路，把“建档”进一步推进到“建档后质控”。</span>
    </div>

    <div class="archive-quality-metrics">
      <article class="archive-quality-metric">
        <span>档案总量</span>
        <strong>{{ summary.total }}</strong>
      </article>
      <article class="archive-quality-metric warning">
        <span>缺失 MRN</span>
        <strong>{{ summary.missingMrn }}</strong>
      </article>
      <article class="archive-quality-metric warning">
        <span>缺少联系电话</span>
        <strong>{{ summary.missingPhone }}</strong>
      </article>
      <article class="archive-quality-metric warning">
        <span>缺少紧急联系人</span>
        <strong>{{ summary.missingEmergency }}</strong>
      </article>
      <article class="archive-quality-metric warning">
        <span>待签知情同意</span>
        <strong>{{ summary.pendingConsent }}</strong>
      </article>
      <article class="archive-quality-metric warning">
        <span>草稿档案</span>
        <strong>{{ summary.draftArchives }}</strong>
      </article>
    </div>

    <div class="archive-quality-grid">
      <article class="archive-quality-section">
        <strong>待治理档案</strong>
        <button
          v-for="item in qualityIssues"
          :key="item.patientId"
          class="archive-quality-row"
          @click="emit('open', item.patientId)"
        >
          <div>
            <span>{{ item.name }} / {{ item.patientId }}</span>
            <small>{{ item.disease }}</small>
          </div>
          <small>{{ item.reasons.join(' / ') }}</small>
        </button>
        <p v-if="!qualityIssues.length" class="empty-note">当前档案字段完整度较好，没有明显待治理项目。</p>
      </article>

      <article class="archive-quality-section">
        <strong>建档来源分布</strong>
        <div class="archive-source-list">
          <div
            v-for="item in sourceStats"
            :key="item.label"
            class="archive-source-row"
          >
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
          </div>
        </div>
        <p class="role-focus-note">这部分用于说明当前系统已经不只是在录患者信息，而是开始向医院主索引、导入来源和资料治理方向靠拢。</p>
      </article>
    </div>
  </section>
</template>
