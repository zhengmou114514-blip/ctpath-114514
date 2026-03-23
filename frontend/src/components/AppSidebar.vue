<script setup lang="ts">
const props = defineProps<{
  sections: string[]
  activeSection: string
}>()

const emit = defineEmits<{
  (e: 'select', section: string): void
}>()

function select(section: string) {
  emit('select', section)
}
</script>

<template>
  <aside class="sidebar">
    <div class="brand">
      <div class="brand-mark">C</div>
      <div>
        <p>CTpath Care</p>
        <strong>Clinical Workspace</strong>
      </div>
    </div>

    <nav class="nav-list">
      <button
        v-for="section in props.sections"
        :key="section"
        class="nav-item"
        :class="{ active: section === props.activeSection }"
        @click="select(section)"
      >
        {{ section }}
      </button>
    </nav>

    <div class="sidebar-card">
      <span>模型状态</span>
      <strong>TKGR-GPRSCL</strong>
      <p>路径推理、监督对比学习、时序知识图谱三部分已经联动展示。</p>
    </div>
  </aside>
</template>
