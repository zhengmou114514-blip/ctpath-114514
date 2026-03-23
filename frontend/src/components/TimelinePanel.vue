<script setup lang="ts">
import type { TimelineEvent } from '../services/types'

defineProps<{
  timeline: TimelineEvent[]
}>()
</script>

<template>
  <section class="surface-card">
    <div class="surface-head">
      <div>
        <p class="surface-eyebrow">Timeline</p>
        <h3>病程轨迹</h3>
      </div>
      <span class="surface-note">病历事件按时间排序</span>
    </div>

    <div class="timeline">
      <article
        v-for="event in timeline"
        :key="`${event.date}-${event.title}`"
        class="timeline-item"
      >
        <div class="timeline-line">
          <span class="timeline-dot" :class="`event-${event.type}`"></span>
        </div>
        <div class="timeline-card">
          <div class="timeline-meta">
            <span>{{ event.date }}</span>
            <span class="event-tag" :class="`event-${event.type}`">{{ event.type }}</span>
          </div>
          <h4>{{ event.title }}</h4>
          <p>{{ event.detail }}</p>
        </div>
      </article>
    </div>
  </section>
</template>
