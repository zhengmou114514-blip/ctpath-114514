<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { PatientCase, PatientEventPayload, PatientUpsertPayload, TimelineEvent } from '../services/types'

type ArchiveFocusSection = 'overview' | 'events'
type ArchiveTab = 'overview' | 'events' | 'preview'

const props = defineProps<{
  patientForm: PatientUpsertPayload
  selectedPatientId: string
  eventForm: PatientEventPayload
  relationOptions: string[]
  savingPatient: boolean
  savingEvent: boolean
  timelineItems: TimelineEvent[]
  selectedPatient: PatientCase | null
  mode?: 'create' | 'detail'
  focusSection?: ArchiveFocusSection
}>()

const emit = defineEmits<{
  (e: 'submitArchive'): void
  (e: 'submitEvent'): void
  (e: 'prepareNew'): void
}>()

const isCreateMode = computed(() => props.mode === 'create')
const activeTab = ref<ArchiveTab>('overview')

const primaryLabel = computed(() => {
  if (props.savingPatient) return '保存中...'
  if (isCreateMode.value) return '完成基础建档'
  return props.selectedPatientId ? '保存档案修改' : '完成基础建档'
})

const secondaryLabel = computed(() => (isCreateMode.value ? '清空表单' : '新建下一份档案'))

function stageLabel(value: string) {
  if (value === 'Early') return '早期'
  if (value === 'Mid') return '中期'
  if (value === 'Late') return '晚期'
  return value
}

function supportLabel(value: string) {
  if (value === 'high') return '高'
  if (value === 'medium') return '中'
  if (value === 'low') return '低'
  return value
}

function switchTab(tab: ArchiveTab) {
  activeTab.value = tab
}

watch(
  () => props.focusSection,
  (value) => {
    if (value === 'events') {
      activeTab.value = 'events'
    }
  },
  { immediate: true }
)
</script>

