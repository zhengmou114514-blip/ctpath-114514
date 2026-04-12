<script setup lang="ts">
import { computed } from 'vue'
import type { PatientQuadruple, TimelineEvent } from '../../services/types'

const props = defineProps<{
  timeline: TimelineEvent[]
  quadruples: PatientQuadruple[]
}>()

const sortedTimeline = computed(() => [...props.timeline].sort((a, b) => b.date.localeCompare(a.date)))
</script>

<template>
  <section class="card middle-panel">
    <article class="block">
      <h3>病程时间线</h3>
      <div v-if="!sortedTimeline.length" class="empty">暂无时间线</div>
      <div v-else class="timeline">
        <article v-for="(item, idx) in sortedTimeline" :key="`${item.date}-${item.type}-${idx}`" class="timeline-item">
          <div class="date">{{ item.date }}</div>
          <div>
            <strong>{{ item.title }}</strong>
            <p>{{ item.detail }}</p>
            <span class="tag">{{ item.type }}</span>
          </div>
        </article>
      </div>
    </article>

    <article class="block">
      <h3>四元组视图</h3>
      <div v-if="!quadruples.length" class="empty">暂无四元组</div>
      <div v-else class="quadruples">
        <header>
          <span>关系</span>
          <span>对象</span>
          <span>时间</span>
        </header>
        <article v-for="(item, idx) in quadruples" :key="`${item.subject}-${item.relation}-${idx}`">
          <span>{{ item.relationLabel || item.relation }}</span>
          <span>{{ item.objectValue }}</span>
          <span>{{ item.timestamp.slice(0, 10) }}</span>
        </article>
      </div>
    </article>
  </section>
</template>

<style scoped>
.middle-panel {
  padding: 12px;
  display: grid;
  gap: 12px;
}

.block {
  display: grid;
  gap: 8px;
}

.block h3 {
  margin: 0;
  color: var(--navy);
  font-size: 1rem;
}

.timeline {
  display: grid;
  gap: 8px;
}

.timeline-item {
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 10px;
  background: #fbfdff;
  display: grid;
  grid-template-columns: 110px 1fr;
  gap: 10px;
}

.date {
  color: var(--ink-muted);
  font-size: 0.82rem;
}

.timeline-item p {
  margin: 4px 0;
  color: var(--ink-soft);
  font-size: 0.84rem;
}

.tag {
  display: inline-flex;
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 2px 8px;
  font-size: 0.74rem;
  color: var(--ink-muted);
}

.quadruples {
  display: grid;
  gap: 6px;
}

.quadruples header,
.quadruples article {
  display: grid;
  grid-template-columns: 1fr 1fr 100px;
  gap: 8px;
}

.quadruples header {
  font-size: 0.76rem;
  color: var(--ink-muted);
  padding: 0 2px;
}

.quadruples article {
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 8px;
  background: #fff;
  font-size: 0.84rem;
}

.empty {
  border: 1px dashed var(--border-strong);
  border-radius: 8px;
  padding: 12px;
  color: var(--ink-muted);
  text-align: center;
}

@media (max-width: 900px) {
  .timeline-item,
  .quadruples header,
  .quadruples article {
    grid-template-columns: 1fr;
  }
}
</style>
