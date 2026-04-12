<script setup lang="ts">
import { computed } from 'vue'
import type { PatientQuadruple, TimelineEvent } from '../../services/types'

const props = defineProps<{
  timeline: TimelineEvent[]
  quadruples: PatientQuadruple[]
}>()

const sortedTimeline = computed(() => [...props.timeline].sort((a, b) => b.date.localeCompare(a.date)))

function eventTone(item: TimelineEvent) {
  const content = `${item.title} ${item.detail}`.toLowerCase()
  if (item.type === 'risk' || content.includes('high') || item.detail.includes('高')) return 'important'
  return 'normal'
}
</script>

<template>
  <section class="card middle-panel">
    <article class="block">
      <div class="block-head">
        <h3>病程时间线（倒序）</h3>
        <span class="small-tip">异常事件高亮</span>
      </div>
      <div v-if="!sortedTimeline.length" class="empty">暂无病程时间线</div>
      <div v-else class="timeline">
        <article
          v-for="(item, idx) in sortedTimeline"
          :key="`${item.date}-${item.type}-${idx}`"
          class="timeline-item"
          :class="`tone-${eventTone(item)}`"
        >
          <div class="date">{{ item.date }}</div>
          <div>
            <div class="row-head">
              <strong>{{ item.title }}</strong>
              <span class="tag">{{ item.type }}</span>
            </div>
            <p>{{ item.detail }}</p>
          </div>
        </article>
      </div>
    </article>

    <article class="block">
      <h3>关键四元组</h3>
      <div v-if="!quadruples.length" class="empty">暂无结构化四元组</div>
      <div v-else class="quadruples">
        <header>
          <span>关系</span>
          <span>对象值</span>
          <span>时间</span>
          <span>来源</span>
        </header>
        <article v-for="(item, idx) in quadruples" :key="`${item.subject}-${item.relation}-${idx}`">
          <span>{{ item.relationLabel || item.relation }}</span>
          <span>{{ item.objectValue }}</span>
          <span>{{ item.timestamp.slice(0, 10) }}</span>
          <span>{{ item.source }}</span>
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

.block-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
}

.block h3 {
  margin: 0;
  color: var(--ws-title, #10263c);
  font-size: 1rem;
}

.small-tip {
  color: var(--ws-text-muted, #617385);
  font-size: 0.76rem;
}

.timeline {
  display: grid;
  gap: 8px;
}

.timeline-item {
  border: 1px solid var(--ws-border, #cfd9e5);
  border-radius: 10px;
  padding: 10px;
  background: #fbfdff;
  display: grid;
  grid-template-columns: 110px 1fr;
  gap: 10px;
}

.timeline-item.tone-important {
  border-color: #efc2c5;
  background: #fff4f5;
}

.date {
  color: var(--ws-text-muted, #617385);
  font-size: 0.82rem;
}

.row-head {
  display: flex;
  justify-content: space-between;
  gap: 10px;
}

.timeline-item p {
  margin: 4px 0 0;
  color: var(--ws-text-muted, #617385);
  font-size: 0.84rem;
}

.tag {
  display: inline-flex;
  border: 1px solid var(--ws-border, #cfd9e5);
  border-radius: 999px;
  padding: 2px 8px;
  font-size: 0.74rem;
  color: var(--ws-text-muted, #617385);
}

.quadruples {
  display: grid;
  gap: 6px;
}

.quadruples header,
.quadruples article {
  display: grid;
  grid-template-columns: 1fr 1fr 100px 80px;
  gap: 8px;
}

.quadruples header {
  font-size: 0.76rem;
  color: var(--ws-text-muted, #617385);
  padding: 0 2px;
}

.quadruples article {
  border: 1px solid var(--ws-border, #cfd9e5);
  border-radius: 8px;
  padding: 8px;
  background: #fff;
  font-size: 0.84rem;
}

.empty {
  border: 1px dashed var(--ws-border-strong, #b8c7d8);
  border-radius: 8px;
  padding: 12px;
  color: var(--ws-text-muted, #617385);
  text-align: center;
  font-size: 0.84rem;
}

@media (max-width: 980px) {
  .timeline-item,
  .quadruples header,
  .quadruples article {
    grid-template-columns: 1fr;
  }
}
</style>
