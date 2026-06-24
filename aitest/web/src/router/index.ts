/** Vue Router — v1.1: Project-scoped routes. Legacy /workspace/* → /projects/:id/* redirects.

  Routes:
    /                               → /dashboard
    /dashboard                      → DashboardView (all projects + platform health)
    /projects/:id                   → ProjectOverview (module grid + SOP progress)
    /projects/:id/execution         → ExecutionView (SOP control + Agent terminal)
    /projects/:id/observability     → ObservabilityView (Timeline + Metrics + Logs)
    /projects/:id/artifacts         → ArtifactsView (file browser + preview)
    /projects/:id/knowledge         → KnowledgeView (ChromaDB + Memory hits)
    /projects/:id/reports           → ReportsView (KPI + reports)
    /projects/:id/settings          → ProjectSettingsView
    /projects/:id/chat              → IntelligenceChatView
    /settings                       → SettingsView (app-level)
    /onboarding                     → OnboardingWizardView

  Legacy: /workspace/* and bare paths redirect to /projects/:id/*
*/
import { createRouter, createWebHashHistory, type RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  { path: '/', redirect: '/dashboard' },

  // ── Dashboard ─────────────────────────────────────────────────────────
  { path: '/dashboard', name: 'dashboard', component: () => import('../views/DashboardView.vue') },

  // ── Project Workspace (new canonical paths) ───────────────────────────
  {
    path: '/projects/:id',
    name: 'project-overview',
    component: () => import('../views/ProjectOverviewView.vue'),
  },
  {
    path: '/projects/:id/execution',
    name: 'project-execution',
    component: () => import('../views/ExecutionView.vue'),
  },
  {
    path: '/projects/:id/observability',
    name: 'project-observability',
    component: () => import('../views/ObservabilityView.vue'),
  },
  {
    path: '/projects/:id/artifacts',
    name: 'project-artifacts',
    component: () => import('../views/ArtifactsView.vue'),
  },
  {
    path: '/projects/:id/knowledge',
    name: 'project-knowledge',
    component: () => import('../views/KnowledgeView.vue'),
  },
  {
    path: '/projects/:id/reports',
    name: 'project-reports',
    component: () => import('../views/ReportsView.vue'),
  },
  {
    path: '/projects/:id/settings',
    name: 'project-settings',
    component: () => import('../views/ProjectSettingsView.vue'),
  },
  {
    path: '/projects/:id/chat',
    name: 'project-chat',
    component: () => import('../views/IntelligenceChatView.vue'),
  },
  {
    path: '/projects/:id/gaps',
    name: 'project-gaps',
    component: () => import('../views/GapDiscoveryView.vue'),
  },
  {
    path: '/projects/:id/strategy',
    name: 'project-strategy',
    component: () => import('../views/StrategyPlannerView.vue'),
  },
  {
    path: '/projects/:id/kanban',
    name: 'project-kanban',
    component: () => import('../views/KanbanView.vue'),
  },
  {
    path: '/projects/:id/terminal',
    name: 'project-terminal',
    component: () => import('../views/AgentTerminalView.vue'),
  },

  // ── App-level ─────────────────────────────────────────────────────────
  { path: '/settings',   name: 'settings',   component: () => import('../views/SettingsView.vue') },
  { path: '/onboarding', name: 'onboarding', component: () => import('../views/OnboardingWizardView.vue') },

  // ── Legacy /workspace/* → redirect to /projects/active/* ──────────────
  // Uses active project from localStorage (project store)
  { path: '/workspace/:view(.*)', redirect: to => {
    const active = localStorage.getItem('tlo-active-project') || 'default'
    const view = to.params.view || 'execution'
    return `/projects/${active}/${view}`
  }},
  // Legacy bare paths
  { path: '/kanban',    redirect: '/dashboard' },
  { path: '/gaps',      redirect: '/dashboard' },
  { path: '/chat',      redirect: '/dashboard' },
  { path: '/execution', redirect: '/dashboard' },
  { path: '/reports',   redirect: '/dashboard' },
  { path: '/knowledge', redirect: '/dashboard' },
  { path: '/strategy',  redirect: '/dashboard' },

  { path: '/:pathMatch(.*)*', redirect: '/dashboard' },
]

export const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

router.beforeEach((to, from) => {
  console.log(`[Router] ${from.name || '/'} → ${to.name || to.path}`)
})
