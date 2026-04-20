<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
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
const selectedIndex = ref(-1)

const roleLabels: Record<string, string> = {
  doctor: '医生',
  nurse: '护士',
  archivist: '档案员',
}

const autocompleteSuggestions = computed(() => {
  const input = props.username.trim().toLowerCase()
  if (!input) return []
  return savedAccounts.value
    .filter((account) => account.username.toLowerCase().includes(input) || account.name.toLowerCase().includes(input))
    .slice(0, 5)
})

onMounted(() => {
  savedAccounts.value = getSavedAccounts()
})

watch(
  () => props.username,
  (value) => {
    showAutocomplete.value = Boolean(value && autocompleteSuggestions.value.length)
    selectedIndex.value = -1
  }
)

function updateUsername(event: Event) {
  emit('update:username', (event.target as HTMLInputElement).value)
}

function updatePassword(event: Event) {
  emit('update:password', (event.target as HTMLInputElement).value)
}

function updateRegisterField(field: keyof RegisterPayload, event: Event) {
  props.registerForm[field] = (event.target as HTMLInputElement | HTMLSelectElement).value as never
}

function selectSuggestion(account: SavedAccount) {
  emit('update:username', account.username)
  emit('update:password', '')
  showAutocomplete.value = false
  window.setTimeout(() => {
    document.querySelector<HTMLInputElement>('input[type="password"]')?.focus()
  }, 80)
}

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
    const selected = suggestions[selectedIndex.value]
    if (selected) selectSuggestion(selected)
  } else if (event.key === 'Escape') {
    showAutocomplete.value = false
  }
}

function handleBlur() {
  window.setTimeout(() => {
    showAutocomplete.value = false
  }, 160)
}

function handleFocus() {
  if (props.username && autocompleteSuggestions.value.length > 0) {
    showAutocomplete.value = true
  }
}
</script>

<template>
  <div class="login-shell">
    <section class="login-panel">
      <div class="login-copy-panel">
        <p class="eyebrow">CTpath Workstation</p>
        <h1>慢病辅助诊疗业务系统</h1>
        <p>
          登录后进入医生、护士或档案员工作台。系统聚焦慢病患者档案、病程时间线、模型辅助建议、随访闭环与治理能力。
        </p>
        <div class="login-status-grid">
          <span>后端：{{ health?.status ?? '未连接' }}</span>
          <span>模式：{{ health?.mode ?? 'unknown' }}</span>
          <span>模型：{{ health?.model_available ? '可用' : '降级/不可用' }}</span>
        </div>
      </div>

      <form v-if="!registerMode" class="login-form" @submit.prevent="emit('submit-login')">
        <div class="form-heading">
          <h2>登录工作台</h2>
          <p>演示账号：demo_clinic / demo_nurse / demo_archivist，密码 demo123456</p>
        </div>

        <label class="field">
          <span>用户名</span>
          <div class="autocomplete-wrapper">
            <input
              :value="username"
              type="text"
              placeholder="demo_clinic"
              autocomplete="off"
              @input="updateUsername"
              @keydown="handleKeydown"
              @blur="handleBlur"
              @focus="handleFocus"
            />
            <div v-if="showAutocomplete && autocompleteSuggestions.length" class="autocomplete-dropdown">
              <button
                v-for="(account, index) in autocompleteSuggestions"
                :key="account.username"
                type="button"
                class="autocomplete-item"
                :class="{ selected: index === selectedIndex }"
                @click="selectSuggestion(account)"
              >
                <span class="suggestion-avatar">{{ account.name.slice(-2) }}</span>
                <span class="suggestion-info">
                  <strong>{{ account.name }}</strong>
                  <small>@{{ account.username }}</small>
                </span>
                <span class="suggestion-role">{{ roleLabels[account.role] ?? account.role }}</span>
              </button>
            </div>
          </div>
        </label>

        <label class="field">
          <span>密码</span>
          <input :value="password" type="password" placeholder="demo123456" @input="updatePassword" />
        </label>

        <p v-if="loginError" class="error-text">{{ loginError }}</p>

        <div class="login-actions">
          <button class="primary-button" type="submit" :disabled="loadingLogin">
            {{ loadingLogin ? '登录中...' : '登录' }}
          </button>
          <button class="secondary-button" type="button" @click="emit('toggle-register', true)">注册账号</button>
        </div>
      </form>

      <form v-else class="login-form" @submit.prevent="emit('submit-register')">
        <div class="form-heading">
          <h2>注册工作台账号</h2>
          <p>填写信息后创建工作台账号。</p>
        </div>

        <label class="field">
          <span>姓名</span>
          <input :value="registerForm.name" type="text" placeholder="例如：王医生" @input="updateRegisterField('name', $event)" />
        </label>
        <label class="field">
          <span>用户名</span>
          <input :value="registerForm.username" type="text" placeholder="例如：wang_doctor" @input="updateRegisterField('username', $event)" />
        </label>
        <label class="field">
          <span>密码</span>
          <input :value="registerForm.password" type="password" placeholder="不少于 6 位" @input="updateRegisterField('password', $event)" />
        </label>
        <label class="field">
          <span>职称</span>
          <input :value="registerForm.title" type="text" placeholder="主治医师 / 护师 / 档案员" @input="updateRegisterField('title', $event)" />
        </label>
        <label class="field">
          <span>科室</span>
          <input :value="registerForm.department" type="text" placeholder="慢病管理中心" @input="updateRegisterField('department', $event)" />
        </label>
        <label class="field">
          <span>角色</span>
          <select :value="registerForm.role" @change="updateRegisterField('role', $event)">
            <option value="doctor">医生</option>
            <option value="nurse">护士</option>
            <option value="archivist">档案员</option>
          </select>
        </label>

        <p v-if="registerError" class="error-text">{{ registerError }}</p>

        <div class="login-actions">
          <button class="primary-button" type="submit" :disabled="loadingRegister">
            {{ loadingRegister ? '注册中...' : '提交注册' }}
          </button>
          <button class="secondary-button" type="button" @click="emit('toggle-register', false)">返回登录</button>
        </div>
      </form>
    </section>
  </div>
