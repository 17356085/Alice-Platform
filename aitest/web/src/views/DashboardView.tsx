/** Dashboard view — shadcn/ui edition. Project list + health + KPIs + quick actions. */
import { useState, useEffect, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useProjectStore } from '../stores/project'
import { useKanbanStore } from '../stores/kanban'
import { useHealth } from '../hooks/useHealth'
import { LayoutDashboard, CheckCircle, AlertTriangle, Play, BarChart3, Activity, Search, FileText, Settings2 } from 'lucide-react'
import ProjectSelector from '../components/ProjectSelector'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { useSettingsStore } from '../stores/settings'

const dashHint: Record<string, string> = {
  default:   'Shadow & Memory',
  aoko:      'Speed & Power',
  soujuurou: 'Warmth & Trust',
}

export default function DashboardView() {
  const theme = useSettingsStore(s => s.app.theme)
  const hint = dashHint[theme] || dashHint.default
  const { t } = useTranslation()
  const projects = useProjectStore(s => s.projects)
  const projectLoading = useProjectStore(s => s.loading)
  const hasProjects = useProjectStore(s => s.hasProjects())
  const activeId = useProjectStore(s => s.activeId)
  const fetchProjects = useProjectStore(s => s.fetchProjects)
  const setActive = useProjectStore(s => s.setActive)
  const modules = useKanbanStore(s => s.modules)
  const fetchModules = useKanbanStore(s => s.fetchModules)
  const { health, loading: healthLoading, refresh: refreshHealth } = useHealth()
  const [productKpi, setProductKpi] = useState<any>(null)

  useEffect(() => {
    fetchProjects()
    fetchModules()
    refreshHealth()
    fetch('http://localhost:8000/api/kpi/product')
      .then(r => r.ok ? r.json() : null)
      .then(data => { if (data) setProductKpi(data) })
      .catch(() => { /* offline */ })
  }, [fetchProjects, fetchModules, refreshHealth])

  const stats = useMemo(() => {
    const mods = Object.entries(modules)
    const completed = mods.filter(([, m]) => (m as any).phases_done >= (m as any).phases_total).length
    const withIssues = mods.filter(([, m]) => (m as any).failed > 0).length
    const ready = mods.filter(([, m]) => (m as any).status === 'completed_with_issues' || (m as any).status === 'ready').length
    return { total: mods.length, completed, withIssues, ready }
  }, [modules])

  return (
    <div className="p-6 md:p-8 max-w-[1200px]">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2.5">
          <LayoutDashboard size={24} />
          <h1 className="text-[22px] font-bold m-0">面板</h1>
          <span className="text-[10px] text-muted-foreground/50 tracking-wider uppercase">{hint}</span>
        </div>
        <ProjectSelector />
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        <StatCard icon={BarChart3} value={stats.total} label="总模块" />
        <StatCard icon={CheckCircle} value={stats.completed} label="已完成" color="text-success" />
        <StatCard icon={AlertTriangle} value={stats.withIssues} label="待修复" color="text-warning" />
        <StatCard icon={Play} value={stats.ready} label="就绪" color="text-info" />
      </div>

      {/* Platform Health */}
      <section className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-semibold flex items-center gap-1.5 m-0">
            <Activity size={16} /> 平台状态
          </h2>
          <Button variant="outline" size="sm" onClick={refreshHealth} disabled={healthLoading}>
            刷新
          </Button>
        </div>

        {healthLoading && !health && <p className="text-muted-foreground py-3">加载中...</p>}
        {health && (
          <div className="grid grid-cols-[repeat(auto-fill,minmax(200px,1fr))] gap-3">
            <HealthCard dotColor={health.status === 'healthy' ? 'bg-success' : 'bg-warning'}
              label="整体状态" value={health.status === 'healthy' ? '正常' : '降级'} />
            {health.components.llm && (
              <HealthCard dotColor="bg-success" label="LLM"
                value={health.components.llm.resolved_provider || '?'}
                warn={health.components.llm.circuit_breakers?.open > 0
                  ? `${health.components.llm.circuit_breakers.open} 熔断` : undefined} />
            )}
            {health.components.worker_pool && (
              <HealthCard dotColor={health.components.worker_pool.status === 'healthy' ? 'bg-success' : 'bg-warning'}
                label="Worker Pool"
                value={`活跃 ${health.components.worker_pool.active}/${health.components.worker_pool.max_workers}`} />
            )}
            {health.components.tenants && (
              <HealthCard dotColor="bg-success" label="项目数"
                value={String(health.components.tenants.count)} />
            )}
          </div>
        )}
        {!healthLoading && !health && (
          <p className="text-muted-foreground text-[13px] py-3">
            后端未连接 — 启动 <code className="bg-secondary px-1.5 py-0.5 rounded">aitest server start</code>
          </p>
        )}
      </section>

      {/* Product KPIs */}
      {productKpi && (
        <section className="mb-8">
          <h2 className="text-base font-semibold mb-4">本周产品指标</h2>
          <div className="grid grid-cols-4 gap-3">
            <KpiCard value={productKpi.this_week.runs} label="运行次数"
              delta={productKpi.vs_last_week.runs_delta >= 0 ? `+${productKpi.vs_last_week.runs_delta}` : String(productKpi.vs_last_week.runs_delta)}
              deltaUp={productKpi.vs_last_week.runs_delta >= 0} />
            <KpiCard value={`${Math.round(productKpi.this_week.success_rate * 100)}%`} label="成功率"
              delta={`${productKpi.vs_last_week.success_rate_delta >= 0 ? '+' : ''}${Math.round(productKpi.vs_last_week.success_rate_delta * 100)}%`}
              deltaUp={productKpi.vs_last_week.trend === 'up'} />
            <KpiCard value={`$${productKpi.this_week.total_cost.toFixed(2)}`} label="本周成本"
              delta={productKpi.vs_last_week.cost_delta <= 0 ? '↓' : '↑'}
              deltaUp={productKpi.vs_last_week.cost_delta <= 0} />
            <KpiCard value={productKpi.this_week.agents_used} label="活跃 Agent" />
          </div>
        </section>
      )}

      {/* Project list */}
      <section className="mb-8">
        <h2 className="text-base font-semibold mb-4">项目列表</h2>
        {projectLoading && <p className="text-muted-foreground py-3">加载中...</p>}
        {!projectLoading && !hasProjects && (
          <Card className="text-center py-10 text-muted-foreground">
            <CardContent className="pt-6">
              <p className="mb-4">暂无项目。创建一个新项目开始。</p>
              <Link to="/onboarding">
                <Button variant="gradient">+ 新建项目</Button>
              </Link>
            </CardContent>
          </Card>
        )}
        {!projectLoading && hasProjects && (
          <div className="grid grid-cols-[repeat(auto-fill,minmax(280px,1fr))] gap-3">
            {projects.map(p => (
              <Card
                key={p.id}
                className={cn(
                  'p-4 cursor-pointer border-2 transition-all hover:shadow-md',
                  p.id === activeId && 'border-primary shadow-[var(--primary-glow)]'
                )}
                onClick={() => setActive(p.id)}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="font-semibold">{p.name || p.id}</span>
                  {p.status && <Badge variant={p.status === 'completed' ? 'success' : p.status === 'issues' ? 'warning' : 'secondary'} className="text-[10px]">{p.status}</Badge>}
                </div>
                <div className="flex gap-4 text-xs text-muted-foreground mb-3">
                  <span>模块: {p.modules?.length || 0}</span>
                  {p.updated_at && <span>更新: {p.updated_at.slice(0, 10)}</span>}
                </div>
                <div className="text-right">
                  <Link to="/workspace/kanban" className="text-[13px] text-primary no-underline hover:underline"
                    onClick={e => { e.stopPropagation(); setActive(p.id) }}>
                    进入工作区 →
                  </Link>
                </div>
              </Card>
            ))}
          </div>
        )}
      </section>

      {/* Quick actions */}
      <section>
        <h2 className="text-base font-semibold mb-4">快速操作</h2>
        <div className="grid grid-cols-4 gap-3">
          <QuickAction to="/onboarding" icon={<Search size={24} />} text="发现新项目" />
          <QuickAction to="/workspace/kanban" icon={<Play size={24} />} text="运行 SOP" />
          <QuickAction to="/workspace/reports" icon={<FileText size={24} />} text="查看报告" />
          <QuickAction to="/settings" icon={<Settings2 size={24} />} text="平台设置" />
        </div>
      </section>
    </div>
  )
}

