<script setup lang="ts">
import { onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import LoginScreenSimple from '../components/LoginScreenSimple.vue'
import { useWorkspaceController } from '../composables/useWorkspaceController'

const route = useRoute()
const router = useRouter()
const workspace = useWorkspaceController()

function updateRegisterField(field: keyof typeof workspace.registerForm, value: string) {
  ;(workspace.registerForm as Record<string, string>)[field] = value
}

function redirectAfterLogin() {
  const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
  void router.replace(redirect || '/')
}

async function submitLogin() {
  await workspace.submitLogin()
  if (workspace.currentDoctor) {
    redirectAfterLogin()
  }
}

async function submitRegister() {
  await workspace.submitRegister()
  if (workspace.currentDoctor) {
    redirectAfterLogin()
  }
}

onMounted(async () => {
  await workspace.initialize()
  if (workspace.currentDoctor) {
    redirectAfterLogin()
  }
})

watch(
  () => workspace.currentDoctor,
  (doctor) => {
    if (doctor) {
      redirectAfterLogin()
    }
  }
)
</script>

<template>
  <LoginScreenSimple
    :username="workspace.username"
    :password="workspace.password"
    :login-error="workspace.loginError"
    :loading-login="workspace.loadingLogin"
    :health="workspace.health"
    :register-mode="workspace.registerMode"
    :register-form="workspace.registerForm"
    :register-error="workspace.registerError"
    :loading-register="workspace.loadingRegister"
    @update:username="workspace.username = $event"
    @update:password="workspace.password = $event"
    @update:register-field="updateRegisterField"
    @submit-login="submitLogin"
    @toggle-register="workspace.toggleRegister"
    @submit-register="submitRegister"
  />
</template>
