<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
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
    <section class="login-card" aria-label="系统登录">
      <div class="brand-side">
        <div class="brand-mark">CT</div>
        <div>
          <p class="eyebrow">慢病辅助诊疗系统</p>
          <h1>CTpath 临床工作台</h1>
          <p>面向医生、护士与档案员的慢病患者管理入口。</p>
        </div>
      </div>

      <form class="login-form" @submit.prevent="emit('submit-login')">
        <div class="form-heading">
          <h2>账号登录</h2>
          <p>请输入分配的工作账号进入对应业务模块。</p>
        </div>

        <label class="field">
          <span>账号</span>
          <div class="autocomplete-wrapper">
            <input
              :value="username"
              type="text"
              placeholder="请输入账号"
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
          <input :value="password" type="password" placeholder="请输入密码" @input="updatePassword" />
        </label>

        <p class="login-hint">演示账号可使用 demo_clinic / demo_nurse / demo_archivist，密码 demo123456。</p>
        <p v-if="loginError" class="error-text">{{ loginError }}</p>

        <button class="primary-button login-submit" type="submit" :disabled="loadingLogin">
          {{ loadingLogin ? '正在登录...' : '登录工作台' }}
        </button>
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

.login-card {
  width: min(860px, 100%);
  display: grid;
  grid-template-columns: minmax(0, 0.9fr) 400px;
  overflow: hidden;
  border: 1px solid var(--ws-border);
  border-radius: 8px;
  background: var(--ws-surface);
  box-shadow: var(--ws-shadow);
}

.brand-side,
.login-form {
  padding: 32px;
}

.brand-side {
  display: grid;
  align-content: center;
  gap: 18px;
  background: #f3f7fb;
  border-right: 1px solid var(--ws-border);
}

.brand-mark {
  width: 52px;
  height: 52px;
  display: grid;
  place-items: center;
  border-radius: 8px;
  background: var(--ws-primary);
  color: #fff;
  font-weight: 900;
  letter-spacing: 0;
}

.brand-side h1,
.brand-side p,
.form-heading h2,
.form-heading p,
.login-hint {
  margin: 0;
}

.brand-side h1 {
  font-size: 24px;
  color: var(--ws-title);
}

.brand-side p,
.form-heading p,
.login-hint {
  color: var(--ws-text-muted);
  line-height: 1.7;
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

.login-hint {
  font-size: 12px;
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

.login-submit {
  width: 100%;
}

@media (max-width: 820px) {
  .login-card {
    grid-template-columns: 1fr;
  }

  .brand-side {
    border-right: 0;
    border-bottom: 1px solid var(--ws-border);
  }
}
</style>
