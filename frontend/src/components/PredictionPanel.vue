<script setup lang="ts">
import { computed } from 'vue'
import type { PredictionItem } from '../services/types'

const props = defineProps<{
  predictions: PredictionItem[]
}>()

const best = computed(() => props.predictions[0] ?? null)

function scoreText(score: number): string {
  return `${(score * 100).toFixed(1)}%`
}

const tone = computed(() => {
  const score = best.value?.score ?? 0
  if (score >= 0.75) return 'risk-high'
  if (score >= 0.5) return 'risk-medium'
  return 'risk-low'
})
</script>

<template>
  <section class="surface-card">
    <div class="surface-head">
      <div>
        <p class="surface-eyebrow">Prediction</p>
        <h3>T+1 预测结果</h3>
      </div>
      <span class="surface-note">Top-K 输出</span>
    </div>

    <div class="forecast-banner" :class="tone">
      <div>
        <span class="forecast-mini">Top-1</span>
        <h4>{{ best?.label }}</h4>
        <p>{{ best?.reason }}</p>
      </div>
      <strong>{{ scoreText(best?.score ?? 0) }}</strong>
    </div>

    <div class="prediction-stack">
      <article v-for="item in predictions" :key="item.label" class="prediction-card">
        <div class="prediction-top">
          <h4>{{ item.label }}</h4>
          <span>{{ scoreText(item.score) }}</span>
        </div>
        <p>{{ item.reason }}</p>
      </article>
    </div>
  </section>
</template>