</template>

<style scoped>
.login-shell {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 32px;
  background: var(--ws-bg);
}

.login-panel {
  width: min(980px, 100%);
  display: grid;
  grid-template-columns: minmax(0, 1fr) 420px;
  gap: 0;
  border: 1px solid var(--ws-border);
  border-radius: 8px;
  background: var(--ws-surface);
  box-shadow: var(--ws-shadow);
  overflow: hidden;
}

.login-copy-panel,
.login-form {
  padding: 28px;
}

.login-copy-panel {
  display: grid;
  align-content: center;
  gap: 16px;
  background: #f3f7fb;
  border-right: 1px solid var(--ws-border);
}

.login-copy-panel h1,
.login-copy-panel p,
.form-heading h2,
.form-heading p {
  margin: 0;
}

.login-copy-panel h1 {
  font-size: 24px;
  color: var(--ws-title);
}

.login-copy-panel p,
.form-heading p {
  color: var(--ws-text-muted);
  line-height: 1.7;
}

.login-status-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.login-status-grid span {
  border: 1px solid var(--ws-border);
  border-radius: 8px;
  background: var(--ws-surface);
  padding: 10px;
  color: var(--ws-title);
  font-size: 12px;
  font-weight: 700;
}

.login-form {
  display: grid;
  gap: 16px;
}

.field {
  display: grid;
  gap: 6px;
}

.field span {
  color: var(--ws-text-muted);
  font-size: 12px;
  font-weight: 700;
}

.autocomplete-wrapper {
  position: relative;
}

.autocomplete-dropdown {
  position: absolute;
  z-index: 20;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  display: grid;
  max-height: 280px;
  overflow-y: auto;
  border: 1px solid var(--ws-border);
  border-radius: 8px;
  background: var(--ws-surface);
  box-shadow: var(--ws-shadow);
}

.autocomplete-item {
  display: grid;
  grid-template-columns: 36px minmax(0, 1fr) auto;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border: 0;
  border-bottom: 1px solid var(--ws-border);
  background: transparent;
  text-align: left;
}

.autocomplete-item:last-child {
  border-bottom: 0;
}

.autocomplete-item:hover,
.autocomplete-item.selected {
  background: var(--ws-primary-soft);
}

.suggestion-avatar {
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  border-radius: 8px;
  background: var(--ws-primary);
  color: #fff;
  font-size: 12px;
  font-weight: 800;
}

.suggestion-info {
  min-width: 0;
  display: grid;
}

.suggestion-info strong,
.suggestion-info small {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.suggestion-info small,
.suggestion-role {
  color: var(--ws-text-muted);
  font-size: 12px;
}

.suggestion-role {
  font-weight: 700;
}

.error-text {
  margin: 0;
  padding: 10px 12px;
  border: 1px solid var(--ws-danger-border);
  border-radius: 8px;
  background: var(--ws-danger-soft);
  color: var(--ws-danger);
  font-size: 12px;
  font-weight: 700;
}

.login-actions {
  display: flex;
  gap: 10px;
}

@media (max-width: 860px) {
  .login-panel {
    grid-template-columns: 1fr;
  }

  .login-copy-panel {
    border-right: 0;
    border-bottom: 1px solid var(--ws-border);
  }

  .login-status-grid {
    grid-template-columns: 1fr;
  }
}
</style>
