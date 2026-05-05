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

const savedAccounts = ref<SavedAccount[]>([])
const showAutocomplete = ref(false)

const suggestions = computed(() => {
  const keyword = props.username.trim().toLowerCase()
  if (!keyword) return []
  return savedAccounts.value
    .filter((item) => item.username.toLowerCase().includes(keyword) || item.name.toLowerCase().includes(keyword))
    .slice(0, 5)
})

onMounted(() => {
  savedAccounts.value = getSavedAccounts()
})

watch(
  () => props.username,
  (value) => {
    showAutocomplete.value = Boolean(value && suggestions.value.length)
  }
)

function updateRegisterField(field: keyof RegisterPayload, event: Event) {
  const target = event.target as HTMLInputElement | HTMLSelectElement
  emit('update:register-field', field, target.value as RegisterPayload[keyof RegisterPayload])
}

function pickSuggestion(account: SavedAccount) {
  emit('update:username', account.username)
  showAutocomplete.value = false
}

function deferHideAutocomplete() {
  globalThis.setTimeout(() => {
    showAutocomplete.value = false
  }, 120)
}
</script>

<template>
  <div class="login-page">
    <main class="login-main">
      <section class="login-card">
        <div class="login-brand">
          <div class="login-brand-copy">
            <h1>慢性病辅助诊疗系统</h1>
          </div>
        </div>

        <form v-if="!registerMode" class="login-form" @submit.prevent="emit('submit-login')">
          <label class="field">
            <span>账号</span>
            <div class="field-shell autocomplete-shell">
              <span class="field-icon"><el-icon><User /></el-icon></span>
              <input
                :value="username"
                autocomplete="off"
                placeholder="请输入账号"
                type="text"
                @blur="deferHideAutocomplete"
                @focus="showAutocomplete = Boolean(suggestions.length)"
                @input="emit('update:username', ($event.target as HTMLInputElement).value)"
              />
              <div v-if="showAutocomplete && suggestions.length" class="autocomplete-list">
                <button
                  v-for="item in suggestions"
                  :key="item.username"
                  class="autocomplete-item"
                  type="button"
                  @mousedown.prevent="pickSuggestion(item)"
                >
                  <strong>{{ item.name }}</strong>
                  <small>{{ item.title }} / {{ item.department }}</small>
                </button>
              </div>
            </div>
          </label>

          <label class="field">
            <span>密码</span>
            <div class="field-shell">
              <span class="field-icon"><el-icon><Key /></el-icon></span>
              <input
                :value="password"
                placeholder="请输入密码"
                type="password"
                @input="emit('update:password', ($event.target as HTMLInputElement).value)"
              />
            </div>
          </label>

          <div class="login-actions-row">
            <label class="remember">
              <input checked type="checkbox" />
              <span>记住账号</span>
            </label>
            <button class="text-link" type="button" @click="emit('toggle-register', true)">注册账号</button>
          </div>

          <p v-if="loginError" class="error-text">{{ loginError }}</p>

          <button class="login-submit" :disabled="loadingLogin" type="submit">
            {{ loadingLogin ? '登录中...' : '登录系统' }}
          </button>
        </form>

        <form v-else class="login-form" @submit.prevent="emit('submit-register')">
          <label class="field">
            <span>账号</span>
            <input :value="registerForm.username" placeholder="请输入账号" type="text" @input="updateRegisterField('username', $event)" />
          </label>
          <label class="field">
            <span>密码</span>
            <input :value="registerForm.password" placeholder="请输入密码" type="password" @input="updateRegisterField('password', $event)" />
          </label>
          <label class="field">
            <span>姓名</span>
            <input :value="registerForm.name" placeholder="请输入姓名" type="text" @input="updateRegisterField('name', $event)" />
          </label>

          <div class="register-grid">
            <label class="field">
              <span>角色</span>
              <select :value="registerForm.role" @change="updateRegisterField('role', $event)">
                <option value="doctor">医生</option>
                <option value="nurse">护士</option>
                <option value="pharmacist">药师</option>
                <option value="archivist">档案员</option>
              </select>
            </label>
            <label class="field">
              <span>职称</span>
              <input :value="registerForm.title" placeholder="请输入职称" type="text" @input="updateRegisterField('title', $event)" />
            </label>
          </div>

          <label class="field">
            <span>科室</span>
            <input :value="registerForm.department" placeholder="请输入科室" type="text" @input="updateRegisterField('department', $event)" />
          </label>

          <p v-if="registerError" class="error-text">{{ registerError }}</p>

          <button class="login-submit" :disabled="loadingRegister" type="submit">
            {{ loadingRegister ? '注册中...' : '提交注册' }}
          </button>
          <button class="text-link align-left" type="button" @click="emit('toggle-register', false)">返回登录</button>
        </form>
      </section>
    </main>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 32px 24px;
  background:
    radial-gradient(circle at 16% 16%, rgba(0, 52, 52, 0.08), transparent 26%),
    radial-gradient(circle at 84% 20%, rgba(21, 94, 117, 0.08), transparent 24%),
    linear-gradient(180deg, #f6fbfc 0%, #eef5f6 100%);
}

