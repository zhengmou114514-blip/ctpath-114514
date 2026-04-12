<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import type { HealthResponse, RegisterPayload } from '../services/types'
import { getSavedAccounts, type SavedAccount } from '../services/api'

const props = defineProps<{
  username: string
  password: string
  loginError: string
  loadingLogin: boolean
  health: HealthResponse | null
  registerMode: boolean
  registerForm: RegisterPayload
  registerError: string
  loadingRegister: boolean
}>()

const emit = defineEmits<{
  (e: 'update:username', value: string): void
  (e: 'update:password', value: string): void
  (e: 'submit-login'): void
  (e: 'toggle-register', value: boolean): void
  (e: 'submit-register'): void
}>()

const showAutocomplete = ref(false)
const savedAccounts = ref<SavedAccount[]>([])
const usernameInputRef = ref<HTMLInputElement | null>(null)
const selectedIndex = ref(-1)

// 加载已保存的账号
onMounted(() => {
  savedAccounts.value = getSavedAccounts()
})

// 自动补全建议（根据输入过滤）
const autocompleteSuggestions = computed(() => {
  if (!props.username || props.username.length === 0) {
    return []
  }
  
  const input = props.username.toLowerCase()
  
  // 过滤匹配的账号（账号或姓名包含输入内容）
  return savedAccounts.value.filter(account => {
    const usernameMatch = account.username.toLowerCase().includes(input)
    const nameMatch = account.name.toLowerCase().includes(input)
    return usernameMatch || nameMatch
  }).slice(0, 5) // 最多显示5个建议
})

// 监听用户名变化，显示/隐藏自动补全
watch(() => props.username, (newValue) => {
  if (newValue && newValue.length > 0) {
    showAutocomplete.value = autocompleteSuggestions.value.length > 0
  } else {
    showAutocomplete.value = false
  }
  selectedIndex.value = -1 // 重置选中索引
})

function updateUsername(event: Event) {
  const value = (event.target as HTMLInputElement).value
  emit('update:username', value)
}

function updatePassword(event: Event) {
  emit('update:password', (event.target as HTMLInputElement).value)
}

// 选择自动补全建议
function selectSuggestion(account: SavedAccount) {
  emit('update:username', account.username)
  emit('update:password', '')
  showAutocomplete.value = false
  // 聚焦到密码输入框
  setTimeout(() => {
    const passwordInput = document.querySelector('input[type="password"]') as HTMLInputElement
    if (passwordInput) {
      passwordInput.focus()
    }
  }, 100)
}

// 键盘导航
function handleKeydown(event: KeyboardEvent) {
  if (!showAutocomplete.value) return
  
  const suggestions = autocompleteSuggestions.value
  
  if (event.key === 'ArrowDown') {
    event.preventDefault()
    selectedIndex.value = Math.min(selectedIndex.value + 1, suggestions.length - 1)
  } else if (event.key === 'ArrowUp') {
    event.preventDefault()
    selectedIndex.value = Math.max(selectedIndex.value - 1, -1)
  } else if (event.key === 'Enter' && selectedIndex.value >= 0) {
    event.preventDefault()
    selectSuggestion(suggestions[selectedIndex.value])
  } else if (event.key === 'Escape') {
    showAutocomplete.value = false
  }
}

// 失去焦点时隐藏自动补全（延迟以允许点击建议）
function handleBlur() {
  setTimeout(() => {
    showAutocomplete.value = false
  }, 200)
}

// 聚焦时显示自动补全
function handleFocus() {
  if (props.username && autocompleteSuggestions.value.length > 0) {
    showAutocomplete.value = true
  }
}

// 获取角色标签
function getRoleLabel(role: string): string {
  const labels: Record<string, string> = {
    doctor: '医生',
    nurse: '护士',
    archivist: '档案管理员',
  }
  return labels[role] || role
}
</script>

