<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import ModelSidebar from '../components/ModelSidebar.vue'
import ModelTopbar from '../components/ModelTopbar.vue'
import { useModelWorkspace } from '../composables/useModelWorkspace'

const workspace = useModelWorkspace()
const router = useRouter()

function handleLogout() {
  workspace.logout()
  void router.replace('/login')
}

onMounted(() => {
  if (workspace.currentUser && !workspace.dashboard) {
    void workspace.refreshAll()
  }
})
</script>

<template>
  <div class="workstation-shell model-shell">
    <ModelSidebar :current-user="workspace.currentUser" @logout="handleLogout" />
    <div class="workstation-main">
      <ModelTopbar
        :health="workspace.health"
        :user="workspace.currentUser"
        :loading="workspace.loading"
        @refresh="workspace.refreshAll"
      />
      <main class="workstation-content">
        <router-view />
      </main>
    </div>
  </div>
</template>
