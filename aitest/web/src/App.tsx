/** Root layout — React 18 port. Segmented sidebar + project selector in header.
 *
 * Key difference from Vue: <router-view /> replaced by <Routes>/<Outlet>.
 * No reactive proxy cycle — React's unidirectional data flow breaks the OOM loop.
 */
import { useEffect, useMemo, lazy, Suspense } from 'react'
import { Routes, Route, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { LayoutDashboard } from 'lucide-react'
import SidebarNav from './components/SidebarNav'
import KanbanHeader from './components/KanbanHeader'
import ProjectSelector from './components/ProjectSelector'
import Toast from './components/Toast'
import { useKanbanWS } from './hooks/useKanbanWS'
import { useProjectStore } from './stores/project'

// ── Lazy views ─────────────────────────────────────────────────
const DashboardView = lazy(() => import('./views/DashboardView'))
const ProjectOverviewView = lazy(() => import('./views/ProjectOverviewView'))
const ExecutionView = lazy(() => import('./views/ExecutionView'))
const ObservabilityView = lazy(() => import('./views/ObservabilityView'))
const ArtifactsView = lazy(() => import('./views/ArtifactsView'))
const KnowledgeView = lazy(() => import('./views/KnowledgeView'))
const ReportsView = lazy(() => import('./views/ReportsView'))
const ProjectSettingsView = lazy(() => import('./views/ProjectSettingsView'))
const IntelligenceChatView = lazy(() => import('./views/IntelligenceChatView'))
const GapDiscoveryView = lazy(() => import('./views/GapDiscoveryView'))
const StrategyPlannerView = lazy(() => import('./views/StrategyPlannerView'))
const KanbanView = lazy(() => import('./views/KanbanView'))
const AgentTerminalView = lazy(() => import('./views/AgentTerminalView'))
const SettingsView = lazy(() => import('./views/SettingsView'))
const OnboardingWizardView = lazy(() => import('./views/OnboardingWizardView'))

// ── View title mapping ─────────────────────────────────────────
const viewTitles: Record<string, string> = {
  dashboard: '面板', kanban: 'SOP 看板', gaps: '缺口发现',
  chat: '智能对话', execution: '执行监控', terminal: 'Agent 终端',
  reports: '测试报告', knowledge: '知识库', settings: '应用设置',
  onboarding: '新建项目', strategy: '策略规划',
  overview: '项目概览', observability: '可观测性', artifacts: '产物',
}

function useCurrentViewName(): string {
  const location = useLocation()
  return useMemo(() => {
    // /projects/:id/kanban → kanban, /dashboard → dashboard
    const parts = location.pathname.split('/').filter(Boolean)
    if (parts[0] === 'projects') return parts[2] || 'overview'
    return parts[0] || 'dashboard'
  }, [location.pathname])
}

const Loading = () => <div className="p-8 text-center text-muted-foreground text-sm">Loading...</div>

// ── Component ──────────────────────────────────────────────────

export default function App() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { connect } = useKanbanWS()
  const init = useProjectStore(s => s.init)
  const currentViewName = useCurrentViewName()

  // Theme init
  useEffect(() => {
    const savedTheme = localStorage.getItem('tlo-theme-name') || 'default'
    const savedDark = localStorage.getItem('tlo-theme') === 'dark'
    document.documentElement.setAttribute('data-theme', savedTheme)
    if (savedDark) document.documentElement.classList.add('dark')

    const onStorage = (e: StorageEvent) => {
      if (e.key === 'tlo-theme-name' && e.newValue)
        document.documentElement.setAttribute('data-theme', e.newValue)
      if (e.key === 'tlo-theme')
        document.documentElement.classList.toggle('dark', e.newValue === 'dark')
    }
    window.addEventListener('storage', onStorage)
    return () => window.removeEventListener('storage', onStorage)
  }, [])

  // Kanban WS — connect unless ?nosock=1
  useEffect(() => {
    if (!location.search.includes('nosock=1')) connect()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Init project store
  useEffect(() => { init() }, [init])

  const currentTitle = viewTitles[currentViewName] || currentViewName

  const handleNavigate = (view: string) => {
    // view is either a path like '/dashboard' or '/projects/:id/kanban'
    navigate(view)
  }

  return (
    <div className="flex h-screen overflow-hidden">
      <SidebarNav currentView={currentViewName} onNavigate={handleNavigate} />

      <div className="flex flex-1 flex-col overflow-hidden">
        <KanbanHeader
          viewTitle={currentTitle}
          viewIcon={LayoutDashboard}
          subtitle={t('app.subtitle')}
          extra={
            (currentViewName === 'dashboard' ||
             currentViewName === 'overview' ||
             currentViewName === 'kanban' ||
             currentViewName === 'execution' ||
             currentViewName === 'observability' ||
             currentViewName === 'artifacts' ||
             currentViewName === 'knowledge' ||
             currentViewName === 'reports' ||
             currentViewName === 'gaps' ||
             currentViewName === 'strategy' ||
             currentViewName === 'chat' ||
             currentViewName === 'terminal' ||
             currentViewName === 'settings')
              ? <ProjectSelector />
              : undefined
          }
        />

        <main className="flex-1 overflow-y-auto">
          <Suspense fallback={<Loading />}>
            <Routes>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<DashboardView />} />

              {/* Project workspace */}
              <Route path="/projects/:id" element={<ProjectOverviewView />} />
              <Route path="/projects/:id/execution" element={<ExecutionView />} />
              <Route path="/projects/:id/observability" element={<ObservabilityView />} />
              <Route path="/projects/:id/artifacts" element={<ArtifactsView />} />
              <Route path="/projects/:id/knowledge" element={<KnowledgeView />} />
              <Route path="/projects/:id/reports" element={<ReportsView />} />
              <Route path="/projects/:id/settings" element={<ProjectSettingsView />} />
              <Route path="/projects/:id/chat" element={<IntelligenceChatView />} />
              <Route path="/projects/:id/gaps" element={<GapDiscoveryView />} />
              <Route path="/projects/:id/strategy" element={<StrategyPlannerView />} />
              <Route path="/projects/:id/kanban" element={<KanbanView />} />
              <Route path="/projects/:id/terminal" element={<AgentTerminalView />} />

              {/* App-level */}
              <Route path="/settings" element={<SettingsView />} />
              <Route path="/onboarding" element={<OnboardingWizardView />} />

              {/* Legacy redirects */}
              <Route path="/workspace/*" element={<Navigate to="/dashboard" replace />} />
              <Route path="/kanban" element={<Navigate to="/dashboard" replace />} />
              <Route path="/gaps" element={<Navigate to="/dashboard" replace />} />
              <Route path="/chat" element={<Navigate to="/dashboard" replace />} />
              <Route path="/execution" element={<Navigate to="/dashboard" replace />} />
              <Route path="/reports" element={<Navigate to="/dashboard" replace />} />
              <Route path="/knowledge" element={<Navigate to="/dashboard" replace />} />
              <Route path="/strategy" element={<Navigate to="/dashboard" replace />} />

              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </Suspense>
        </main>
      </div>

      <Toast />
    </div>
  )
}
