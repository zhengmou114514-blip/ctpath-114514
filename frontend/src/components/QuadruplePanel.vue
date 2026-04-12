<script setup lang="ts">
import type { PatientQuadruple } from '../services/types'

const props = defineProps<{
  quadruples: PatientQuadruple[]
  highlightedKeys?: string[]
  focused?: boolean
}>()

function rowKey(item: PatientQuadruple) {
  return `${item.subject}-${item.relation}-${item.timestamp}`
}

function isHighlighted(item: PatientQuadruple) {
  return Boolean(props.highlightedKeys?.includes(rowKey(item)))
}
</script>

<template>
  <section class="quadruple-panel" :class="{ 'is-focus-target': props.focused }">
    <div class="panel-head">
      <div>
        <p class="eyebrow">四元组证据</p>
        <h3>当前模型输入事件</h3>
      </div>
      <span class="panel-meta">{{ props.quadruples.length }} 条</span>
    </div>

    <div class="quadruple-table">
      <div class="quadruple-table-head">
        <span>主体</span>
        <span>关系</span>
        <span>对象</span>
        <span>时间</span>
      </div>

      <article
        v-for="item in props.quadruples"
        :key="rowKey(item)"
        class="quadruple-row"
        :class="{ 'is-highlighted': isHighlighted(item) }"
      >
        <span>{{ item.subject }}</span>
        <span :title="item.relation">{{ item.relationLabel }}</span>
        <span :title="item.objectValue">{{ item.objectValue }}</span>
        <span>{{ item.timestamp.replace('T', ' ') }}</span>
      </article>
    </div>
  </section>
</template>
