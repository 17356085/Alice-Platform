import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Activity, Bot, CheckCircle2, Clock3, GitBranch, Gauge,
  Layers3, Network, Play, Search, ShieldCheck, TerminalSquare, Zap,
} from 'lucide-react'
import { useProjectStore } from '../../stores/project'
import { useHealth } from '../../hooks/useHealth'
import { StatCard, AgentCard, type Agent } from '@/components/shared'

const agents: Agent[] = [
  { name: 'Alice-Core', kind: 'Orchestrator', description: 'Coordinates multi-agent test workflows and manages execution across all sub-systems.', status: 'running', score: '98.2%', runs: '1,847 runs', tools: ['TestRunner', 'BrowserDriver', 'APIClient', '+1'], icon: Network },
  { name: 'Test Runner', kind: 'Execution', description: 'Executes unit and integration tests. Parses results and surfaces failures with full context.', status: 'running', score: '96.4%', runs: '3,241 runs', tools: ['Jest', 'Playwright', 'Vitest', '+1'], icon: TerminalSquare },
  { name: 'Browser Driver', kind: 'Execution', description: 'Controls headless browser sessions for E2E testing and visual regression baselines.', status: 'running', score: '91.7%', runs: '2,108 runs', tools: ['Playwright', 'Screenshot', 'NetworkInterceptor', '+1'], icon: Bot },
  { name: 'API Validator', kind: 'Validation', description: 'Validates REST and GraphQL API contracts. Auto-generates test cases from OpenAPI specifications.', status: 'success', score: '99.1%', runs: '4,520 runs', tools: ['OpenAPI', 'HTTPClient', 'SchemaValidator', '+1'], icon: ShieldCheck },
  { name: 'Report Generator', kind: 'Analysis', description: 'Synthesizes test execution results into structured reports and identifies regression patterns.', status: 'idle', score: '100%', runs: '892 runs', tools: ['Markdown', 'Chart', 'Email', '+1'], icon: Layers3 },
  { name: 'Scheduler', kind: 'Infrastructure', description: 'Manages execution schedules, trigger queues, and workflow dispatch with priority handling.', status: 'idle', score: '97.8%', runs: '6,103 runs', tools: ['CronJob', 'Queue', 'Webhook', '+1'], icon: Clock3 },
]

const recentRuns = [
  ['run-a8f2c4', '2m ago · 3.2s', '12/12', 'green'],
  ['run-e91b83', '14m ago · 4.8s', '7/8', 'yellow'],
  ['run-7d3f91', '1h ago · 2.9s', '12/12', 'green'],
  ['run-6c2a45', '2h ago · 1.2s', '3/12', 'red'],
  ['run-5be72', '3h ago · 3.5s', '12/12', 'green'],
] as const

export default function DashboardView() {
  const navigate = useNavigate()
  const init = useProjectStore(s => s.init)
  const activeId = useProjectStore(s => s.activeId)
  const { health } = useHealth()

  useEffect(() => { init() }, [init])

  const projectPath = activeId ? `/projects/${activeId}` : '/projects'

  return (
    <div className="alice-dashboard min-h-full p-6 lg:p-8">
      <div className="alice-page-head">
        <div>
          <p className="alice-eyebrow">Alice <span>/</span> Dashboard</p>
          <h1>Good evening, operator.</h1>
          <p className="alice-subtitle">Your agent orchestration workspace is ready.</p>
        </div>
        <button className="alice-primary-button" onClick={() => navigate(`${projectPath}/run`)}>
          <Play size={14} fill="currentColor" /> New run
        </button>
      </div>

      <div className="alice-search"><Search size={15} /><span>Search agents, runs, memories...</span><kbd>⌘ K</kbd></div>

      <section className="alice-stat-grid">
        <StatCard label="ACTIVE AGENTS" value="3 / 6" detail="3 running workflows" icon={Bot} tone="cyan" />
        <StatCard label="WORKFLOWS TODAY" value="14" detail="↑ 3 from yesterday" icon={GitBranch} tone="blue" />
        <StatCard label="SUCCESS RATE" value="94.2%" detail="Last 30 days" icon={CheckCircle2} tone="green" />
        <StatCard label="MEMORY NODES" value="1,284" detail="48 updated this run" icon={Zap} tone="violet" />
      </section>

      <button className="alice-running-banner" onClick={() => navigate(`${projectPath}/run`)}>
        <span className="alice-live-dot" />
        <span className="alice-running-label">Execution in progress</span>
        <span className="alice-mono">workflow-9f2a3b</span>
        <span className="alice-banner-spacer" />
        <span><Clock3 size={12} /> Running for 7.8s</span>
        <span><Activity size={12} /> 3 agents active</span>
      </button>

      <div className="alice-content-grid">
        <section>
          <div className="alice-section-head"><h2>Agent Registry</h2><span>6 agents</span></div>
          <div className="alice-agent-grid">
            {agents.map(agent => (
              <AgentCard
                key={agent.name}
                agent={agent}
                onClick={() => navigate(`${projectPath}/assets/agents/${agent.name.toLowerCase().replaceAll(' ', '-')}`)}
              />
            ))}
          </div>
        </section>

        <aside className="alice-side-stack">
          <div>
            <div className="alice-section-head"><h2>Recent Runs</h2><button onClick={() => navigate('/runs')}>View all</button></div>
            <div className="alice-panel">
              {recentRuns.map(([id, meta, tests, tone]) => <button className="alice-run-row" key={id} onClick={() => navigate('/runs')}><i className={`alice-run-dot ${tone}`} /><span><b>{id}</b><small>{meta}</small></span><strong className={tone}>{tests}</strong><small>tests</small></button>)}
            </div>
          </div>
          <div>
            <div className="alice-section-head"><h2>System</h2></div>
            <div className="alice-panel alice-health-panel">
              <HealthRow label="API Gateway" value={health?.status === 'degraded' ? 'Degraded' : 'Healthy'} tone={health?.status === 'degraded' ? 'yellow' : 'green'} />
              <HealthRow label="Memory Store" value="2.1 GB" tone="cyan" />
              <HealthRow label="Task Queue" value="4 pending" tone="yellow" />
              <HealthRow label="Model API" value="< 200ms" tone="green" />
            </div>
          </div>
        </aside>
      </div>
    </div>
  )
}

function HealthRow({ label, value, tone }: { label: string; value: string; tone: string }) {
  return <div className="alice-health-row"><span><i className={`alice-run-dot ${tone}`} />{label}</span><b>{value}</b></div>
}
