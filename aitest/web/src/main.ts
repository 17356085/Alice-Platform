import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import './styles/tokens.css'
import './styles/themes/all.css'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'kanban', component: () => import('./views/KanbanView.vue') },
    { path: '/execution', name: 'execution', component: () => import('./views/ExecutionView.vue') },
    { path: '/reports', name: 'reports', component: () => import('./views/ReportsView.vue') },
    { path: '/knowledge', name: 'knowledge', component: () => import('./views/KnowledgeView.vue') },
    { path: '/gaps', name: 'gaps', component: () => import('./views/GapDiscoveryView.vue'), meta: { title: '🔍 Gap Discovery' } },
    { path: '/chat', name: 'chat', component: () => import('./views/IntelligenceChatView.vue'), meta: { title: '💬 Intelligence Chat' } },
    { path: '/strategy', name: 'strategy', component: () => import('./views/StrategyPlannerView.vue'), meta: { title: '🗺 Strategy Planner' } },
    { path: '/settings', name: 'settings', component: () => import('./views/SettingsView.vue'), meta: { title: '⚙️ Settings' } },
  ],
})

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')
