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

const systemStatus = computed(() => ({
  mode: `${String(props.health?.mode ?? 'demo').toUpperCase()} 模式`,
  model: props.health?.model_available ? '模型可用' : '模型降级',
  db: '业务数据源 · MySQL',
}))

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
  <div class="login-shell">
    <div class="login-bg"></div>
    <div class="login-overlay"></div>

    <main class="login-main">
      <section class="login-card">
        <div class="login-brand">
          <h1>CTPATH</h1>
          <p>慢病辅助诊疗业务系统</p>
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
                  <small>@{{ item.username }}</small>
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

          <p class="login-hint">演示账号：`demo_clinic / demo123456`。登录后将进入慢病辅助诊疗工作台。</p>
          <p v-if="loginError" class="error-text">{{ loginError }}</p>

          <button class="login-submit" :disabled="loadingLogin" type="submit">
            {{ loadingLogin ? '登录中...' : '登录系统' }}
          </button>
        </form>

        <form v-else class="login-form" @submit.prevent="emit('submit-register')">
          <div class="register-copy">
            <h2>注册账号</h2>
            <p>沿用当前系统已有注册流程，为毕设演示补齐真实注册入口，不新增第二套认证逻辑。</p>
          </div>

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
            {{ loadingRegister ? '注册中...' : '完成注册' }}
          </button>
          <button class="text-link align-left" type="button" @click="emit('toggle-register', false)">返回登录</button>
        </form>

        <div class="login-legal">
          <p>系统仅用于慢病辅助诊疗业务展示和答辩演示，不覆盖完整 HIS 全流程。</p>
        </div>
      </section>
    </main>

    <footer class="login-footer">
      <div class="footer-left">
        <span class="footer-dot"></span>
        <span>系统状态</span>
      </div>
      <div class="footer-right">
        <span>{{ systemStatus.mode }}</span>
        <span>{{ systemStatus.model }}</span>
        <span>{{ systemStatus.db }}</span>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.login-shell {
  position: relative;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  overflow: hidden;
}

.login-bg,
.login-overlay {
  position: absolute;
  inset: 0;
}

.login-bg {
  background:
    radial-gradient(circle at top left, rgba(140, 210, 215, 0.28), transparent 38%),
    radial-gradient(circle at bottom right, rgba(76, 97, 108, 0.16), transparent 32%),
    linear-gradient(180deg, rgba(247, 250, 251, 0.92), rgba(235, 238, 239, 0.98));
}

.login-overlay {
  background: linear-gradient(180deg, rgba(247, 250, 251, 0.82), rgba(235, 238, 239, 0.94));
}

.login-main {
  position: relative;
  z-index: 1;
  flex: 1;
  display: grid;
  place-items: center;
  padding: 24px;
}

.login-card {
  width: min(520px, calc(100vw - 48px));
  display: grid;
  gap: 28px;
  border-radius: 16px;
  background: #fff;
  padding: 40px;
  box-shadow: 0 12px 32px -4px rgba(24, 28, 29, 0.06);
}

.login-brand {
  text-align: center;
}

.login-brand h1 {
  margin: 0;
  color: #004347;
  font-size: clamp(52px, 7vw, 74px);
  font-weight: 800;
  letter-spacing: -0.04em;
}

.login-brand p {
  margin: 6px 0 0;
  color: #3f4849;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.16em;
  text-transform: uppercase;
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
  color: #181c1d;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.field-shell,
.field :deep(input),
.field :deep(select) {
  width: 100%;
}

.field :deep(input),
.field :deep(select) {
  border: 0;
  border-bottom: 1px solid rgba(190, 200, 201, 0.45);
  border-radius: 4px 4px 0 0;
  background: #f1f4f5;
  padding: 12px 14px;
  min-height: 48px;
  color: #181c1d;
}

.field-shell {
  position: relative;
}

.field-shell :deep(input) {
  padding-left: 46px;
}

.field-icon {
  position: absolute;
  left: 14px;
  top: 50%;
  transform: translateY(-50%);
  color: #6f797a;
  z-index: 1;
}

.autocomplete-shell {
  position: relative;
}

.autocomplete-list {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  right: 0;
  z-index: 4;
  display: grid;
  gap: 0;
  overflow: hidden;
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 12px 32px -4px rgba(24, 28, 29, 0.1);
}

.autocomplete-item {
  border: 0;
  background: transparent;
  padding: 12px 14px;
  text-align: left;
}

.autocomplete-item:hover {
  background: #f1f4f5;
}

.autocomplete-item strong {
  display: block;
}

.autocomplete-item small {
  color: #526772;
}

.login-actions-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.remember {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #526772;
}

.login-hint,
.register-copy p {
  margin: 0;
  color: #526772;
  line-height: 1.6;
}

.register-copy h2 {
  margin: 0 0 8px;
}

.register-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.error-text {
  margin: 0;
  border-radius: 12px;
  background: #ffdad6;
  padding: 12px 14px;
  color: #93000a;
  font-weight: 700;
}

.login-submit {
  border: 0;
  border-radius: 6px;
  background: linear-gradient(180deg, #004347 0%, #005c61 100%);
  min-height: 48px;
  color: #fff;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.text-link {
  border: 0;
  background: transparent;
  color: #004347;
  font-weight: 700;
}

.align-left {
  justify-self: start;
}

.login-legal {
  border-top: 1px solid rgba(190, 200, 201, 0.18);
  padding-top: 16px;
  text-align: center;
}

.login-legal p {
  margin: 0;
  color: rgba(63, 72, 73, 0.72);
  font-size: 12px;
}

.login-footer {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  background: #f1f4f5;
  padding: 12px 24px;
}

.footer-left,
.footer-right {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
  color: #526772;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.footer-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: #004347;
  box-shadow: 0 0 0 6px rgba(0, 67, 71, 0.1);
}

@media (max-width: 720px) {
  .login-card {
    width: 100%;
    padding: 28px 22px;
  }

  .register-grid,
  .login-footer {
    grid-template-columns: 1fr;
    display: grid;
  }
}
</style>
