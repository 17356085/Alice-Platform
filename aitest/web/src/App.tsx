/** Root layout — React 18 port. Segmented sidebar + project selector in header.
 *
 * Key difference from Vue: <router-view /> replaced by <Routes>/<Outlet>.
 * No reactive proxy cycle — React's unidirectional data flow breaks the OOM loop.
 */
import { useEffect, useMemo, useState, lazy, Suspense } from 'react'
import { Routes, Route, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { LayoutDashboard } from 'lucide-react'
import SidebarNav from './components/SidebarNav'
import { ErrorBoundary } from './components/ErrorBoundary'
import KanbanHeader from './components/KanbanHeader'
import ProjectSelector from './components/ProjectSelector'
import { Toaster } from './lib/toast'
import { useKanbanWS } from './hooks/useKanbanWS'
import { useProjectStore } from './stores/project'

// ── Lazy views ─────────────────────────────────────────────────
const DashboardView = lazy(() => import('./views/global/ProjectsView'))
const ProjectOverviewView = lazy(() => import('./views/project/overview/OverviewView'))
const ExecutionView = lazy(() => import('./views/project/run/ExecutionView'))
const ObservabilityView = lazy(() => import('./views/cross-cutting/ObservabilityView'))
const ArtifactsView = lazy(() => import('./views/project/assets/ArtifactsView'))
const KnowledgeView = lazy(() => import('./views/project/assets/KnowledgeView'))
const ReportsView = lazy(() => import('./views/project/quality/ReportsView'))
const ProjectSettingsView = lazy(() => import('./views/project/ProjectSettingsView'))
const IntelligenceChatView = lazy(() => import('./views/cross-cutting/IntelligenceChatView'))
const GapDiscoveryView = lazy(() => import('./views/project/quality/GapDiscoveryView'))
const StrategyPlannerView = lazy(() => import('./views/project/build/StrategyPlannerView'))
const BuildView = lazy(() => import('./views/project/build/BuildView'))
const KanbanView = lazy(() => import('./views/project/run/KanbanView'))
const TimelineView = lazy(() => import('./views/project/overview/TimelineView'))
const AgentTerminalView = lazy(() => import('./views/project/assets/AgentTerminalView'))
const SettingsView = lazy(() => import('./views/global/SettingsView'))
const AgentDetailView = lazy(() => import('./views/project/assets/AgentDetailView'))
const KnowledgeGraphView = lazy(() => import('./views/project/assets/KnowledgeGraphView'))
const OnboardingWizardView = lazy(() => import('./views/cross-cutting/OnboardingWizardView'))
const RunInspectorView = lazy(() => import('./views/project/run/RunInspectorView'))

// ── View title mapping ─────────────────────────────────────────
const viewTitles: Record<string, string> = {
  dashboard: '面板', kanban: 'SOP 看板', gaps: '缺口发现',
  chat: '智能对话', execution: '执行监控', terminal: 'Agent 终端',
  reports: '测试报告', knowledge: '知识库', settings: '应用设置',
  onboarding: '新建项目', strategy: '策略规划',
  overview: '项目概览', observability: '可观测性', artifacts: '产物',
  timeline: '时间线', agent: 'Agent 详情', knowledgegraph: '知识图谱',
  runs: '运行记录', projects: '项目', evaluations: '质量评估', registry: '注册中心',
  build: '构建', run: '执行', quality: '质量', assets: '资产',
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
  const { connect, disconnect } = useKanbanWS()
  const init = useProjectStore(s => s.init)
  const currentViewName = useCurrentViewName()
  const [fade, setFade] = useState(true)

  // Page transition: force render → crossfade on route change
  const loc = useLocation()
  useEffect(() => {
    setFade(false)
    // Double rAF ensures browser paints opacity:0 before transitioning to 1
    requestAnimationFrame(() => {
      requestAnimationFrame(() => setFade(true))
    })
  }, [loc.pathname])

  // Theme init — Alice Studio three-character system
  useEffect(() => {
    const savedTheme = localStorage.getItem('tlo-theme-name') || 'alice'
    const theme = savedTheme === 'default' ? 'alice' : savedTheme  // backward compat
    const savedDark = localStorage.getItem('tlo-theme') === 'dark'
    document.documentElement.setAttribute('data-theme', theme)
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
  // MEM-AUDIT: cleanup disconnects on unmount; prevents StrictMode double-connect
  useEffect(() => {
    if (!location.search.includes('nosock=1')) connect()
    return () => disconnect()
  }, [connect, disconnect])

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
             currentViewName === 'timeline' ||
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
             currentViewName === 'runs' ||
             currentViewName === 'settings')
              ? <ProjectSelector />
              : undefined
          }
        />

        <main className={`flex-1 overflow-y-auto page-transition ${fade ? 'show' : ''}`}>
          <ErrorBoundary>
            <Suspense fallback={<Loading />}>
            <Routes>
              <Route path="/" element={<Navigate to="/projects" replace />} />
              <Route path="/dashboard" element={<DashboardView />} />
              <Route path="/projects" element={<DashboardView />} />
              <Route path="/runs" element={<ExecutionView />} />
              <Route path="/evaluations" element={<ReportsView />} />
              <Route path="/registry" element={<SettingsView />} />

              {/* Project resource model */}
              <Route path="/projects/:id" element={<Navigate to="overview" replace />} />
              <Route path="/projects/:id/overview" element={<ProjectOverviewView />} />
              <Route path="/projects/:id/build" element={<BuildView />} />
              <Route path="/projects/:id/build/strategy" element={<StrategyPlannerView />} />
              <Route path="/projects/:id/run" element={<ExecutionView />} />
              <Route path="/projects/:id/run/execute" element={<ExecutionView />} />
              <Route path="/projects/:id/run/kanban" element={<KanbanView />} />
              <Route path="/projects/:id/quality" element={<ReportsView />} />
              <Route path="/projects/:id/quality/reports" element={<ReportsView />} />
              <Route path="/projects/:id/quality/gaps" element={<GapDiscoveryView />} />
              <Route path="/projects/:id/assets" element={<ArtifactsView />} />
              <Route path="/projects/:id/assets/artifacts" element={<ArtifactsView />} />
              <Route path="/projects/:id/assets/knowledge" element={<KnowledgeView />} />
              <Route path="/projects/:id/assets/graph" element={<KnowledgeGraphView />} />
              <Route path="/projects/:id/assets/agents/:agentId" element={<AgentDetailView />} />
              <Route path="/projects/:id/assets/agents/:agentId/terminal" element={<AgentTerminalView />} />

              {/* Legacy project URLs */}
              <Route path="/projects/:id/timeline" element={<TimelineView />} />
              <Route path="/projects/:id/agents/:agentId" element={<AgentDetailView />} />
              <Route path="/projects/:id/knowledgegraph" element={<KnowledgeGraphView />} />
              <Route path="/projects/:id/execution" element={<Navigate to="run/execute" replace />} />
              <Route path="/projects/:id/observability" element={<ObservabilityView />} />
              <Route path="/projects/:id/artifacts" element={<Navigate to="assets/artifacts" replace />} />
              <Route path="/projects/:id/knowledge" element={<Navigate to="assets/knowledge" replace />} />
              <Route path="/projects/:id/reports" element={<Navigate to="quality/reports" replace />} />
              <Route path="/projects/:id/settings" element={<ProjectSettingsView />} />
              <Route path="/projects/:id/chat" element={<IntelligenceChatView />} />
              <Route path="/projects/:id/gaps" element={<Navigate to="quality/gaps" replace />} />
              <Route path="/projects/:id/strategy" element={<Navigate to="build/strategy" replace />} />
              <Route path="/projects/:id/kanban" element={<Navigate to="run/kanban" replace />} />
              <Route path="/projects/:id/terminal" element={<AgentTerminalView />} />
              <Route path="/projects/:id/runs/:runId" element={<RunInspectorView />} />

              {/* App-level */}
              <Route path="/settings" element={<SettingsView />} />
              <Route path="/onboarding" element={<OnboardingWizardView />} />

              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </Suspense>
          </ErrorBoundary>
        </main>
      </div>

      <Toaster />
      <div className="noise-overlay" />
    </div>
  )
}
