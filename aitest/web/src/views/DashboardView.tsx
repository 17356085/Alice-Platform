/** Dashboard view — React port. Project list + health + KPIs + quick actions.
 *  Vue computed → React useMemo. Vue router-link → React Router Link.
 */
import { useState, useEffect, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useProjectStore } from '../stores/project'
import { useKanbanStore } from '../stores/kanban'
import { useHealth } from '../hooks/useHealth'
import { LayoutDashboard, CheckCircle, AlertTriangle, Play, BarChart3, Activity } from 'lucide-react'
import ProjectSelector from '../components/ProjectSelector'

export default function DashboardView() {
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
    <div className="dashboard">
      {/* Header */}
      <div className="dashboard-header">
        <div className="header-left">
          <LayoutDashboard size={24} />
          <h1>面板</h1>
        </div>
        <ProjectSelector />
      </div>

      {/* Stats cards */}
      <div className="stats-grid">
        <StatCard icon={BarChart3} value={stats.total} label="总模块" />
        <StatCard icon={CheckCircle} value={stats.completed} label="已完成" color="green" />
        <StatCard icon={AlertTriangle} value={stats.withIssues} label="待修复" color="yellow" />
        <StatCard icon={Play} value={stats.ready} label="就绪" color="blue" />
      </div>

      {/* Platform Health */}
      <div className="section">
        <div className="section-header">
          <h2><Activity size={16} /> 平台状态</h2>
          <button className="btn-refresh" onClick={refreshHealth} disabled={healthLoading}>刷新</button>
        </div>
        {healthLoading && !health && <div className="loading">加载中...</div>}
        {health && (
          <div className="health-grid">
            <div className="health-card">
              <span className={`health-dot ${health.status}`} />
              <span className="health-label">整体状态</span>
              <span className="health-value">{health.status === 'healthy' ? '正常' : '降级'}</span>
            </div>
            {health.components.llm && (
              <div className="health-card">
                <span className="health-dot ok" />
                <span className="health-label">LLM</span>
                <span className="health-value">{health.components.llm.resolved_provider || '?'}</span>
                {health.components.llm.circuit_breakers?.open > 0 && (
                  <span className="health-warn">{health.components.llm.circuit_breakers.open} 熔断</span>
                )}
              </div>
            )}
            {health.components.worker_pool && (
              <div className="health-card">
                <span className={`health-dot ${health.components.worker_pool.status}`} />
                <span className="health-label">Worker Pool</span>
                <span className="health-value">活跃 {health.components.worker_pool.active}/{health.components.worker_pool.max_workers}</span>
              </div>
            )}
            {health.components.tenants && (
              <div className="health-card">
                <span className="health-dot ok" />
                <span className="health-label">项目数</span>
                <span className="health-value">{health.components.tenants.count}</span>
              </div>
            )}
          </div>
        )}
        {!healthLoading && !health && (
          <div className="muted">后端未连接 — 启动 <code>aitest server start</code></div>
        )}
      </div>

      {/* Product KPIs */}
      {productKpi && (
        <div className="section">
          <h2>本周产品指标</h2>
          <div className="product-kpi-row">
            <div className="pkpi-card">
              <div className="pkpi-value">{productKpi.this_week.runs}</div>
              <div className="pkpi-label">运行次数</div>
              <div className={`pkpi-delta ${productKpi.vs_last_week.runs_delta >= 0 ? 'up' : 'down'}`}>
                {productKpi.vs_last_week.runs_delta >= 0 ? '+' : ''}{productKpi.vs_last_week.runs_delta}
              </div>
            </div>
            <div className="pkpi-card">
              <div className="pkpi-value">{Math.round(productKpi.this_week.success_rate * 100)}%</div>
              <div className="pkpi-label">成功率</div>
              <div className={`pkpi-delta ${productKpi.vs_last_week.trend}`}>
                {productKpi.vs_last_week.success_rate_delta >= 0 ? '+' : ''}{Math.round(productKpi.vs_last_week.success_rate_delta * 100)}%
              </div>
            </div>
            <div className="pkpi-card">
              <div className="pkpi-value">${productKpi.this_week.total_cost.toFixed(2)}</div>
              <div className="pkpi-label">本周成本</div>
              <div className={`pkpi-delta ${productKpi.vs_last_week.cost_delta <= 0 ? 'up' : 'down'}`}>
                {productKpi.vs_last_week.cost_delta <= 0 ? '↓' : '↑'}
              </div>
            </div>
            <div className="pkpi-card">
              <div className="pkpi-value">{productKpi.this_week.agents_used}</div>
              <div className="pkpi-label">活跃 Agent</div>
            </div>
          </div>
        </div>
      )}

      {/* Project list */}
      <div className="section">
        <h2>项目列表</h2>
        {projectLoading && <div className="loading">加载中...</div>}
        {!projectLoading && !hasProjects && (
          <div className="empty-state">
            <p>暂无项目。创建一个新项目开始。</p>
            <Link to="/onboarding" className="btn-primary">+ 新建项目</Link>
          </div>
        )}
        {!projectLoading && hasProjects && (
          <div className="project-cards">
            {projects.map(p => (
              <div
                key={p.id}
                className={`project-card${p.id === activeId ? ' active' : ''}`}
                onClick={() => setActive(p.id)}
              >
                <div className="card-header">
                  <span className="card-name">{p.name || p.id}</span>
                  {p.status && <span className={`badge ${p.status}`}>{p.status}</span>}
                </div>
                <div className="card-body">
                  <span>模块: {p.modules?.length || 0}</span>
                  {p.updated_at && <span>更新: {p.updated_at.slice(0, 10)}</span>}
                </div>
                <div className="card-footer">
                  <Link to="/workspace/kanban" className="card-link" onClick={e => { e.stopPropagation(); setActive(p.id) }}>
                    进入工作区 →
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Quick actions */}
      <div className="section">
        <h2>快速操作</h2>
        <div className="quick-actions">
          <Link to="/onboarding" className="action-card">
            <span className="action-icon">🔍</span><span className="action-text">发现新项目</span>
          </Link>
          <Link to="/workspace/kanban" className="action-card">
            <span className="action-icon">▶️</span><span className="action-text">运行 SOP</span>
          </Link>
          <Link to="/workspace/reports" className="action-card">
            <span className="action-icon">📊</span><span className="action-text">查看报告</span>
          </Link>
          <Link to="/settings" className="action-card">
            <span className="action-icon">⚙️</span><span className="action-text">平台设置</span>
          </Link>
        </div>
      </div>

      <style>{`
        .dashboard { padding: 24px 32px; max-width: 1200px; }
        .dashboard-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 24px; }
        .header-left { display: flex; align-items: center; gap: 10px; }
        .header-left h1 { font-size: 22px; font-weight: 700; margin: 0; }
        .stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 32px; }
        .stat-card { background: var(--bg-primary); border: 1px solid var(--border); border-radius: 12px; padding: 20px; text-align: center; }
        .stat-icon { margin-bottom: 8px; opacity: .7; }
        .stat-value { font-size: 28px; font-weight: 700; }
        .stat-label { font-size: 12px; color: var(--text-muted); margin-top: 4px; }
        .stat-card.green .stat-icon { color: #22c55e; }
        .stat-card.yellow .stat-icon { color: #eab308; }
        .stat-card.blue .stat-icon { color: #3b82f6; }
        .section { margin-bottom: 32px; }
        .section h2 { font-size: 16px; font-weight: 600; margin-bottom: 16px; }
        .project-cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px; }
        .project-card { background: var(--bg-primary); border: 2px solid var(--border); border-radius: 12px; padding: 16px; cursor: pointer; transition: border-color .15s, box-shadow .15s; }
        .project-card:hover, .project-card.active { border-color: var(--accent); box-shadow: 0 2px 8px rgba(0,0,0,.08); }
        .card-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
        .card-name { font-weight: 600; }
        .badge { font-size: 10px; padding: 2px 8px; border-radius: 10px; text-transform: uppercase; }
        .badge.completed { background: #d4edda; color: #155724; }
        .badge.issues, .badge.completed_with_issues { background: #fff3cd; color: #856404; }
        .card-body { display: flex; gap: 16px; font-size: 12px; color: var(--text-muted); margin-bottom: 12px; }
        .card-footer { text-align: right; }
        .card-link { font-size: 13px; color: var(--accent); text-decoration: none; }
        .quick-actions { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
        .action-card { display: flex; flex-direction: column; align-items: center; gap: 8px; padding: 20px; background: var(--bg-primary); border: 1px solid var(--border); border-radius: 12px; text-decoration: none; color: var(--text-primary); transition: background .15s; }
        .action-card:hover { background: var(--bg-secondary); }
        .section-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
        .section-header h2 { display: flex; align-items: center; gap: 6px; margin: 0; }
        .btn-refresh { font-size: 12px; padding: 4px 12px; border: 1px solid var(--border); border-radius: 6px; background: var(--bg-primary); cursor: pointer; }
        .health-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; }
        .health-card { display: flex; align-items: center; gap: 8px; padding: 12px 16px; background: var(--bg-primary); border: 1px solid var(--border); border-radius: 10px; }
        .health-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
        .health-dot.healthy, .health-dot.ok { background: #22c55e; }
        .health-dot.degraded { background: #eab308; }
        .health-dot.error { background: #ef4444; }
        .health-label { font-size: 12px; color: var(--text-muted); min-width: 60px; }
        .health-value { font-size: 13px; font-weight: 600; }
        .health-warn { font-size: 11px; color: #ef4444; background: #fef2f2; padding: 1px 6px; border-radius: 4px; margin-left: auto; }
        .loading { color: var(--text-muted); padding: 12px 0; }
        .muted { color: var(--text-muted); font-size: 13px; padding: 12px 0; }
        .muted code { background: var(--bg-secondary); padding: 2px 6px; border-radius: 3px; }
        .product-kpi-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
        .pkpi-card { background: var(--bg-primary); border: 1px solid var(--border); border-radius: 10px; padding: 16px; text-align: center; }
        .pkpi-value { font-size: 26px; font-weight: 700; }
        .pkpi-label { font-size: 11px; color: var(--text-muted); margin-top: 4px; }
        .pkpi-delta { font-size: 12px; font-weight: 600; margin-top: 4px; }
        .pkpi-delta.up { color: #22c55e; } .pkpi-delta.down { color: #ef4444; }
        .action-icon { font-size: 24px; }
        .action-text { font-size: 13px; font-weight: 500; }
        .loading, .empty-state { text-align: center; padding: 40px; color: var(--text-muted); }
        .btn-primary { display: inline-block; margin-top: 12px; padding: 8px 20px; background: var(--accent); color: #fff; border-radius: 8px; text-decoration: none; font-size: 13px; }
      `}</style>
    </div>
  )
}

function StatCard({ icon: Icon, value, label, color }: { icon: any; value: number; label: string; color?: string }) {
  return (
    <div className={`stat-card${color ? ` ${color}` : ''}`}>
      <Icon size={20} className="stat-icon" />
      <div className="stat-value">{value}</div>
      <div className="stat-label">{label}</div>
    </div>
  )
}
