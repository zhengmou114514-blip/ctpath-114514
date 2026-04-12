<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import DetailHeaderCard from '../components/patient-detail/DetailHeaderCard.vue'
import FollowupPlanPanel from '../components/patient-detail/FollowupPlanPanel.vue'
import InsightPanel from '../components/patient-detail/InsightPanel.vue'
import LeftProfilePanel from '../components/patient-detail/LeftProfilePanel.vue'
import CourseTimelinePanel from '../components/patient-detail/CourseTimelinePanel.vue'
import { getPatientCase, getPatientQuadruples, predictPatient } from '../services/api'
import type { PatientCase, PatientQuadruple, PredictResponse } from '../services/types'

const props = defineProps<{
  patientId: string
}>()

const emit = defineEmits<{
  (e: 'back'): void
}>()

const patient = ref<PatientCase | null>(null)
const quadruples = ref<PatientQuadruple[]>([])
const prediction = ref<PredictResponse | null>(null)

const loadingPatient = ref(false)
const loadingPredict = ref(false)
const screenError = ref('')

const hasPatient = computed(() => Boolean(patient.value))

async function loadPatientDetail(id: string) {
  if (!id) return
  loadingPatient.value = true
  screenError.value = ''

  try {
    const [patientRes, quadruplesRes] = await Promise.all([getPatientCase(id), getPatientQuadruples(id)])
    patient.value = patientRes
    quadruples.value = quadruplesRes
    prediction.value = null
  } catch (error) {
    screenError.value = error instanceof Error ? error.message : '加载患者详情失败'
    patient.value = null
    quadruples.value = []
  } finally {
    loadingPatient.value = false
  }
}

async function refreshPrediction() {
  if (!patient.value) return
  loadingPredict.value = true
  screenError.value = ''

  try {
    prediction.value = await predictPatient({
      patientId: patient.value.patientId,
      asOfTime: patient.value.lastVisit,
      topk: 3,
    })
  } catch (error) {
    screenError.value = error instanceof Error ? error.message : '预测失败'
  } finally {
    loadingPredict.value = false
  }
}

watch(
  () => props.patientId,
  (id) => {
    void loadPatientDetail(id)
  },
  { immediate: true }
)

onMounted(() => {
  if (props.patientId) {
    void loadPatientDetail(props.patientId)
  }
})
</script>

<template>
  <section class="patient-detail-page">
    <div class="page-head">
      <button class="secondary-button" @click="emit('back')">返回患者列表</button>
      <p class="error-text" v-if="screenError">{{ screenError }}</p>
    </div>

    <div v-if="loadingPatient" class="empty-card">患者详情加载中...</div>
    <div v-else-if="!hasPatient" class="empty-card">未找到患者数据</div>

    <template v-else>
      <DetailHeaderCard :patient="patient!" />

      <section class="detail-grid">
        <LeftProfilePanel :patient="patient!" />
        <CourseTimelinePanel :timeline="patient!.timeline" :quadruples="quadruples" />
        <InsightPanel :patient="patient!" :prediction-result="prediction" :loading-predict="loadingPredict" @predict="refreshPrediction" />
      </section>

      <FollowupPlanPanel :patient="patient!" />
    </template>
  </section>
</template>

<style scoped>
.patient-detail-page {
  display: grid;
  gap: 12px;
}

.page-head {
  display: flex;
  align-items: center;
  gap: 10px;
}

.detail-grid {
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr) 360px;
  gap: 12px;
  align-items: start;
}

@media (max-width: 1400px) {
  .detail-grid {
    grid-template-columns: 1fr;
  }
}
</style>
