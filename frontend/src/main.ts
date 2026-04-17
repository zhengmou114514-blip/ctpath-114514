import { createApp } from 'vue'
import './style.css'
import './styles/workstation-theme.css'
import App from './App.vue'
import './services/request'
import router from './router'
import { createPinia } from 'pinia'
import { useAuthStore } from './stores/auth'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia as any)
app.use(router as any)

useAuthStore(pinia).restoreSession()

app.mount('#app')