.login-main {
  width: 100%;
  display: grid;
  place-items: center;
}

.login-card {
  width: min(460px, 100%);
  display: grid;
  gap: 22px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.95);
  padding: 34px 30px;
  box-shadow:
    0 18px 48px rgba(24, 28, 30, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(14px);
}

.login-brand h1 {
  margin: 0;
  color: #181c1e;
  font-family: var(--ws-font-headline);
  font-size: 22px;
  line-height: 1.35;
  font-weight: 700;
}

.login-brand {
  display: grid;
  gap: 4px;
}

.login-brand-copy {
  min-width: 0;
}

.login-form {
  display: grid;
  gap: 16px;
}

.field {
  display: grid;
  gap: 8px;
}

.field span {
  color: #3f4848;
  font-size: 13px;
  font-weight: 700;
}

.field-shell,
.field input,
.field select {
  width: 100%;
  min-height: 48px;
  border: 1px solid #d5dde0;
  border-radius: 14px;
  background: #fff;
}

.field input,
.field select {
  padding: 0 14px;
  font: inherit;
  color: #181c1e;
}

.field-shell {
  position: relative;
  display: flex;
  align-items: center;
  overflow: visible;
}

.field-shell input {
  border: 0;
  min-height: 46px;
  padding-left: 42px;
}

.field-icon {
  position: absolute;
  left: 14px;
  display: inline-flex;
  color: #6f7978;
}

.autocomplete-list {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  right: 0;
  z-index: 3;
  display: grid;
  gap: 4px;
  border: 1px solid #d5dde0;
  border-radius: 14px;
  background: #fff;
  padding: 6px;
  box-shadow: 0 12px 28px rgba(24, 28, 30, 0.08);
}

.autocomplete-item {
  display: grid;
  gap: 2px;
  border: 0;
  border-radius: 10px;
  background: transparent;
  padding: 10px 12px;
  text-align: left;
}

.autocomplete-item strong {
  color: #181c1e;
}

.autocomplete-item small {
  color: #526772;
}

.register-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.login-actions-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.remember {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  color: #526772;
  font-size: 13px;
  line-height: 1;
}

.remember input[type='checkbox'] {
  width: 16px;
  height: 16px;
  min-height: 16px;
  margin: 0;
  padding: 0;
  border-radius: 4px;
  background: transparent;
  box-shadow: none;
  flex: 0 0 auto;
  accent-color: #003434;
}

.remember span {
  white-space: nowrap;
}

.text-link {
  border: 0;
  background: transparent;
  padding: 0;
  color: #0059bb;
  font-weight: 700;
}

.align-left {
  justify-self: flex-start;
}

.error-text {
  margin: 0;
  color: #ba1a1a;
  font-size: 13px;
  font-weight: 600;
}

.login-submit {
  min-height: 50px;
  border: 0;
  border-radius: 14px;
  background: #003434;
  color: #fff;
  font-family: var(--ws-font-headline);
  font-size: 15px;
  font-weight: 700;
}

.login-submit:disabled {
  opacity: 0.72;
}

@media (max-width: 640px) {
  .login-card {
    padding: 26px 20px;
    border-radius: 18px;
  }

  .register-grid {
    grid-template-columns: 1fr;
  }

  .login-brand {
    align-items: flex-start;
  }

  .login-brand h1 {
    font-size: 24px;
  }
}
</style>
