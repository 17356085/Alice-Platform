/** Vue Router — v1.0 segmented: Dashboard | Workspace | App Settings.

Routes:
  /                    → /dashboard
  /dashboard           → DashboardView (all projects overview)
  /workspace/kanban    → KanbanView (per-project SOP board)
  /workspace/gaps      → GapDiscoveryView
  /workspace/chat      → IntelligenceChatView
  /workspace/execution → ExecutionView
  /workspace/reports   → ReportsView
  /workspace/knowledge → KnowledgeView
  /workspace/settings  → ProjectSettingsView
  /settings            → SettingsView (app-level)
  /onboarding          → OnboardingWizardView
  /strategy            → StrategyPlannerView (legacy, kept for compat)
*/
import { createRouter, createWebHashHistory, type RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  { path: '/', redirect: '/dashboard' },

  // Dashboard
  { path: '/dashboard', name: 'dashboard', component: () => import('../views/DashboardView.vue') },

  // Workspace (per-project)
  { path: '/workspace/kanban',    name: 'kanban',    component: () => import('../views/KanbanView.vue') },
  { path: '/workspace/gaps',      name: 'gaps',      component: () => import('../views/GapDiscoveryView.vue') },
  { path: '/workspace/chat',      name: 'chat',      component: () => import('../views/IntelligenceChatView.vue') },
  { path: '/workspace/execution', name: 'execution', component: () => import('../views/ExecutionView.vue') },
  { path: '/workspace/reports',   name: 'reports',   component: () => import('../views/ReportsView.vue') },
  { path: '/workspace/knowledge', name: 'knowledge', component: () => import('../views/KnowledgeView.vue') },
  { path: '/workspace/terminal',  name: 'terminal',  component: () => import('../views/AgentTerminalView.vue') },
  { path: '/workspace/ideation',  name: 'ideation',  component: () => import('../views/IdeationView.vue') },
  { path: '/workspace/integrations', name: 'integrations', component: () => import('../views/IntegrationView.vue') },
  { path: '/workspace/settings',  name: 'project-settings', component: () => import('../views/ProjectSettingsView.vue') },

  // App settings
  { path: '/settings',   name: 'settings',   component: () => import('../views/SettingsView.vue') },
  { path: '/onboarding', name: 'onboarding', component: () => import('../views/OnboardingWizardView.vue') },
  { path: '/strategy',   name: 'strategy',   component: () => import('../views/StrategyPlannerView.vue') },

  // Legacy redirects (backward compat)
  { path: '/kanban',    redirect: '/workspace/kanban' },
  { path: '/gaps',      redirect: '/workspace/gaps' },
  { path: '/chat',      redirect: '/workspace/chat' },
  { path: '/execution', redirect: '/workspace/execution' },
  { path: '/reports',   redirect: '/workspace/reports' },
  { path: '/knowledge', redirect: '/workspace/knowledge' },

  { path: '/:pathMatch(.*)*', redirect: '/dashboard' },
]

export const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

router.beforeEach((to, from) => {
  console.log(`[Router] ${from.name || '/'} → ${to.name || to.path}`)
})
