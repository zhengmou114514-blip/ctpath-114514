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

const serviceText = computed(() => (props.health?.status === 'ok' ? '业务服务正常' : '服务连接中'))
const suggestions = computed(() => {
  const keyword = props.username.trim().toLowerCase()
  if (!keyword) return savedAccounts.value.slice(0, 4)
  return savedAccounts.value
    .filter((item) => item.username.toLowerCase().includes(keyword) || item.name.toLowerCase().includes(keyword))
    .slice(0, 4)
})

onMounted(() => {
  savedAccounts.value = getSavedAccounts()
})

watch(
  () => props.username,
  () => {
    showAutocomplete.value = Boolean(suggestions.value.length)
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

function hideAutocomplete() {
  globalThis.setTimeout(() => {
    showAutocomplete.value = false
  }, 120)
}
</script>

<template>
  <main class="login-simple-page">
    <section class="login-hero-panel">
      <div class="brand-row">
        <div class="brand-emblem">慢</div>
        <div>
          <strong>慢病辅助诊疗业务系统</strong>
          <span>门诊慢病管理入口</span>
        </div>
      </div>

      <div class="hero-copy">
        <h1>慢病门诊工作站</h1>
        <p>慢性病辅助诊疗系统整合患者档案、病程时间线、模型辅助分析、随访闭环、药品权限与治理中心，进入后按角色呈现互斥的业务工作台。</p>
      </div>

      <div class="capability-grid">
        <article>
          <span>01</span>
          <strong>风险识别</strong>
          <p>待处理患者、当前摘要、风险提示与模型摘要。</p>
        </article>
        <article>
          <span>02</span>
          <strong>模型辅助</strong>
          <p>当前患者洞察、证据摘要、建议来源与降级状态。</p>
        </article>
        <article>
          <span>03</span>
          <strong>随访闭环</strong>
          <p>随访任务、联系记录、完成关闭与医生复核。</p>
        </article>
      </div>
    </section>

    <section class="login-form-panel" aria-label="登录认证">
      <div class="form-heading">
        <p>{{ serviceText }}</p>
        <h2>{{ registerMode ? '账号注册' : '登录认证' }}</h2>
        <span>请输入账号密码进入对应角色工作台</span>
      </div>

      <form v-if="!registerMode" class="simple-login-form" @submit.prevent="emit('submit-login')">
        <label class="simple-field">
          <span>账号</span>
          <div class="simple-field-shell">
            <el-icon><User /></el-icon>
            <input
              :value="username"
              autocomplete="off"
              placeholder="请输入账号"
              type="text"
              @blur="hideAutocomplete"
              @focus="showAutocomplete = Boolean(suggestions.length)"
              @input="emit('update:username', ($event.target as HTMLInputElement).value)"
            />
            <div v-if="showAutocomplete && suggestions.length" class="simple-autocomplete">
              <button
                v-for="item in suggestions"
                :key="item.username"
                type="button"
                @mousedown.prevent="pickSuggestion(item)"
              >
                <strong>{{ item.name }}</strong>
                <small>{{ item.title }} / {{ item.department }}</small>
              </button>
            </div>
          </div>
        </label>

        <label class="simple-field">
          <span>密码</span>
          <div class="simple-field-shell">
            <el-icon><Key /></el-icon>
            <input
              :value="password"
              placeholder="请输入密码"
              type="password"
              @input="emit('update:password', ($event.target as HTMLInputElement).value)"
            />
          </div>
        </label>

        <div class="form-row">
          <label class="remember-line">
            <input checked type="checkbox" />
            <span>记住账号</span>
          </label>
          <button class="link-button" type="button" @click="emit('toggle-register', true)">注册账号</button>
        </div>

        <p v-if="loginError" class="simple-error">{{ loginError }}</p>
        <button class="simple-submit" :disabled="loadingLogin" type="submit">
          {{ loadingLogin ? '登录中...' : '登录系统' }}
        </button>

        <div class="demo-note">
          <strong>演示账号</strong>
          <span>可输入已保存账号快速进入医生、护士、药师或管理员工作台。</span>
        </div>
      </form>

      <form v-else class="simple-login-form" @submit.prevent="emit('submit-register')">
        <label class="simple-field">
          <span>账号</span>
          <input :value="registerForm.username" placeholder="请输入账号" type="text" @input="updateRegisterField('username', $event)" />
        </label>
        <label class="simple-field">
          <span>密码</span>
          <input :value="registerForm.password" placeholder="请输入密码" type="password" @input="updateRegisterField('password', $event)" />
        </label>
        <label class="simple-field">
          <span>姓名</span>
          <input :value="registerForm.name" placeholder="请输入姓名" type="text" @input="updateRegisterField('name', $event)" />
        </label>
        <div class="register-row">
          <label class="simple-field">
            <span>角色</span>
            <select :value="registerForm.role" @change="updateRegisterField('role', $event)">
              <option value="doctor">医生</option>
              <option value="nurse">护士</option>
              <option value="pharmacist">药师</option>
              <option value="archivist">档案员</option>
            </select>
          </label>
          <label class="simple-field">
            <span>职称</span>
            <input :value="registerForm.title" placeholder="请输入职称" type="text" @input="updateRegisterField('title', $event)" />
          </label>
        </div>
        <label class="simple-field">
          <span>科室</span>
          <input :value="registerForm.department" placeholder="请输入科室" type="text" @input="updateRegisterField('department', $event)" />
        </label>
        <p v-if="registerError" class="simple-error">{{ registerError }}</p>
        <button class="simple-submit" :disabled="loadingRegister" type="submit">
          {{ loadingRegister ? '注册中...' : '提交注册' }}
        </button>
        <button class="link-button align-start" type="button" @click="emit('toggle-register', false)">返回登录</button>
      </form>
    </section>
  </main>
</template>

<style scoped>
.login-simple-page {
  min-height: 100vh;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 420px;
  gap: 44px;
  align-items: center;
  padding: 48px 72px;
  background:
    linear-gradient(90deg, rgba(0, 52, 52, 0.05) 1px, transparent 1px),
    linear-gradient(180deg, #f7fafb 0%, #eef5f6 100%);
  background-size: 28px 28px, auto;
}

.login-hero-panel {
  display: grid;
  gap: 40px;
  max-width: 760px;
}

.brand-row {
  display: inline-flex;
  width: fit-content;
  align-items: center;
  gap: 14px;
  color: #172033;
}

.brand-emblem {
  display: grid;
  width: 48px;
  height: 48px;
  place-items: center;
  border-radius: 6px;
  background: #003434;
  color: #fff;
  font-size: 20px;
  font-weight: 800;
}

.brand-row strong,
.brand-row span {
  display: block;
}

.brand-row strong {
  font-size: 18px;
}

.brand-row span {
  margin-top: 2px;
  color: #526772;
  font-size: 12px;
  font-weight: 700;
}

.hero-copy {
  display: grid;
  gap: 18px;
}

.hero-copy h1 {
  max-width: 680px;
  margin: 0;
  color: #181c1e;
  font-size: 44px;
  line-height: 1.12;
  font-weight: 800;
}

.hero-copy p {
  max-width: 680px;
  margin: 0;
  color: #526772;
  font-size: 16px;
  line-height: 1.9;
}

.capability-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.capability-grid article {
  min-height: 150px;
  padding: 20px;
  border: 1px solid #d5dde0;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.74);
  box-shadow: 0 1px 6px rgba(24, 28, 30, 0.08);
}

.capability-grid span {
  color: #005c61;
  font-size: 12px;
  font-weight: 800;
}

.capability-grid strong {
  display: block;
  margin-top: 10px;
  color: #181c1e;
  font-size: 16px;
}

.capability-grid p {
  margin: 10px 0 0;
  color: #526772;
  font-size: 13px;
  line-height: 1.7;
}

.login-form-panel {
  display: grid;
  gap: 24px;
  padding: 30px;
  border: 1px solid #d5dde0;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 18px 48px rgba(24, 28, 30, 0.08);
}

.form-heading {
  display: grid;
  gap: 6px;
}

.form-heading p {
  width: fit-content;
  margin: 0;
  padding: 5px 10px;
  border-radius: 4px;
  background: #dceced;
  color: #005c61;
  font-size: 12px;
  font-weight: 800;
}

.form-heading h2 {
  margin: 6px 0 0;
  color: #181c1e;
  font-size: 26px;
}

.form-heading span {
  color: #526772;
  font-size: 13px;
}

.simple-login-form,
.simple-field {
  display: grid;
  gap: 14px;
}

.simple-field {
  gap: 8px;
}

.simple-field > span {
  color: #3f4848;
  font-size: 13px;
  font-weight: 800;
}

.simple-field input,
.simple-field select,
.simple-field-shell {
  width: 100%;
  min-height: 44px;
  border: 1px solid #d5dde0;
  border-radius: 6px;
  background: #fff;
}

.simple-field input,
.simple-field select {
  padding: 0 12px;
  color: #181c1e;
}

.simple-field-shell {
  position: relative;
  display: flex;
  align-items: center;
}

.simple-field-shell .el-icon {
  position: absolute;
  left: 13px;
  color: #6f7978;
}

.simple-field-shell input {
  min-height: 42px;
  border: 0;
  padding-left: 40px;
}

.simple-autocomplete {
  position: absolute;
  z-index: 5;
  top: calc(100% + 6px);
  left: 0;
  right: 0;
  display: grid;
  gap: 4px;
  padding: 6px;
  border: 1px solid #d5dde0;
  border-radius: 6px;
  background: #fff;
  box-shadow: 0 12px 28px rgba(24, 28, 30, 0.08);
}

.simple-autocomplete button {
  display: grid;
  gap: 2px;
  border: 0;
  border-radius: 4px;
  background: transparent;
  padding: 10px;
  text-align: left;
}

.simple-autocomplete button:hover {
  background: #f7fafb;
}

.simple-autocomplete strong {
  color: #181c1e;
}

.simple-autocomplete small {
  color: #526772;
}

.form-row,
.remember-line {
  display: flex;
  align-items: center;
}

.form-row {
  justify-content: space-between;
  gap: 12px;
}

.remember-line {
  gap: 8px;
  color: #526772;
  font-size: 13px;
}

.remember-line input {
  width: 16px;
  height: 16px;
  min-height: 16px;
  margin: 0;
  padding: 0;
  accent-color: #003434;
}

.link-button {
  border: 0;
  background: transparent;
  color: #0059bb;
  font-size: 13px;
  font-weight: 800;
}

.align-start {
  justify-self: flex-start;
}

.simple-error {
  margin: 0;
  color: #ba1a1a;
  font-size: 13px;
  font-weight: 700;
}

.simple-submit {
  min-height: 46px;
  border: 0;
  border-radius: 6px;
  background: #003434;
  color: #fff;
  font-weight: 800;
  box-shadow: 0 10px 22px rgba(0, 52, 52, 0.18);
}

.simple-submit:disabled {
  opacity: 0.68;
  cursor: not-allowed;
}

.demo-note {
  display: grid;
  gap: 4px;
  padding: 12px;
  border-radius: 6px;
  background: #f7fafb;
  color: #526772;
  font-size: 12px;
  line-height: 1.6;
}

.demo-note strong {
  color: #181c1e;
}

.register-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

@media (max-width: 980px) {
  .login-simple-page {
    grid-template-columns: 1fr;
    gap: 28px;
    padding: 32px 24px;
  }

  .capability-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 560px) {
  .login-simple-page {
    padding: 24px 16px;
  }

  .hero-copy h1 {
    font-size: 32px;
  }

  .login-form-panel {
    padding: 22px;
  }

  .register-row {
    grid-template-columns: 1fr;
  }
}
</style>
