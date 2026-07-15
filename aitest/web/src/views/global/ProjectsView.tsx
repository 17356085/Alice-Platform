import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Activity, Bot, CheckCircle2, Clock3, GitBranch, Gauge,
  Layers3, Network, Play, Search, ShieldCheck, TerminalSquare, Zap,
} from 'lucide-react'
import { useProjectStore } from '../../stores/project'
import { useHealth } from '../../hooks/useHealth'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { PageHeader, StatCard, AgentCard, ErrorState, LoadingState, type Agent } from '@/components/shared'

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
  const { health, loading: healthLoading, error: healthError, refresh } = useHealth()

  useEffect(() => { init() }, [init])

  const projectPath = activeId ? `/projects/${activeId}` : '/projects'

  return (
    <div className="min-h-full space-y-6 bg-background p-4 sm:p-6 lg:p-8">
      <PageHeader
        eyebrow="Alice / Workspace"
        title="项目工作台"
        description="从 Agent 状态、最近执行和系统健康开始定位下一步工作。"
        actions={<Button onClick={() => navigate(`${projectPath}/run`)}><Play data-icon="inline-start" fill="currentColor" />新建运行</Button>}
      />

      <div className="relative max-w-xl">
        <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" aria-hidden="true" />
        <Input className="pl-9" placeholder="搜索 Agent、Run、Memory…" aria-label="搜索工作台内容" />
      </div>

      <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="活跃 Agent" value="3 / 6" detail="3 个工作流正在运行" icon={Bot} tone="info" />
        <StatCard label="今日工作流" value="14" detail="较昨日增加 3 个" icon={GitBranch} tone="primary" />
        <StatCard label="成功率" value="94.2%" detail="最近 30 天" icon={CheckCircle2} tone="success" />
        <StatCard label="Memory 节点" value="1,284" detail="本次运行更新 48 个" icon={Zap} tone="neutral" />
      </section>

      <button className="flex w-full flex-wrap items-center gap-3 rounded-lg border border-info/20 bg-info/5 px-4 py-3 text-left text-sm transition-colors hover:bg-info/10" onClick={() => navigate(`${projectPath}/run`)}>
        <span className="size-2 rounded-full bg-info" aria-hidden="true" />
        <span className="font-medium text-info">有运行正在进行</span>
        <span className="font-mono text-xs text-muted-foreground">workflow-9f2a3b</span>
        <span className="ml-auto flex items-center gap-3 text-xs text-muted-foreground"><span className="inline-flex items-center gap-1"><Clock3 className="size-3" />7.8 秒</span><span className="inline-flex items-center gap-1"><Activity className="size-3" />3 个 Agent</span></span>
      </button>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_20rem]">
        <section>
          <div className="mb-3 flex items-center justify-between gap-3"><h2 className="text-sm font-semibold text-foreground">Agent Registry</h2><span className="text-xs text-muted-foreground">6 个 Agent</span></div>
          <div className="grid gap-3 md:grid-cols-2 2xl:grid-cols-3">
            {agents.map(agent => (
              <AgentCard
                key={agent.name}
                agent={agent}
                onClick={() => navigate(`${projectPath}/assets/agents/${agent.name.toLowerCase().replaceAll(' ', '-')}`)}
              />
            ))}
          </div>
        </section>

        <aside className="flex flex-col gap-6">
          <div>
            <div className="mb-3 flex items-center justify-between gap-3"><h2 className="text-sm font-semibold text-foreground">最近运行</h2><Button variant="ghost" size="sm" onClick={() => navigate('/runs')}>查看全部</Button></div>
            <Card><CardContent className="divide-y divide-border p-0">
              {recentRuns.map(([id, meta, tests, tone]) => <button className="flex w-full items-center gap-3 px-4 py-3 text-left transition-colors hover:bg-accent" key={id} onClick={() => navigate('/runs')}><span className={`size-2 shrink-0 rounded-full ${tone === 'green' ? 'bg-success' : tone === 'yellow' ? 'bg-warning' : 'bg-destructive'}`} /><span className="flex min-w-0 flex-1 flex-col gap-1"><b className="truncate font-mono text-xs font-medium text-foreground">{id}</b><small className="text-xs text-muted-foreground">{meta}</small></span><strong className="font-mono text-xs text-foreground">{tests}</strong></button>)}
            </CardContent></Card>
          </div>
          <div>
            <div className="mb-3 flex items-center justify-between gap-3"><h2 className="text-sm font-semibold text-foreground">系统状态</h2><Button variant="ghost" size="sm" onClick={() => void refresh()} disabled={healthLoading}>刷新</Button></div>
            {healthError ? <ErrorState message={healthError} action={<Button variant="outline" size="sm" onClick={() => void refresh()}>重试</Button>} /> : healthLoading && !health ? <LoadingState rows={4} /> : <Card><CardHeader className="pb-2"><CardTitle className="text-sm">服务健康</CardTitle></CardHeader><CardContent className="flex flex-col gap-3"><HealthRow label="API Gateway" value={health?.status === 'degraded' ? 'Degraded' : 'Healthy'} tone={health?.status === 'degraded' ? 'warning' : 'success'} /><HealthRow label="Memory Store" value="2.1 GB" tone="info" /><HealthRow label="Task Queue" value="4 pending" tone="warning" /><HealthRow label="Model API" value="&lt; 200ms" tone="success" /></CardContent></Card>}
          </div>
        </aside>
      </div>
    </div>
  )
}

function HealthRow({ label, value, tone }: { label: string; value: string; tone: 'success' | 'info' | 'warning' }) {
  const dotClass = { success: 'bg-success', info: 'bg-info', warning: 'bg-warning' }[tone]
  return <div className="flex items-center justify-between gap-3 border-b border-border/70 pb-3 text-sm last:border-0 last:pb-0"><span className="flex items-center gap-2 text-muted-foreground"><span className={`size-2 rounded-full ${dotClass}`} />{label}</span><b className="font-mono text-xs font-medium text-foreground">{value}</b></div>
}
