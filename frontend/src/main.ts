import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
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
useAuthStore(pinia).restoreSession()
app.use(router as any)
app.use(ElementPlus as any)

app.mount('#app')
