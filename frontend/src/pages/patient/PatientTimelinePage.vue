<script setup lang="ts">
import { computed, ref } from 'vue'
import { useWorkspaceContext } from '../../composables/workspaceContext'

const workspace = useWorkspaceContext()
const patient = computed(() => workspace.selectedPatient)
const filter = ref('all')
const items = computed(() => {
  const all = patient.value?.timeline ?? []
  return filter.value === 'all' ? all : all.filter((item) => item.type === filter.value)
})
</script>

<template>
  <section v-if="patient" class="clinical-card">
    <div class="section-header">
      <div><p class="eyebrow">病程时间线</p><h2>诊疗过程记录</h2></div>
      <select v-model="filter">
        <option value="all">全部</option>
        <option value="visit">诊疗</option>
        <option value="diagnosis">检查</option>
        <option value="medication">用药</option>
        <option value="risk">随访</option>
      </select>
    </div>
    <el-timeline v-if="items.length">
      <el-timeline-item v-for="item in items" :key="`${item.date}-${item.title}`" :timestamp="item.date" placement="top">
        <strong>{{ item.title }}</strong>
        <p>{{ item.detail }}</p>
      </el-timeline-item>
    </el-timeline>
    <el-empty v-else description="暂无病程记录" />
  </section>
</template>
