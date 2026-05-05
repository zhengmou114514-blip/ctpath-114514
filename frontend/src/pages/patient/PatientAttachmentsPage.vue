<script setup lang="ts">
import { computed } from 'vue'
import { useWorkspaceContext } from '../../composables/workspaceContext'

const workspace = useWorkspaceContext()
const patient = computed(() => workspace.selectedPatient)
const items = computed(() => [
  { label: '患者照片', status: patient.value?.avatarUrl ? '已归档' : '待上传' },
  { label: '身份证', status: patient.value?.identityMasked ? '已登记' : '待补充' },
  { label: '检查报告', status: '可上传' },
  { label: '转诊资料', status: '按需补充' },
  { label: '知情同意书', status: patient.value?.consentStatus === 'signed' ? '已签署' : '待签署' },
  { label: '其他慢病资料', status: '可上传' },
])
</script>

<template>
  <section v-if="patient" class="clinical-card">
    <div class="section-header">
      <div><p class="eyebrow">附件资料</p><h2>电子档案附件</h2></div>
      <button class="primary-button" type="button">上传附件</button>
    </div>
    <div class="attachment-grid">
      <article v-for="item in items" :key="item.label">
        <strong>{{ item.label }}</strong>
        <span>{{ item.status }}</span>
      </article>
    </div>
  </section>
</template>

<style scoped>
.attachment-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }
.attachment-grid article { display: grid; gap: 8px; border: 1px solid #d5e6ef; background: #f7fbfd; padding: 14px; }
.attachment-grid span { color: #526772; }
@media (max-width: 900px) { .attachment-grid { grid-template-columns: 1fr; } }
</style>
