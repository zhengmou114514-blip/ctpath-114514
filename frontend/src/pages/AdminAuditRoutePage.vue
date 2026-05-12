<script setup lang="ts">
import { computed } from 'vue'
import { useWorkspaceContext } from '../composables/workspaceContext'
import SystemCenterPage from './SystemCenterPage.vue'

const workspace = useWorkspaceContext()
const doctor = computed(() => workspace.currentDoctor)
</script>

<template>
  <SystemCenterPage v-if="doctor" :doctor="doctor" :health="workspace.health" />
</template>
