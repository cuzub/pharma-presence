import { createApp } from 'vue'
import { createPinia } from 'pinia'
import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap-icons/font/bootstrap-icons.css'
import './styles/main.css'
import App from './App.vue'
import router from './router'
import { surErreurSession } from './services/api'
import { useAuthStore } from './stores/auth'

const app = createApp(App)
app.use(createPinia())
app.use(router)

const auth = useAuthStore()
surErreurSession({
  nonAuthentifie: () => {
    auth.oublierSession()
    if (router.currentRoute.value.name !== 'login') {
      router.push({ path: '/login', query: { expiree: '1' } })
    }
  },
  changementMdpRequis: () => {
    auth.marquerChangementMdpRequis()
    router.push('/mot-de-passe')
  }
})

app.mount('#app')