// ── Sub-components ──

function StatCard({ icon: Icon, value, label, color }: {
  icon: any; value: number; label: string; color?: string
}) {
  return (
    <Card className="p-5 text-center">
      <Icon size={20} className={cn('mx-auto mb-2 opacity-70', color)} />
      <div className="text-[28px] font-bold">{value}</div>
      <div className="text-xs text-muted-foreground mt-1">{label}</div>
    </Card>
  )
}

function HealthCard({ dotColor, label, value, warn }: {
  dotColor: string; label: string; value: string; warn?: string
}) {
  return (
    <div className="flex items-center gap-2 p-3 bg-card border border-border rounded-xl">
      <span className={cn('w-2 h-2 rounded-full shrink-0', dotColor)} />
      <span className="text-xs text-muted-foreground min-w-[60px]">{label}</span>
      <span className="text-[13px] font-semibold">{value}</span>
      {warn && <span className="text-[11px] text-destructive bg-destructive-light px-1.5 py-0.5 rounded ml-auto">{warn}</span>}
    </div>
  )
}

function KpiCard({ value, label, delta, deltaUp }: {
  value: string | number; label: string; delta?: string; deltaUp?: boolean
}) {
  return (
    <Card className="p-4 text-center">
      <div className="text-[26px] font-bold">{value}</div>
      <div className="text-[11px] text-muted-foreground mt-1">{label}</div>
      {delta && (
        <div className={cn('text-xs font-semibold mt-1', deltaUp ? 'text-success' : 'text-destructive')}>
          {delta}
        </div>
      )}
    </Card>
  )
}

function QuickAction({ to, icon, text }: { to: string; icon: React.ReactNode; text: string }) {
  return (
    <Link to={to}
      className="flex flex-col items-center gap-2 p-5 bg-card border border-border rounded-xl no-underline text-foreground transition-colors hover:bg-secondary">
      <span className="text-2xl">{icon}</span>
      <span className="text-[13px] font-medium">{text}</span>
    </Link>
  )
}
