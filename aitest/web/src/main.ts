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
    { path: '/settings', name: 'settings', component: () => import('./views/SettingsView.vue') },
  ],
})

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')
