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
import { API_BASE_URL, SITE_BASE_URL } from './config'

console.log('SITE_BASE_URL:', SITE_BASE_URL, 'API_BASE_URL:', API_BASE_URL)
const routes = [
  { path: `${SITE_BASE_URL}/`, component: DataSetSelector },
  { path: `${SITE_BASE_URL}/interpolator/:setname`, component: Interpolator },
]
console.log('Routes:', routes, window.location.pathname)
export const router = createRouter({
  history: createWebHistory(),
  routes,
})
registerPlugins(app)
app.use(router)

app.mount('#app')
