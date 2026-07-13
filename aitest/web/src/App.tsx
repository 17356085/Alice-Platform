/**
 * Backend-connected Studio shell.
 *
 * Project selection, read models and interaction APIs are wired through the
 * shared API client; pages render explicit empty states when the backend has
 * no data instead of inventing sample records.
 */
import { Route, Routes } from 'react-router-dom'
import DesignStudioApp from './DesignStudioApp'
import IntelligenceChatView from './views/cross-cutting/IntelligenceChatView'
import ObservabilityView from './views/cross-cutting/ObservabilityView'
import OnboardingWizardView from './views/cross-cutting/OnboardingWizardView'
import EvaluationsView from './views/global/EvaluationsView'
import GlobalRunsView from './views/global/GlobalRunsView'
import ProjectsView from './views/global/ProjectsView'
import RegistryView from './views/global/RegistryView'
import SettingsView from './views/global/SettingsView'
import AgentDetailView from './views/project/assets/AgentDetailView'
import AgentTerminalView from './views/project/assets/AgentTerminalView'
import ArtifactsView from './views/project/assets/ArtifactsView'
import KnowledgeGraphView from './views/project/assets/KnowledgeGraphView'
import KnowledgeView from './views/project/assets/KnowledgeView'
import ProjectSettingsView from './views/project/ProjectSettingsView'
import BuildView from './views/project/build/BuildView'
import StrategyPlannerView from './views/project/build/StrategyPlannerView'
import ProjectOverviewView from './views/project/overview/OverviewView'
import TimelineView from './views/project/overview/TimelineView'
import GapDiscoveryView from './views/project/quality/GapDiscoveryView'
import ReportsView from './views/project/quality/ReportsView'
import ExecutionView from './views/project/run/ExecutionView'
import KanbanView from './views/project/run/KanbanView'
import RunInspectorView from './views/project/run/RunInspectorView'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<DesignStudioApp />} />
      <Route path="/projects" element={<ProjectsView />} />
      <Route path="/projects/:id" element={<ProjectOverviewView />} />
      <Route path="/projects/:id/settings" element={<ProjectSettingsView />} />
      <Route path="/projects/:id/timeline" element={<TimelineView />} />
      <Route path="/projects/:id/run" element={<ExecutionView />} />
      <Route path="/projects/:id/kanban" element={<KanbanView />} />
      <Route path="/projects/:id/runs/:runId" element={<RunInspectorView />} />
      <Route path="/projects/:id/gaps" element={<GapDiscoveryView />} />
      <Route path="/projects/:id/reports" element={<ReportsView />} />
      <Route path="/projects/:id/build" element={<BuildView />} />
      <Route path="/projects/:id/strategy" element={<StrategyPlannerView />} />
      <Route path="/projects/:id/knowledge" element={<KnowledgeView />} />
      <Route path="/projects/:id/graph" element={<KnowledgeGraphView />} />
      <Route path="/projects/:id/artifacts" element={<ArtifactsView />} />
      <Route path="/projects/:id/assets/agents/:agentId" element={<AgentDetailView />} />
      <Route path="/projects/:id/assets/agents/:agentId/terminal" element={<AgentTerminalView />} />
      <Route path="/runs" element={<GlobalRunsView />} />
      <Route path="/evaluations" element={<EvaluationsView />} />
      <Route path="/registry" element={<RegistryView />} />
      <Route path="/settings" element={<SettingsView />} />
      <Route path="/chat" element={<IntelligenceChatView />} />
      <Route path="/observability" element={<ObservabilityView />} />
      <Route path="/onboarding" element={<OnboardingWizardView />} />
      <Route path="*" element={<DesignStudioApp />} />
    </Routes>
  )
}
