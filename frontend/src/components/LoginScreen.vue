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
  model: props.health?.model_available ? '推理服务可用' : '推理服务告警',
  db: props.health?.mode === 'mysql' ? '业务数据源 / MySQL' : '业务数据源 / Demo',
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
    <div class="login-left">
      <div class="login-left-overlay"></div>
      <div class="login-left-content">
        <div class="logo-box">CT</div>
        <div class="brand-copy">
          <h1>CTpath 慢病辅助诊疗业务系统</h1>
          <p>基于时序知识图谱的慢病辅助诊疗工作台，用于患者档案、病程追踪、预测建议与随访闭环管理。</p>
        </div>
        <div class="trust-row">
          <span class="trust-badge">临床工作站</span>
          <span class="trust-badge">预测建议联动</span>
          <span class="trust-badge">随访闭环管理</span>
        </div>
      </div>
    </div>

    <main class="login-main">
      <section class="login-card">
        <div class="login-brand">
          <h2>{{ registerMode ? '注册账号' : '登录系统' }}</h2>
          <p>
            {{
              registerMode
                ? '填写基础账号信息后即可申请进入慢病辅助诊疗工作台。注册成功后使用系统分配角色进入对应业务页面。'
                : '进入 CTpath 慢病辅助诊疗业务系统，查看患者档案、病程摘要、预测建议与随访任务。'
            }}
          </p>
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

          <p class="login-hint">演示账号：`demo_clinic / demo123456`，用于进入医生工作台并查看完整主闭环。</p>
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

        <div class="login-legal">
          <p>系统聚焦慢病辅助诊疗，不覆盖收费、住院、药房库存等完整 HIS 范围。</p>
        </div>
      </section>
    </main>

    <footer class="login-footer">
      <div class="footer-left">
        <span class="footer-dot"></span>
        <span>系统在线</span>
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
  display: grid;
  min-height: 100vh;
  grid-template-columns: minmax(0, 45%) minmax(0, 1fr);
  background: #f7fafc;
}

.login-left {
  position: relative;
  display: none;
  overflow: hidden;
  background:
    linear-gradient(145deg, rgba(0, 52, 52, 0.95), rgba(0, 77, 77, 0.78)),
    radial-gradient(circle at top left, rgba(176, 238, 237, 0.18), transparent 36%);
}

.login-left-overlay {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 20% 20%, rgba(148, 209, 209, 0.18), transparent 24%),
    radial-gradient(circle at 75% 72%, rgba(173, 199, 255, 0.14), transparent 26%);
}

.login-left-content {
  position: relative;
  z-index: 1;
  display: flex;
  height: 100%;
  flex-direction: column;
  justify-content: center;
  gap: 24px;
  padding: 64px;
  color: #fff;
}

.logo-box {
  display: grid;
  width: 64px;
  height: 64px;
  place-items: center;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.92);
  color: #003434;
  font-family: var(--ws-font-headline);
  font-size: 24px;
  font-weight: 900;
  letter-spacing: 0.08em;
}

.brand-copy h1 {
  margin: 0;
  font-family: var(--ws-font-headline);
  font-size: clamp(36px, 3vw, 46px);
  line-height: 1.15;
}

.brand-copy p {
  margin: 14px 0 0;
  max-width: 460px;
  color: rgba(255, 255, 255, 0.82);
  font-size: 18px;
  line-height: 1.7;
}

.trust-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.trust-badge {
  display: inline-flex;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.12);
  padding: 8px 14px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.06em;
}

.login-main {
  display: grid;
  place-items: center;
  padding: 32px 24px 88px;
}

.login-card {
  width: min(460px, 100%);
  display: grid;
  gap: 24px;
  border-radius: 24px;
  background: #fff;
  padding: 36px 32px;
  box-shadow: 0 16px 40px rgba(24, 28, 30, 0.08);
}

.login-brand h2 {
  margin: 0;
  color: #181c1e;
  font-family: var(--ws-font-headline);
  font-size: 28px;
  font-weight: 700;
}

.login-brand p {
  margin: 10px 0 0;
  color: #526772;
  line-height: 1.7;
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
}

.remember {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #526772;
  font-size: 13px;
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

.login-hint,
.login-legal p {
  margin: 0;
  color: #526772;
  line-height: 1.65;
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

.login-footer {
  position: fixed;
  right: 0;
  bottom: 0;
  left: 0;
  display: flex;
  min-height: 56px;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  border-top: 1px solid rgba(191, 200, 200, 0.7);
  background: rgba(247, 250, 252, 0.94);
  padding: 0 24px;
  color: #526772;
  backdrop-filter: blur(12px);
}

.footer-left,
.footer-right {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.footer-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: #2f7d32;
}

@media (min-width: 1024px) {
  .login-left {
    display: block;
  }
}

@media (max-width: 1023px) {
  .login-shell {
    grid-template-columns: 1fr;
  }

  .login-main {
    padding-bottom: 104px;
  }
}

@media (max-width: 640px) {
  .login-card {
    padding: 28px 20px;
    border-radius: 18px;
  }

  .register-grid {
    grid-template-columns: 1fr;
  }

  .login-footer {
    align-items: flex-start;
    padding-top: 10px;
    padding-bottom: 10px;
  }
}
</style>
