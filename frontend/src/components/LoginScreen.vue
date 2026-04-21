<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { Key, User } from '@element-plus/icons-vue'
import { getSavedAccounts, type SavedAccount } from '../services/api'
import type { HealthResponse, RegisterPayload } from '../services/types'

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
  (e: 'update:register-field', field: keyof RegisterPayload, value: RegisterPayload[keyof RegisterPayload]): void
  (e: 'submit-login'): void
  (e: 'toggle-register', value: boolean): void
  (e: 'submit-register'): void
}>()

const showAutocomplete = ref(false)
const savedAccounts = ref<SavedAccount[]>([])
const selectedIndex = ref(-1)
const rememberSession = ref(true)

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

const systemStatus = computed(() => {
  const mode = (props.health?.mode ?? 'demo').toUpperCase()
  return {
    mode: `${mode} 模式`,
    model: props.health?.model_available ? '模型：可用' : '模型：降级',
    db: '业务库：MYSQL',
  }
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
  const target = event.target as HTMLInputElement | HTMLSelectElement
  emit('update:register-field', field, target.value as RegisterPayload[keyof RegisterPayload])
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
    <section class="login-panel" aria-label="登录认证">
      <div class="login-brand">
        <h1>CTpath</h1>
        <p>慢病辅助诊疗业务系统</p>
        <small>基于时序知识图谱的慢病辅助诊疗工作台</small>
      </div>

      <form v-if="!registerMode" class="login-form" @submit.prevent="emit('submit-login')">
        <label class="field">
          <span>登录账号</span>
          <div class="auth-input-shell autocomplete-wrapper">
            <span class="auth-input-icon">
              <el-icon><User /></el-icon>
            </span>
            <input
              :value="username"
              type="text"
              placeholder="请输入账号或演示账号"
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
          <span>登录密码</span>
          <div class="auth-input-shell">
            <span class="auth-input-icon">
              <el-icon><Key /></el-icon>
            </span>
            <input :value="password" type="password" placeholder="请输入密码" @input="updatePassword" />
          </div>
        </label>

        <div class="login-options">
          <label class="remember-toggle">
            <input v-model="rememberSession" type="checkbox" />
            <span>记住账号</span>
          </label>
          <button type="button" class="text-link" @click="emit('toggle-register', true)">注册账号</button>
        </div>

        <p class="login-hint">演示账号：`demo_clinic`、`demo_nurse`、`demo_archivist`，统一密码：`demo123456`。</p>
        <p v-if="loginError" class="error-text">{{ loginError }}</p>

        <button class="primary-button login-submit" type="submit" :disabled="loadingLogin">
          {{ loadingLogin ? '登录中...' : '登录系统' }}
        </button>
      </form>

      <form v-else class="login-form" @submit.prevent="emit('submit-register')">
        <div class="register-copy">
          <h2>账号注册</h2>
          <p>使用当前后端注册流程创建工作台账号。注册成功后会直接进入系统，不额外新增新的认证模块。</p>
        </div>

        <label class="field">
          <span>账号</span>
          <input :value="registerForm.username" type="text" placeholder="请输入登录账号" @input="updateRegisterField('username', $event)" />
        </label>

        <label class="field">
          <span>密码</span>
          <input :value="registerForm.password" type="password" placeholder="请设置登录密码" @input="updateRegisterField('password', $event)" />
        </label>

        <label class="field">
          <span>姓名</span>
          <input :value="registerForm.name" type="text" placeholder="请输入真实姓名" @input="updateRegisterField('name', $event)" />
        </label>

        <div class="register-grid">
          <label class="field">
            <span>角色</span>
            <select :value="registerForm.role" @change="updateRegisterField('role', $event)">
              <option value="doctor">医生</option>
              <option value="nurse">护士</option>
              <option value="archivist">档案员</option>
            </select>
          </label>

          <label class="field">
            <span>职称</span>
            <input :value="registerForm.title" type="text" placeholder="如：主治医师" @input="updateRegisterField('title', $event)" />
          </label>
        </div>

        <label class="field">
          <span>科室</span>
          <input :value="registerForm.department" type="text" placeholder="如：慢病门诊" @input="updateRegisterField('department', $event)" />
        </label>

        <p v-if="registerError" class="error-text">{{ registerError }}</p>

        <button class="primary-button login-submit" type="submit" :disabled="loadingRegister">
          {{ loadingRegister ? '提交中...' : '提交注册' }}
        </button>

        <button type="button" class="text-link align-left" @click="emit('toggle-register', false)">返回登录</button>
      </form>
    </section>

    <footer class="login-system-bar" aria-label="系统状态">
      <span>系统在线</span>
      <div class="meta-row">
        <span>{{ systemStatus.mode }}</span>
        <span>{{ systemStatus.model }}</span>
        <span>{{ systemStatus.db }}</span>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.login-panel {
  position: relative;
  z-index: 1;
  width: min(560px, calc(100vw - 48px));
  display: grid;
  gap: 28px;
  padding: 56px 48px 42px;
}

.login-brand {
  display: grid;
  justify-items: center;
  gap: 8px;
  text-align: center;
}

.login-brand h1 {
  font-size: clamp(48px, 7vw, 72px);
  color: var(--ws-primary);
}

.login-brand p {
  margin: 0;
  font-family: var(--ws-font-headline);
  font-size: 14px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.login-brand small {
  color: rgba(63, 72, 73, 0.78);
  font-size: 13px;
  line-height: 1.6;
}

.login-form {
  display: grid;
  gap: 20px;
}

.field {
  display: grid;
  gap: 8px;
}

.field span {
  font-family: var(--ws-font-headline);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.auth-input-shell {
  position: relative;
}

.auth-input-shell input {
  padding-left: 54px;
}

.login-form input,
.login-form select,
.login-form textarea {
  width: 100%;
}

.auth-input-icon {
  position: absolute;
  top: 50%;
  left: 18px;
  transform: translateY(-50%);
  color: rgba(24, 28, 29, 0.48);
  font-size: 18px;
}

.autocomplete-wrapper {
  position: relative;
}

.autocomplete-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  right: 0;
  z-index: 4;
  display: grid;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.98);
  box-shadow: var(--ws-shadow-card);
  overflow: hidden;
}

.autocomplete-item {
  display: grid;
  grid-template-columns: 42px minmax(0, 1fr) auto;
  gap: 12px;
  align-items: center;
  padding: 14px 16px;
  border: 0;
  background: transparent;
  text-align: left;
}

.autocomplete-item:hover,
.autocomplete-item.selected {
  background: rgba(207, 230, 242, 0.45);
}

.suggestion-avatar {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  border-radius: 12px;
  background: linear-gradient(135deg, var(--ws-primary), var(--ws-primary-container));
  color: white;
  font-weight: 700;
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
  color: rgba(63, 72, 73, 0.72);
  font-size: 12px;
}

.suggestion-role {
  font-weight: 700;
}

.login-options {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.remember-toggle {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  color: rgba(24, 28, 29, 0.82);
}

.remember-toggle input {
  width: 20px;
  min-height: 20px;
  height: 20px;
  padding: 0;
}

.text-link {
  border: 0;
  background: transparent;
  color: var(--ws-primary);
  font-weight: 700;
}

.login-hint,
.register-copy p {
  margin: 0;
  color: rgba(63, 72, 73, 0.76);
  line-height: 1.65;
}

.register-copy {
  display: grid;
  gap: 10px;
}

.register-copy h2 {
  font-size: 28px;
}

.register-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.error-text {
  margin: 0;
  padding: 14px 16px;
  border-radius: 14px;
  background: rgba(255, 218, 214, 0.9);
  color: var(--ws-error);
  font-weight: 700;
}

.login-submit {
  width: 100%;
}

.align-left {
  justify-self: start;
}

@media (max-width: 720px) {
  .login-panel {
    width: 100%;
    padding: 36px 24px 28px;
  }

  .login-options,
  .register-grid {
    display: grid;
  }
}
</style>
