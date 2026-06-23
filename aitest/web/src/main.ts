import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHashHistory } from 'vue-router'
import { createI18n } from 'vue-i18n'
import App from './App.vue'
import './styles/tokens.css'
import './styles/themes/all.css'
import zh from './locales/zh.json'
import en from './locales/en.json'

// i18n init
const savedLang = localStorage.getItem('tlo-lang') || 'zh'
const i18n = createI18n({ legacy: false, locale: savedLang, fallbackLocale: 'en', messages: { zh, en } })

// Routes — hash mode works without server config
const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', redirect: '/kanban' },
    { path: '/kanban', name: 'kanban', component: () => import('./views/KanbanView.vue') },
    { path: '/gaps', name: 'gaps', component: () => import('./views/GapDiscoveryView.vue') },
    { path: '/chat', name: 'chat', component: () => import('./views/IntelligenceChatView.vue') },
    { path: '/strategy', name: 'strategy', component: () => import('./views/StrategyPlannerView.vue') },
    { path: '/execution', name: 'execution', component: () => import('./views/ExecutionView.vue') },
    { path: '/reports', name: 'reports', component: () => import('./views/ReportsView.vue') },
    { path: '/knowledge', name: 'knowledge', component: () => import('./views/KnowledgeView.vue') },
    { path: '/settings', name: 'settings', component: () => import('./views/SettingsView.vue') },
    { path: '/:pathMatch(.*)*', redirect: '/kanban' },
  ],
})

// Global navigation guard for debugging
router.beforeEach((to, from) => {
  console.log(`[Router] ${from.name || '/'} → ${to.name || to.path}`)
})

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(i18n)
app.mount('#app')
