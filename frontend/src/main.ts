import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import { configureAuthTransport } from '@/api/client'
import App from './App.vue'
import router from './router'
import { useAuth } from './stores/auth'

async function startApp() {
  const app = createApp(App)
  const pinia = createPinia()
  app.use(pinia)

  const auth = useAuth(pinia)
  configureAuthTransport({
    getAccessToken: () => auth.access,
    refreshAccess: () => auth.refreshAccess(),
    onSessionExpired: async () => {
      auth.logout()
      const current = router.currentRoute.value
      if (current.name !== 'login') {
        await router.replace({ name: 'login', query: { next: current.fullPath } })
      }
    },
  })

  await auth.initialize()
  app.use(router)
  await router.isReady()
  app.mount('#app')
}

void startApp()
