/** Agent Detail — profile, metrics, run history. */
import { useMemo } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Bot, Zap, CheckCircle, XCircle, Clock, DollarSign, Activity, ArrowRight } from 'lucide-react'
import { useKanbanStore } from '@/stores/kanban'
import { useTimelineStore } from '@/stores/timeline'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge, type BadgeVariant } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { Separator } from '@/components/ui/separator'
import { cn } from '@/lib/utils'

const AGENT_META: Record<string, { label: string; desc: string; caps: string[] }> = {
  'project-agent':       { label: 'Project Agent',      desc: 'Initializes project context and validates module structure.', caps: ['Context','Validation'] },
  'requirement-agent':   { label: 'Requirement Agent',  desc: 'Analyzes business requirements and generates test scenarios.', caps: ['Analysis','Planning'] },
  'test-design-agent':   { label: 'Test Design Agent',  desc: 'Designs page objects, locators, and test case structures.', caps: ['Design','Locators'] },
  'automation-agent':    { label: 'Automation Agent',   desc: 'Generates Page Object code and test scripts.', caps: ['Codegen','Selenium'] },
  'execution-agent':     { label: 'Execution Agent',    desc: 'Runs test suites and collects evidence.', caps: ['Runner','Evidence'] },
  'bug-analysis-agent':  { label: 'Bug Analysis Agent', desc: 'Analyzes test failures and classifies root causes.', caps: ['Analysis','Debug'] },
  'report-agent':        { label: 'Report Agent',       desc: 'Generates Excel reports and KPI summaries.', caps: ['Reporting','Excel'] },
  'knowledge-agent':     { label: 'Knowledge Agent',    desc: 'Updates ChromaDB with new patterns and known issues.', caps: ['RAG','Memory'] },
  'data-sanitization':   { label: 'Sanitization Agent', desc: 'Cleans test data and anonymizes sensitive fields.', caps: ['Data','Privacy'] },
}

const agentColor: Record<string, string> = {
  'project-agent': 'info', 'requirement-agent': 'info', 'test-design-agent': 'warning',
  'automation-agent': 'gold', 'execution-agent': 'success', 'bug-analysis-agent': 'destructive',
  'report-agent': 'info', 'knowledge-agent': 'gold', 'data-sanitization': 'secondary',
}

export default function AgentDetailView() {
  const { id: pid, agentId } = useParams<{ id: string; agentId: string }>()
  const agent = agentId || 'automation-agent'
  const meta = AGENT_META[agent] || { label: agent, desc: 'Agent profile unavailable.', caps: [] }
  const modules = useKanbanStore(s => s.modules)
  const events = useTimelineStore(s => s.events)

  const agentEvents = useMemo(() =>
    events.filter(e => e.agent === agent || e.message.includes(agent)),
    [events, agent]
  )

  const stats = useMemo(() => {
    const completed = agentEvents.filter(e => e.type === 'phase_complete').length
    const failed = agentEvents.filter(e => e.type === 'error').length
    const totalTokens = agentEvents.reduce((s, e) => s + (e.tokensIn || 0) + (e.tokensOut || 0), 0)
    const totalCost = agentEvents.reduce((s, e) => s + (e.cost || 0), 0)
    const avgDuration = agentEvents.filter(e => e.duration).length > 0
      ? agentEvents.filter(e => e.duration).reduce((s, e) => s + (e.duration || 0), 0) / agentEvents.filter(e => e.duration).length
      : 0
    return { completed, failed, total: completed + failed, totalTokens, totalCost, avgDuration }
  }, [agentEvents])

  const successRate = stats.total > 0 ? Math.round(stats.completed / stats.total * 100) : 0

  return (
    <div className="p-6 max-w-[1000px]">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className={cn('w-10 h-10 rounded-xl flex items-center justify-center',
          `bg-${agentColor[agent] || 'secondary'}`)}>
          <Bot size={20} className="text-white" />
        </div>
        <div>
          <h1 className="text-xl font-bold">{meta.label}</h1>
          <p className="text-xs text-muted-foreground">{meta.desc}</p>
        </div>
        <div className="flex-1" />
        <Link to={`/projects/${pid || 'default'}/timeline`}>
          <Button variant="outline" size="sm" className="gap-1 text-xs">
            <Clock size={13} /> 查看时间线
          </Button>
        </Link>
      </div>

      {/* Capability tags */}
      <div className="flex gap-1.5 mb-6">
        {meta.caps.map(c => (
          <Badge key={c} variant={(agentColor[agent] as BadgeVariant) || 'secondary'} className="text-[10px]">{c}</Badge>
        ))}
      </div>

      {/* Metrics grid */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <MetricCard icon={CheckCircle} value={`${successRate}%`} label="成功率" color="text-success" />
        <MetricCard icon={Activity} value={stats.total} label="执行次数" color="text-info" />
        <MetricCard icon={Zap} value={(stats.totalTokens).toLocaleString()} label="Tokens" color="text-warning" />
        <MetricCard icon={DollarSign} value={`$${stats.totalCost.toFixed(2)}`} label="成本" color="text-gold" />
      </div>

      {/* Run history + performance */}
      <div className="grid grid-cols-2 gap-6">
        {/* Recent runs */}
        <Card>
          <CardHeader><CardTitle className="text-sm">最近执行</CardTitle></CardHeader>
          <CardContent>
            {agentEvents.length === 0 ? (
              <p className="text-xs text-muted-foreground text-center py-8">暂无执行记录</p>
            ) : (
              <div className="space-y-2">
                {agentEvents.slice(0, 10).map(e => (
                  <div key={e.id} className="flex items-center gap-3 text-xs p-1.5 rounded hover:bg-accent/30">
                    <Badge variant={e.type === 'error' ? 'destructive' : e.type === 'phase_complete' ? 'success' : 'secondary'}
                      className="text-[9px] shrink-0">{e.icon}</Badge>
                    <span className="flex-1 truncate">{e.message}</span>
                    <span className="text-muted-foreground font-mono tabular-nums shrink-0">
                      {new Date(e.ts).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Performance chart */}
        <Card>
          <CardHeader><CardTitle className="text-sm">性能指标</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-muted-foreground">成功率</span>
                <span className="font-mono">{successRate}%</span>
              </div>
              <Progress value={successRate} className="h-1.5" />
            </div>
            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-muted-foreground">平均耗时</span>
                <span className="font-mono">{stats.avgDuration.toFixed(1)}s</span>
              </div>
              <Progress value={Math.min(stats.avgDuration * 20, 100)} className="h-1.5 [&>div]:bg-warning" />
            </div>
            <Separator />
            <div className="grid grid-cols-2 gap-3 text-center text-xs">
              <div>
                <div className="text-lg font-bold font-mono text-success">{stats.completed}</div>
                <div className="text-muted-foreground">成功</div>
              </div>
              <div>
                <div className="text-lg font-bold font-mono text-destructive">{stats.failed}</div>
                <div className="text-muted-foreground">失败</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

function MetricCard({ icon: Icon, value, label, color }: {
  icon: React.ComponentType<{ className?: string }>; value: string | number; label: string; color: string
}) {
  return (
    <Card className="p-4 text-center">
      <Icon size={18} className={cn('mx-auto mb-2 opacity-60', color)} />
      <div className="text-2xl font-bold tabular-nums">{value}</div>
      <div className="text-[11px] text-muted-foreground mt-1">{label}</div>
    </Card>
  )
}
