<template>
  <div class="pagination-wrapper">
    <div class="pagination-info">
      共 <span class="highlight">{{ total }}</span> 条记录，
      第 <span class="highlight">{{ currentPage }}</span> / <span class="highlight">{{ totalPages }}</span> 页
    </div>
    
    <div class="pagination-controls">
      <button 
        class="page-btn"
        :disabled="currentPage === 1"
        @click="handlePageChange(1)"
      >
        首页
      </button>
      
      <button 
        class="page-btn"
        :disabled="currentPage === 1"
        @click="handlePageChange(currentPage - 1)"
      >
        ‹
      </button>
      
      <template v-for="page in visiblePages" :key="page">
        <button 
          v-if="page !== '...'"
          class="page-btn"
          :class="{ active: page === currentPage }"
          @click="handlePageChange(page as number)"
        >
          {{ page }}
        </button>
        <span v-else class="ellipsis">...</span>
      </template>
      
      <button 
        class="page-btn"
        :disabled="currentPage === totalPages"
        @click="handlePageChange(currentPage + 1)"
      >
        ›
      </button>
      
      <button 
        class="page-btn"
        :disabled="currentPage === totalPages"
        @click="handlePageChange(totalPages)"
      >
        末页
      </button>
    </div>
    
    <div class="page-size-selector">
      <select v-model="localPageSize" @change="handlePageSizeChange">
        <option :value="10">10条/页</option>
        <option :value="20">20条/页</option>
        <option :value="50">50条/页</option>
        <option :value="100">100条/页</option>
      </select>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'

interface Props {
  total: number
  page: number
  pageSize: number
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:page': [page: number]
  'update:pageSize': [pageSize: number]
  'change': [page: number, pageSize: number]
}>()

const localPageSize = ref(props.pageSize)

const currentPage = computed(() => props.page)
const totalPages = computed(() => Math.ceil(props.total / props.pageSize) || 1)

// 计算可见的页码
const visiblePages = computed(() => {
  const pages: (number | string)[] = []
  const total = totalPages.value
  const current = currentPage.value
  
  if (total <= 7) {
    for (let i = 1; i <= total; i++) {
      pages.push(i)
    }
  } else {
    if (current <= 3) {
      pages.push(1, 2, 3, 4, '...', total)
    } else if (current >= total - 2) {
      pages.push(1, '...', total - 3, total - 2, total - 1, total)
    } else {
      pages.push(1, '...', current - 1, current, current + 1, '...', total)
    }
  }
  
  return pages
})

function handlePageChange(page: number) {
  if (page >= 1 && page <= totalPages.value && page !== currentPage.value) {
    emit('update:page', page)
    emit('change', page, props.pageSize)
  }
}

function handlePageSizeChange() {
  emit('update:pageSize', localPageSize.value)
  emit('change', 1, localPageSize.value)
}

// 监听props变化
watch(() => props.pageSize, (newVal) => {
  localPageSize.value = newVal
})
</script>

<style scoped>
.pagination-wrapper {
  display: flex;
  align-items: center;
  gap: 20px;
  font-size: 14px;
}

.pagination-info {
  color: #666;
}

.highlight {
  color: #1890ff;
  font-weight: 600;
}

.pagination-controls {
  display: flex;
  align-items: center;
  gap: 4px;
}

.page-btn {
  min-width: 32px;
  height: 32px;
  padding: 0 8px;
  border: 1px solid #d9d9d9;
  background: white;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
  font-size: 14px;
}

.page-btn:hover:not(:disabled) {
  border-color: #1890ff;
  color: #1890ff;
}

.page-btn:disabled {
  cursor: not-allowed;
  opacity: 0.4;
}

.page-btn.active {
  background: #1890ff;
  border-color: #1890ff;
  color: white;
}

.ellipsis {
  padding: 0 8px;
  color: #999;
}

.page-size-selector select {
  height: 32px;
  padding: 0 8px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.page-size-selector select:focus {
  outline: none;
  border-color: #1890ff;
}
</style>
