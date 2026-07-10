/** Dashboard — Hero stats + compact health + secondary projects.
 *  Apple single-focus: Stats dominate, everything else recedes.
 */
import { useState, useEffect, useMemo } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useProjectStore } from '../stores/project'
import { useKanbanStore } from '../stores/kanban'
import { useHealth } from '../hooks/useHealth'
import { LayoutDashboard, CheckCircle, AlertTriangle, Play, BarChart3, Activity, Clock, Plus, FolderOpen, ArrowRight } from 'lucide-react'
import ProjectSelector from '../components/ProjectSelector'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { cn } from '@/lib/utils'
import { useSettingsStore } from '../stores/settings'
import { useTimelineStore } from '../stores/timeline'
import { api } from '../api/client'

export default function DashboardView() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const projects = useProjectStore(s => s.projects)
  const projectLoading = useProjectStore(s => s.loading)
  const hasProjects = useProjectStore(s => s.hasProjects())
  const activeId = useProjectStore(s => s.activeId)
  const fetchProjects = useProjectStore(s => s.fetchProjects)
  const setActive = useProjectStore(s => s.setActive)
  const modules = useKanbanStore(s => s.modules)
  const fetchModules = useKanbanStore(s => s.fetchModules)
  const { health, loading: healthLoading, refresh: refreshHealth } = useHealth()
  const [productKpi, setProductKpi] = useState<{ this_week?: { runs?: number; pass_rate?: number; success_rate?: number; avg_duration_s?: number; total_cost?: number }; last_week?: { runs?: number; pass_rate?: number; success_rate?: number; avg_duration_s?: number; total_cost?: number } } | null>(null)
  const [kpiError, setKpiError] = useState(false)
  const recentEvents = useTimelineStore(s => s.recent)(5)

  useEffect(() => {
    fetchProjects()
    fetchModules()
    refreshHealth()
    api.get('/api/v1/kpi/product')
      .then(data => { if (data) { setProductKpi(data); setKpiError(false) } })
      .catch(() => setKpiError(true))
  }, [fetchProjects, fetchModules, refreshHealth])

  const stats = useMemo(() => {
    const mods = Object.entries(modules)
    const completed = mods.filter(([, m]) => m.phases_done >= m.phases_total).length
    const withIssues = mods.filter(([, m]) => m.failed > 0).length
    const ready = mods.filter(([, m]) => m.status === 'completed_with_issues' || m.status === 'ready').length
    return { total: mods.length, completed, withIssues, ready }
  }, [modules])

  return (
    <div className="p-6 md:p-8 max-w-[1200px]">
      {/* ── Top bar: title + health + project selector ── */}
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-3">
          <h1 className="text-[22px] font-bold m-0">面板</h1>
          {/* Compact health inline */}
          {health && (
            <div className="flex items-center gap-3 ml-4 pl-4 border-l border-border">
              <HealthDot status={health.status} />
              <span className="text-xs text-muted-foreground">
                {health.status === 'healthy' ? '系统正常' : '系统降级'}
              </span>
              {health.components?.llm && (
                <span className="text-[11px] text-muted-foreground/60">
                  {String((health.components.llm as Record<string, unknown>).resolved_provider) || '?'}
                  {(((health.components.llm as Record<string, unknown>).circuit_breakers as { open?: number } | undefined)?.open ?? 0) > 0 && (
                    <span className="text-destructive ml-1">{((health.components.llm as Record<string, unknown>).circuit_breakers as { open: number }).open} 熔断</span>
                  )}
                </span>
              )}
              {health.components?.ecosystem && (
                <span className="text-[11px] text-muted-foreground/60">
                  {((health.components.ecosystem as Record<string, unknown>).project_count as number | undefined) || 0} 项目 / {((health.components.ecosystem as Record<string, unknown>).discovery_strategy_count as number | undefined) || 0} 策略
                  {String((health.components.ecosystem as Record<string, unknown>).status) && String((health.components.ecosystem as Record<string, unknown>).status) !== 'healthy' && (
                    <span className="text-warning ml-1">{String((health.components.ecosystem as Record<string, unknown>).status)}</span>
                  )}
                </span>
              )}
            </div>
          )}
          {healthLoading && <span className="text-xs text-muted-foreground ml-4">检查中...</span>}
          {!health && !healthLoading && (
            <span className="text-xs text-muted-foreground ml-4">
              后端未连接 — <code className="bg-secondary px-1 py-0.5 rounded text-[11px]">aitest server start</code>
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="sm" onClick={refreshHealth} disabled={healthLoading}
            className="text-xs text-muted-foreground">
            <Activity size={14} className="mr-1" /> 刷新
          </Button>
          <ProjectSelector />
        </div>
      </div>

      {/* ═══ HERO: Stats — single focal point ═══ */}
      <section className="mb-10">
        <div className="grid grid-cols-4 gap-6">
          <HeroStat value={stats.total} label="总模块" color="text-foreground"
            onClick={() => hasProjects && activeId && navigate(`/projects/${activeId}/kanban`)} />
          <HeroStat value={stats.completed} label="已完成" color="text-success"
            onClick={() => hasProjects && activeId && navigate(`/projects/${activeId}/reports`)} />
          <HeroStat value={stats.ready} label="就绪" color="text-info"
            onClick={() => hasProjects && activeId && navigate(`/projects/${activeId}/execution`)} />
          <HeroStat value={stats.withIssues} label="待修复" color="text-warning"
            onClick={() => hasProjects && activeId && navigate(`/projects/${activeId}/gaps`)} />
        </div>
        {/* Overall progress bar */}
        {stats.total > 0 && (
          <div className="mt-4 flex items-center gap-3">
            <Progress value={stats.total ? Math.round(stats.completed / Math.max(stats.total, 1) * 100) : 0}
              className="h-1.5 flex-1" />
            <span className="text-[11px] text-muted-foreground tabular-nums">
              {stats.completed}/{stats.total} 模块完成
            </span>
          </div>
        )}
      </section>

      {/* ═══ Secondary: Projects + Activity side by side ═══ */}
      <div className="grid grid-cols-[2fr_1fr] gap-8">
        {/* Project list — secondary, compact */}
        <section>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">项目</h2>
            <Link to="/onboarding">
              <Button variant="ghost" size="sm" className="text-xs gap-1 text-muted-foreground">
                <Plus size={13} /> 新建
              </Button>
            </Link>
          </div>

          {projectLoading && <p className="text-xs text-muted-foreground py-8 text-center">加载中...</p>}

          {!projectLoading && !hasProjects && (
            <Card className="text-center py-12">
              <CardContent>
                <FolderOpen size={40} className="mx-auto mb-3 opacity-15" />
                <p className="text-sm text-muted-foreground mb-4">暂无项目。导入被测系统开始。</p>
                <Link to="/onboarding">
                  <Button variant="gradient">创建第一个项目</Button>
                </Link>
              </CardContent>
            </Card>
          )}

          {!projectLoading && hasProjects && (
            <div className="space-y-1">
              {projects.slice(0, 5).map(p => (
                <button
                  key={p.id}
                  onClick={() => { setActive(p.id); navigate(`/projects/${p.id}/kanban`) }}
                  className={cn(
                    'w-full flex items-center gap-4 px-3 py-2.5 rounded-lg text-left transition-colors hover:bg-accent/50',
                    p.id === activeId && 'bg-accent/70'
                  )}
                >
                  <span className="font-medium text-sm flex-1 truncate">{p.name || p.id}</span>
                  <span className="text-[11px] text-muted-foreground tabular-nums">
                    {p.modules?.length || 0} 模块
                  </span>
                  {p.status && (
                    <Badge variant={p.status === 'completed' ? 'success' : 'secondary'} className="text-[10px]">
                      {p.status}
                    </Badge>
                  )}
                  <ArrowRight size={14} className="text-muted-foreground/30" />
                </button>
              ))}
              {projects.length > 5 && (
                <p className="text-[11px] text-muted-foreground text-center pt-2">
                  +{projects.length - 5} 个项目 — 选择活跃项目查看
                </p>
              )}
            </div>
          )}
        </section>

        {/* Activity feed — compact sidebar */}
        <section>
          <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-3">最近活动</h2>
          {recentEvents.length === 0 ? (
            <p className="text-xs text-muted-foreground py-8 text-center">暂无活动</p>
          ) : (
            <div className="space-y-2">
              {recentEvents.map(event => (
                <div key={event.id}
                  className="flex items-start gap-2 text-xs cursor-pointer hover:bg-accent/40 rounded-md px-2 py-1.5 -mx-2 transition-colors"
                  onClick={() => activeId && navigate(`/projects/${activeId}/timeline`)}
                >
                  <span className="text-[11px] font-mono text-muted-foreground mt-px tabular-nums shrink-0 w-10">
                    {new Date(event.ts).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}
                  </span>
                  <span className="shrink-0">{event.icon}</span>
                  <span className="truncate text-muted-foreground">{event.message}</span>
                </div>
              ))}
            </div>
          )}

          {/* KPI summary — if available */}
          {productKpi && productKpi.this_week && (
            <div className="mt-4 pt-4 border-t border-border">
              <div className="grid grid-cols-2 gap-2">
                <div className="text-center p-2 rounded-lg bg-muted/30">
                  <div className="text-lg font-bold tabular-nums">{Math.round((productKpi.this_week.success_rate ?? 0) * 100)}%</div>
                  <div className="text-[10px] text-muted-foreground">成功率</div>
                </div>
                <div className="text-center p-2 rounded-lg bg-muted/30">
                  <div className="text-lg font-bold tabular-nums">${(productKpi.this_week.total_cost ?? 0).toFixed(0)}</div>
                  <div className="text-[10px] text-muted-foreground">本周成本</div>
                </div>
              </div>
            </div>
          )}

          {kpiError && (
            <div className="mt-4 text-center">
              <button onClick={() => {
                setKpiError(false)
                api.get('/api/v1/kpi/product')
                  .then(data => { if (data) { setProductKpi(data); setKpiError(false) } })
                  .catch(() => setKpiError(true))
              }}
                className="text-[11px] text-muted-foreground hover:text-foreground transition-colors"
              >
                KPI 加载失败 — 点击重试
              </button>
            </div>
          )}
        </section>
      </div>
    </div>
  )
}

// ── Hero stat block ──
function HeroStat({ value, label, color, onClick }: {
  value: number; label: string; color: string; onClick?: () => void
}) {
  return (
    <div
      onClick={onClick}
      className={cn(
        'text-center py-8 px-4 rounded-2xl transition-colors',
        onClick && 'cursor-pointer hover:bg-accent/30',
        'bg-card/40 border border-border/50'
      )}
    >
      <div className={cn('text-[42px] font-bold leading-none tabular-nums', color)}>
        {value}
      </div>
      <div className="text-[13px] text-muted-foreground mt-2 font-medium">{label}</div>
    </div>
  )
}

function HealthDot({ status }: { status: string }) {
  return (
    <span className={cn(
      'w-2 h-2 rounded-full shrink-0',
      status === 'healthy' ? 'bg-success' : 'bg-warning'
    )} />
  )
}
