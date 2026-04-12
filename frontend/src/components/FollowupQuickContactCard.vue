<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { ContactLogCreatePayload } from '../services/types'

interface QuickContactCandidate {
  patientId: string
  label: string
}

const props = defineProps<{
  candidates: QuickContactCandidate[]
  selectedPatientId?: string
  saving: boolean
}>()

const emit = defineEmits<{
  (e: 'submit', payload: { patientId: string; payload: ContactLogCreatePayload }): void
  (e: 'open-patient', patientId: string): void
}>()

const quickContactPatientId = ref('')
const contactTime = ref(new Date().toISOString().slice(0, 16))
const contactType = ref<ContactLogCreatePayload['contactType']>('phone')
const contactTarget = ref<ContactLogCreatePayload['contactTarget']>('patient')
const contactResult = ref<ContactLogCreatePayload['contactResult']>('reached')
const contactNextDate = ref('')
const contactNote = ref('')

const selectedPatientLabel = computed(
  () => props.candidates.find((item) => item.patientId === quickContactPatientId.value)?.label ?? '未选择患者'
)

function submitQuickContactLog() {
  if (!quickContactPatientId.value) return
  emit('submit', {
    patientId: quickContactPatientId.value,
    payload: {
      contactTime: contactTime.value,
      contactType: contactType.value,
      contactTarget: contactTarget.value,
      contactResult: contactResult.value,
      note: contactNote.value.trim(),
      nextContactDate: contactNextDate.value || undefined,
    },
  })
  contactResult.value = 'reached'
  contactNote.value = ''
  contactNextDate.value = ''
}

watch(
  () => [props.selectedPatientId, props.candidates.length] as const,
  () => {
    if (props.selectedPatientId && props.candidates.some((item) => item.patientId === props.selectedPatientId)) {
      quickContactPatientId.value = props.selectedPatientId
      return
    }
    if (!quickContactPatientId.value && props.candidates.length) {
      const firstCandidate = props.candidates[0]
      if (firstCandidate) {
        quickContactPatientId.value = firstCandidate.patientId
      }
    }
  },
  { immediate: true }
)
</script>

<template>
  <article class="card quick-entry-card followup-quick-contact-card">
    <div class="panel-head">
      <div>
        <p class="eyebrow">快速录入</p>
        <h3>电话随访结果</h3>
      </div>
      <span class="panel-meta">适合护士或慢病管理师在随访工作台直接登记本次联系结果</span>
    </div>

    <div class="mobile-contact-patient-strip">
      <span class="data-label">当前患者</span>
      <strong>{{ selectedPatientLabel }}</strong>
    </div>

    <div class="form-grid mobile-contact-grid">
      <label class="field">
        <span>患者</span>
        <select v-model="quickContactPatientId">
          <option v-for="item in props.candidates" :key="item.patientId" :value="item.patientId">{{ item.label }}</option>
        </select>
      </label>
      <label class="field">
        <span>联系时间</span>
        <input v-model="contactTime" type="datetime-local" />
      </label>
      <label class="field">
        <span>联系类型</span>
        <select v-model="contactType">
          <option value="phone">电话随访</option>
          <option value="family">家属联系</option>
          <option value="wechat">线上沟通</option>
          <option value="outpatient">门诊复联</option>
        </select>
      </label>
      <label class="field">
        <span>联系对象</span>
        <select v-model="contactTarget">
          <option value="patient">患者本人</option>
          <option value="emergency_contact">紧急联系人</option>
        </select>
      </label>
      <label class="field">
        <span>联系结果</span>
        <select v-model="contactResult">
          <option value="reached">已接通</option>
          <option value="missed">未接通</option>
          <option value="scheduled">已约定复联</option>
          <option value="urgent">建议尽快就诊</option>
        </select>
      </label>
      <label class="field">
        <span>下次联系日期</span>
        <input v-model="contactNextDate" type="date" />
      </label>
      <label class="field full-span">
        <span>随访备注</span>
        <textarea
          v-model="contactNote"
          rows="3"
          placeholder="记录电话反馈、服药情况、复诊意愿、家属意见或需要提前处理的风险"
        />
      </label>
    </div>

    <div class="form-actions mobile-contact-actions">
      <button class="primary-button" :disabled="!quickContactPatientId || props.saving" @click="submitQuickContactLog">
        {{ props.saving ? '保存中...' : '保存联系记录' }}
      </button>
      <button v-if="quickContactPatientId" class="secondary-button" @click="emit('open-patient', quickContactPatientId)">
        打开患者详情
      </button>
    </div>
  </article>
</template>
