<script setup lang="ts">
import type { StatItem } from '../services/types'

defineProps<{
  stats: StatItem[]
}>()
</script>

<template>
  <section class="stats-grid">
    <article v-for="item in stats" :key="item.label" class="stat-card">
      <span>{{ item.label }}</span>
      <strong>{{ item.value }}</strong>
      <small>{{ item.trend }}</small>
    </article>
  </section>
</template>
