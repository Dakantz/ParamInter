/**
 * main.ts
 *
 * Bootstraps Vuetify and other plugins then mounts the App`
 */

import '@/assets/style.css'
// Plugins
import { registerPlugins } from './plugins'
import { createMemoryHistory, createRouter, createWebHistory } from 'vue-router'

// Components
import App from './App.vue'

// Composables
import { createApp } from 'vue'

const app = createApp(App)

import DataSetSelector from './views/DataSetSelector.vue'
import Interpolator from './views/Interpolator.vue'
import { SITE_BASE_URL } from './config'

const routes = [
  { path: '/', component: DataSetSelector },
  { path: '/interpolator/:setname', component: Interpolator },
]

export const router = createRouter({
  history: createWebHistory(SITE_BASE_URL),
  routes,
})
registerPlugins(app)
app.use(router)

app.mount('#app')