<template>
  <section class="module-shell archive-grid archive-grid-practical">
    <article class="card archive-tab-card">
      <div class="archive-process-strip">
        <div class="archive-process-step" :class="{ active: activeTab === 'overview' }">
          <strong>1</strong>
          <span>基础身份登记</span>
        </div>
        <div class="archive-process-step" :class="{ active: activeTab === 'events' }">
          <strong>2</strong>
          <span>结构化事件补录</span>
        </div>
        <div class="archive-process-step" :class="{ active: activeTab === 'preview' }">
          <strong>3</strong>
          <span>建档完成核对</span>
        </div>
      </div>

      <div class="archive-tabbar">
        <button class="secondary-button" :class="{ active: activeTab === 'overview' }" @click="switchTab('overview')">基础建档</button>
        <button class="secondary-button" :class="{ active: activeTab === 'events' }" @click="switchTab('events')">结构化事件</button>
        <button class="secondary-button" :class="{ active: activeTab === 'preview' }" @click="switchTab('preview')">档案摘要</button>
      </div>
    </article>

    <article v-if="activeTab === 'overview'" class="card archive-form-card archive-single-panel">
      <div class="panel-head">
        <div>
          <p class="eyebrow">步骤 1</p>
          <h3>基础身份登记</h3>
        </div>
        <span class="panel-meta">按照门诊建档顺序，先登记身份、慢病标签和最近就诊信息。</span>
      </div>

      <div class="archive-section-intro-grid">
        <article class="archive-intro-tile">
          <strong>身份信息</strong>
          <span>患者编号、姓名、年龄、性别</span>
        </article>
        <article class="archive-intro-tile">
          <strong>联系信息</strong>
          <span>头像链接、手机号、紧急联系人</span>
        </article>
        <article class="archive-intro-tile">
          <strong>慢病标签</strong>
          <span>主要疾病、当前阶段、风险标签</span>
        </article>
        <article class="archive-intro-tile">
          <strong>门诊摘要</strong>
          <span>最近就诊日期与病情摘要</span>
        </article>
      </div>

      <div class="form-grid">
        <label class="field">
          <span>患者编号</span>
          <input v-model="patientForm.patientId" :disabled="!!selectedPatientId" type="text" placeholder="PID9010" />
        </label>
        <label class="field">
          <span>患者姓名</span>
          <input v-model="patientForm.name" type="text" placeholder="请输入患者姓名" />
        </label>
        <label class="field">
          <span>年龄</span>
          <input v-model.number="patientForm.age" type="number" min="0" max="120" />
        </label>
        <label class="field">
          <span>性别</span>
          <select v-model="patientForm.gender">
            <option value="女">女</option>
            <option value="男">男</option>
          </select>
        </label>
        <label class="field full-span">
          <span>头像链接</span>
          <input v-model="patientForm.avatarUrl" type="url" placeholder="https://.../avatar.png 或 SVG" />
        </label>
        <label class="field">
          <span>联系电话</span>
          <input v-model="patientForm.phone" type="text" placeholder="请输入患者联系电话" />
        </label>
        <label class="field">
          <span>紧急联系人姓名</span>
          <input v-model="patientForm.emergencyContactName" type="text" placeholder="请输入紧急联系人姓名" />
        </label>
        <label class="field">
          <span>与患者关系</span>
          <input v-model="patientForm.emergencyContactRelation" type="text" placeholder="如：配偶 / 子女 / 监护人" />
        </label>
        <label class="field">
          <span>紧急联系人电话</span>
          <input v-model="patientForm.emergencyContactPhone" type="text" placeholder="请输入紧急联系人电话" />
        </label>
        <label class="field">
          <span>主要疾病</span>
          <input v-model="patientForm.primaryDisease" type="text" placeholder="如：Diabetes / Hypertension" />
        </label>
        <label class="field">
          <span>当前阶段</span>
          <select v-model="patientForm.currentStage">
            <option value="Early">早期</option>
            <option value="Mid">中期</option>
            <option value="Late">晚期</option>
          </select>
        </label>
        <label class="field">
          <span>最近就诊</span>
          <input v-model="patientForm.lastVisit" type="date" />
        </label>
        <label class="field">
          <span>证件号脱敏</span>
          <input v-model="patientForm.identityMasked" type="text" placeholder="3203********1234" />
        </label>
        <label class="field">
          <span>医保类型</span>
          <input v-model="patientForm.insuranceType" type="text" placeholder="城镇职工 / 城乡居民 / 自费" />
        </label>
        <label class="field">
          <span>建档科室</span>
          <input v-model="patientForm.department" type="text" placeholder="慢病管理门诊" />
        </label>
        <label class="field">
          <span>责任医生</span>
          <input v-model="patientForm.primaryDoctor" type="text" placeholder="周医生" />
        </label>
        <label class="field">
          <span>责任护士/管理师</span>
          <input v-model="patientForm.caseManager" type="text" placeholder="张护士" />
        </label>
        <label class="field">
          <span>过敏史</span>
          <input v-model="patientForm.allergyHistory" type="text" placeholder="无 / 青霉素过敏" />
        </label>
        <label class="field full-span">
          <span>家族史</span>
          <input v-model="patientForm.familyHistory" type="text" placeholder="无特殊家族史 / 父亲有卒中病史" />
        </label>
        <label class="field">
          <span>MRN</span>
          <input v-model="patientForm.medicalRecordNumber" type="text" placeholder="MRN0025" />
        </label>
        <label class="field">
          <span>å»ºæ¡£æ¥æº</span>
          <select v-model="patientForm.archiveSource">
            <option value="outpatient">é—¨è¯Šå»ºæ¡£</option>
            <option value="community_referral">ç¤¾åŒºè½¬ä»‹</option>
            <option value="discharge_followup">å‡ºé™¢éšè®¿</option>
            <option value="manual">äººå·¥è¡¥å½•</option>
          </select>
        </label>
        <label class="field">
          <span>æ¡£æ¡ˆçŠ¶æ€</span>
          <select v-model="patientForm.archiveStatus">
            <option value="draft">è‰ç¨¿</option>
            <option value="active">åœ¨ç®¡</option>
            <option value="suspended">æš‚åœ</option>
            <option value="closed">å·²ç»“æ¡ˆ</option>
          </select>
        </label>
        <label class="field">
          <span>çŸ¥æƒ…åŒæ„</span>
          <select v-model="patientForm.consentStatus">
            <option value="signed">å·²ç­¾ç½²</option>
            <option value="pending">å¾…ç¡®è®¤</option>
            <option value="family_authorized">å®¶å±žä»£ç­¾</option>
            <option value="withdrawn">å·²æ’¤å›ž</option>
          </select>
        </label>
        <div class="field field-static">
          <span>系统初始标记</span>
          <div class="archive-static-grid">
            <div class="summary-chip summary-chip-accent">
              <span>风险标签</span>
              <strong>{{ patientForm.riskLevel }}</strong>
            </div>
            <div class="summary-chip">
              <span>数据支持度</span>
              <strong>{{ supportLabel(patientForm.dataSupport) }}</strong>
            </div>
          </div>
        </div>
        <label class="field full-span">
          <span>病情摘要</span>
          <textarea
            v-model="patientForm.summary"
            rows="4"
            placeholder="记录本次接诊关注点、既往慢病情况、近期检查结果与需要随访的问题"
          />
        </label>
      </div>

      <div class="form-actions">
        <button class="primary-button" :disabled="props.savingPatient" @click="emit('submitArchive')">
          {{ primaryLabel }}
        </button>
        <button class="secondary-button" @click="emit('prepareNew')">{{ secondaryLabel }}</button>
        <button class="secondary-button" @click="switchTab('events')">下一步：结构化事件</button>
      </div>
    </article>

    <article v-else-if="activeTab === 'events'" class="card archive-event-card archive-single-panel" :class="{ 'is-focus-target': props.focusSection === 'events' }">
      <div class="panel-head">
        <div>
          <p class="eyebrow">步骤 2</p>
          <h3>结构化事件补录</h3>
        </div>
        <span class="panel-meta">这一步对应模型输入，建议录入疾病阶段、依从性、支持系统和关键指标等时序信息。</span>
      </div>

      <div class="archive-section-intro-grid">
        <article class="archive-intro-tile">
          <strong>时间戳</strong>
          <span>记录事件发生的日期时间</span>
        </article>
        <article class="archive-intro-tile">
          <strong>关系类型</strong>
          <span>选择模型可识别的标准关系</span>
        </article>
        <article class="archive-intro-tile">
          <strong>对象值</strong>
          <span>填写阶段、等级、分箱或观察结果</span>
        </article>
      </div>

      <div class="form-grid">
        <label class="field">
          <span>事件时间</span>
          <input v-model="eventForm.eventTime" type="datetime-local" />
        </label>
        <label class="field">
          <span>关系类型</span>
          <select v-model="eventForm.relation">
            <option v-for="item in props.relationOptions" :key="item" :value="item">{{ item }}</option>
          </select>
        </label>
        <label class="field">
          <span>对象值</span>
          <input v-model="eventForm.objectValue" type="text" placeholder="如：Mid / High / Q2" />
        </label>
        <label class="field full-span">
          <span>临床备注</span>
          <textarea v-model="eventForm.note" rows="3" placeholder="可记录本次录入依据、来源系统或对应检查说明" />
        </label>
      </div>

      <div class="form-actions">
        <button class="primary-button" :disabled="props.savingEvent" @click="emit('submitEvent')">
          {{ props.savingEvent ? '保存中...' : '新增结构化事件' }}
        </button>
        <button class="secondary-button" @click="switchTab('preview')">下一步：建档核对</button>
      </div>
    </article>

    <article v-else class="card preview-card archive-preview-card archive-single-panel">
      <div class="panel-head">
        <div>
          <p class="eyebrow">步骤 3</p>
          <h3>建档完成核对</h3>
        </div>
        <span class="panel-meta">{{ props.selectedPatient ? props.selectedPatient.name : '新建档案' }}</span>
      </div>

      <div class="archive-preview-grid">
        <div class="archive-preview-item">
          <span>疾病阶段</span>
          <strong>{{ stageLabel(props.patientForm.currentStage) }}</strong>
        </div>
        <div class="archive-preview-item">
          <span>风险标签</span>
          <strong>{{ props.patientForm.riskLevel }}</strong>
        </div>
        <div class="archive-preview-item">
          <span>数据支持度</span>
          <strong>{{ supportLabel(props.patientForm.dataSupport) }}</strong>
        </div>
        <div class="archive-preview-item">
          <span>最近就诊</span>
          <strong>{{ props.patientForm.lastVisit || '-' }}</strong>
        </div>
        <div class="archive-preview-item">
          <span>联系电话</span>
          <strong>{{ props.patientForm.phone || '-' }}</strong>
        </div>
        <div class="archive-preview-item">
          <span>紧急联系人</span>
          <strong>
            {{
              props.patientForm.emergencyContactName
                ? `${props.patientForm.emergencyContactName}${props.patientForm.emergencyContactRelation ? ` / ${props.patientForm.emergencyContactRelation}` : ''}`
                : '-'
            }}
          </strong>
        </div>
        <div class="archive-preview-item">
          <span>证件号脱敏</span>
          <strong>{{ props.patientForm.identityMasked || '-' }}</strong>
        </div>
        <div class="archive-preview-item">
          <span>医保类型</span>
          <strong>{{ props.patientForm.insuranceType || '-' }}</strong>
        </div>
        <div class="archive-preview-item">
          <span>建档科室</span>
          <strong>{{ props.patientForm.department || '-' }}</strong>
        </div>
        <div class="archive-preview-item">
          <span>责任医生</span>
          <strong>{{ props.patientForm.primaryDoctor || '-' }}</strong>
        </div>
        <div class="archive-preview-item">
          <span>责任护士/管理师</span>
          <strong>{{ props.patientForm.caseManager || '-' }}</strong>
        </div>
        <div class="archive-preview-item">
          <span>MRN</span>
          <strong>{{ props.patientForm.medicalRecordNumber || '-' }}</strong>
        </div>
        <div class="archive-preview-item">
          <span>å»ºæ¡£æ¥æº</span>
          <strong>{{ props.patientForm.archiveSource || '-' }}</strong>
        </div>
        <div class="archive-preview-item">
          <span>æ¡£æ¡ˆçŠ¶æ€</span>
          <strong>{{ props.patientForm.archiveStatus || '-' }}</strong>
        </div>
        <div class="archive-preview-item">
          <span>çŸ¥æƒ…åŒæ„</span>
          <strong>{{ props.patientForm.consentStatus || '-' }}</strong>
        </div>
        <div class="archive-preview-item">
          <span>过敏史</span>
          <strong>{{ props.patientForm.allergyHistory || '-' }}</strong>
        </div>
        <div class="archive-preview-item">
          <span>家族史</span>
          <strong>{{ props.patientForm.familyHistory || '-' }}</strong>
        </div>
      </div>

      <div class="preview-list">
        <article
          v-for="item in (props.timelineItems.length ? props.timelineItems : props.selectedPatient?.timeline ?? [])"
          :key="`${item.date}-${item.title}`"
          class="preview-row"
        >
          <strong>{{ item.title }}</strong>
          <span>{{ item.date }}</span>
          <p>{{ item.detail }}</p>
        </article>
      </div>

      <div v-if="props.selectedPatient?.auditLogs?.length" class="preview-list">
        <article
          v-for="log in props.selectedPatient.auditLogs"
          :key="log.logId"
          class="preview-row"
        >
          <strong>{{ log.action }}</strong>
          <span>{{ log.createdAt }}</span>
          <p>{{ log.detail }}{{ log.operatorName ? ` / ${log.operatorName}` : '' }}</p>
        </article>
      </div>

      <div class="form-actions">
        <button class="secondary-button" @click="switchTab('overview')">返回基础建档</button>
        <button class="secondary-button" @click="switchTab('events')">返回结构化事件</button>
      </div>
    </article>
  </section>
</template>