<template>
  <div class="login-shell">
    <section class="login-panel card">
      <div class="login-header">
        <p class="eyebrow">门诊入口</p>
        <h1>慢性病辅助诊疗系统</h1>
        <p class="login-copy">请先登录后再进入系统，不再默认跳过登录直接进入后台页面。</p>
      </div>

      <form v-if="!props.registerMode" class="login-form" @submit.prevent="emit('submit-login')">
        <label class="field">
          <span>账号</span>
          <div class="autocomplete-wrapper">
            <input 
              ref="usernameInputRef"
              :value="props.username" 
              type="text" 
              placeholder="demo_clinic" 
              @input="updateUsername"
              @keydown="handleKeydown"
              @blur="handleBlur"
              @focus="handleFocus"
              autocomplete="off"
            />
            
            <!-- 自动补全下拉框 -->
            <div v-if="showAutocomplete && autocompleteSuggestions.length > 0" class="autocomplete-dropdown">
              <div
                v-for="(account, index) in autocompleteSuggestions"
                :key="account.username"
                class="autocomplete-item"
                :class="{ selected: index === selectedIndex }"
                @click="selectSuggestion(account)"
              >
                <div class="suggestion-avatar">
                  {{ account.name.slice(-2) }}
                </div>
                <div class="suggestion-info">
                  <div class="suggestion-name">{{ account.name }}</div>
                  <div class="suggestion-username">@{{ account.username }}</div>
                </div>
                <div class="suggestion-role" :class="`role-${account.role}`">
                  {{ getRoleLabel(account.role) }}
                </div>
              </div>
            </div>
          </div>
        </label>

        <label class="field">
          <span>密码</span>
          <input :value="props.password" type="password" placeholder="demo123456" @input="updatePassword" />
        </label>

        <div class="login-meta">
          <span>演示账号：demo_clinic / demo_nurse / demo_archivist (密码: demo123456)</span>
          <span>服务状态：{{ props.health ? `${props.health.status} / ${props.health.mode}` : '未连接' }}</span>
        </div>

        <p v-if="props.loginError" class="error-text">{{ props.loginError }}</p>

        <div class="login-actions">
          <button class="primary-button" type="submit" :disabled="props.loadingLogin">
            {{ props.loadingLogin ? '登录中...' : '登录系统' }}
          </button>
          <button class="secondary-button" type="button" @click="emit('toggle-register', true)">注册账号</button>
        </div>
      </form>

      <form v-else class="login-form" @submit.prevent="emit('submit-register')">
        <label class="field">
          <span>姓名</span>
          <input v-model="props.registerForm.name" type="text" placeholder="请输入姓名" />
        </label>

        <label class="field">
          <span>账号</span>
          <input v-model="props.registerForm.username" type="text" placeholder="请输入账号" />
        </label>

        <label class="field">
          <span>密码</span>
          <input v-model="props.registerForm.password" type="password" placeholder="请输入密码" />
        </label>

        <label class="field">
          <span>职称</span>
          <input v-model="props.registerForm.title" type="text" placeholder="如：主治医师" />
        </label>

        <label class="field">
          <span>科室</span>
          <input v-model="props.registerForm.department" type="text" placeholder="如：慢病管理门诊" />
        </label>

        <p v-if="props.registerError" class="error-text">{{ props.registerError }}</p>

        <div class="login-actions">
          <button class="primary-button" type="submit" :disabled="props.loadingRegister">
            {{ props.loadingRegister ? '注册中...' : '完成注册' }}
          </button>
          <button class="secondary-button" type="button" @click="emit('toggle-register', false)">返回登录</button>
        </div>
      </form>
    </section>
  </div>
</template>

<style scoped>
/* 自动补全包装器 */
.autocomplete-wrapper {
  position: relative;
  width: 100%;
}

.autocomplete-wrapper input {
  width: 100%;
}

/* 自动补全下拉框 */
.autocomplete-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  max-height: 280px;
  overflow-y: auto;
  z-index: 1000;
  margin-top: 4px;
}

/* 自动补全项 */
.autocomplete-item {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  cursor: pointer;
  transition: background-color 0.2s;
  border-bottom: 1px solid #f0f0f0;
}

.autocomplete-item:last-child {
  border-bottom: none;
}

.autocomplete-item:hover,
.autocomplete-item.selected {
  background-color: #f5f5f5;
}

.autocomplete-item.selected {
  background-color: #e6f7ff;
}

/* 建议头像 */
.suggestion-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 500;
  margin-right: 10px;
  flex-shrink: 0;
}

/* 建议信息 */
.suggestion-info {
  flex: 1;
  min-width: 0;
}

.suggestion-name {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.suggestion-username {
  font-size: 12px;
  color: #999;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 建议角色标签 */
.suggestion-role {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
  margin-left: 8px;
  flex-shrink: 0;
}

.suggestion-role.role-doctor {
  background: #e6e8ff;
  color: #667eea;
}

.suggestion-role.role-nurse {
  background: #ffe6f0;
  color: #f5576c;
}

.suggestion-role.role-archivist {
  background: #e6f7ff;
  color: #4facfe;
}

/* 滚动条样式 */
.autocomplete-dropdown::-webkit-scrollbar {
  width: 6px;
}

.autocomplete-dropdown::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.autocomplete-dropdown::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.autocomplete-dropdown::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>
