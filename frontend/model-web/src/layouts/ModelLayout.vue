<script setup lang="ts">
import ModelSidebar from '../components/ModelSidebar.vue'
import ModelTopbar from '../components/ModelTopbar.vue'
import { useModelWorkspace } from '../composables/useModelWorkspace'

const workspace = useModelWorkspace()
</script>

<template>
  <div class="workstation-shell model-shell">
    <ModelSidebar :current-user="workspace.currentUser" @logout="workspace.logout" />
    <div class="workstation-main">
      <ModelTopbar
        :health="workspace.health"
        :user="workspace.currentUser"
        @refresh="workspace.refreshAll"
      />
      <main class="workstation-content">
        <router-view />
      </main>
    </div>
  </div>
</template>
