<script setup lang="ts">
import { computed } from 'vue'
import { useWorkspaceContext } from '../../composables/workspaceContext'

const workspace = useWorkspaceContext()
const patient = computed(() => workspace.selectedPatient)
</script>

<template>
  <section v-if="patient" class="clinical-card">
    <p class="eyebrow">当前用药</p>
    <h2>医生端用药摘要</h2>
    <p>医生端仅查看当前用药摘要、用药充分性和药事复核状态。完整新增用药与用药复核由药事管理模块处理。</p>
    <div class="med-summary">
      <article><span>患者</span><strong>{{ patient.name }}</strong></article>
      <article><span>主诊断</span><strong>{{ patient.primaryDisease }}</strong></article>
      <article><span>药事状态</span><strong>待药房复核</strong></article>
    </div>
  </section>
</template>

<style scoped>
.med-summary { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }
.med-summary article { display: grid; gap: 6px; border: 1px solid #d5e6ef; padding: 12px; background: #f7fbfd; }
@media (max-width: 900px) { .med-summary { grid-template-columns: 1fr; } }
</style>
