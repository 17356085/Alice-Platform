/** Segmented sidebar: Dashboard | Workspace (per-project) | Bottom actions.
 *  React port — Vue template directives → JSX conditional rendering.
 */
import { useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useProjectStore } from '../stores/project'
import {
  LayoutDashboard, LayoutGrid, Search, MessageSquare, Play,
  BarChart3, BookOpen, Settings, Plus, FolderOpen, Terminal,
  Lightbulb, Link2, Clock, Eye,
} from 'lucide-react'

interface SidebarNavProps {
  currentView: string
  onNavigate: (view: string) => void
}

// ── Nav items ──────────────────────────────────────────────────

type TierItem = { id: string; icon: any; key: string }

const tier1Items: TierItem[] = [
  { id: 'execution', icon: Play, key: '执行中心' },
  { id: 'artifacts', icon: FolderOpen, key: '产物' },
]

const tier2Items: TierItem[] = [
  { id: 'observability', icon: Clock, key: '可观测性' },
  { id: 'reports', icon: BarChart3, key: '报告' },
  { id: 'knowledge', icon: BookOpen, key: '知识' },
  { id: 'kanban', icon: LayoutGrid, key: '看板' },
]

const tier3Items: TierItem[] = [
  { id: 'terminal', icon: Terminal, key: '终端' },
  { id: 'gaps', icon: Search, key: '缺口' },
  { id: 'chat', icon: MessageSquare, key: '对话' },
  { id: 'settings', icon: Settings, key: '设置' },
]

function currentSection(view: string): 'dashboard' | 'project' | 'bottom' {
  if (view === 'dashboard') return 'dashboard'
  if (view.startsWith('project-') || view === 'overview' ||
      view === 'execution' || view === 'kanban' || view === 'gaps' ||
      view === 'chat' || view === 'terminal' || view === 'reports' ||
      view === 'knowledge' || view === 'observability' || view === 'artifacts' ||
      view === 'strategy') return 'project'
  return 'bottom'
}

// ── Styles (inline for CSS var compatibility) ──────────────────

const navBtnBase: React.CSSProperties = {
  display: 'flex', alignItems: 'center', gap: 12,
  padding: '8px 12px', borderRadius: 8, fontSize: 13,
  width: '100%', textAlign: 'left', border: 'none', cursor: 'pointer',
  fontWeight: 500, transition: 'all .15s', background: 'transparent',
}

// ── Component ──────────────────────────────────────────────────

export default function SidebarNav({ currentView, onNavigate }: SidebarNavProps) {
  const { t } = useTranslation()
  const activeId = useProjectStore(s => s.activeId)
  const activeProject = useProjectStore(s => s.activeProject())
  const hasActiveProject = !!activeId
  const pid = activeId || 'default'

  const hasProjectData = useMemo(() => {
    try {
      const mods = JSON.parse(localStorage.getItem('tlo-modules') || '{}')
      return Object.keys(mods).length > 0
    } catch { return false }
  }, [])

  const section = currentSection(currentView)

  const navBtnStyle = (active: boolean): React.CSSProperties => ({
    ...navBtnBase,
    ...(active
      ? { background: 'var(--sidebar-active-bg)', color: 'var(--sidebar-active)' }
      : { color: 'var(--sidebar-foreground)' }),
  })

  const projectActive = (itemId: string) => currentView === itemId

  return (
    <aside
      className="w-[232px] flex flex-col flex-shrink-0 select-none border-r"
      style={{ background: 'var(--sidebar)', borderColor: 'var(--sidebar-border)' }}
    >
      {/* Logo */}
      <div
        className="px-5 py-4 flex items-center gap-2.5"
        style={{ borderBottom: '1px solid var(--sidebar-border)' }}
      >
        <div
          className="w-7 h-7 rounded-lg flex items-center justify-center"
          style={{ background: 'var(--primary-gradient)' }}
        >
          <Play size={14} className="text-white" fill="white" strokeWidth={3} />
        </div>
        <span className="text-[15px] font-bold" style={{ color: 'var(--sidebar-logo)' }}>
          TLO<span className="font-light opacity-50"> Platform</span>
        </span>
      </div>

      <nav className="flex-1 p-2.5 flex flex-col overflow-y-auto">
        {/* Section: Dashboard */}
        <button
          onClick={() => onNavigate('/dashboard')}
          style={navBtnStyle(section === 'dashboard')}
          className="nav-btn"
        >
          <LayoutDashboard size={18} strokeWidth={section === 'dashboard' ? 2.5 : 1.8} className="flex-shrink-0" />
          <span className="truncate">面板</span>
        </button>

        {/* Divider */}
        <div className="sidebar-divider" />

        {/* Section: Workspace */}
        {hasActiveProject ? (
          <div className="workspace-section">
            <div className="section-label">
              <FolderOpen size={12} />
              <span className="truncate">{activeProject?.name || activeProject?.id || 'Workspace'}</span>
            </div>

            {/* Tier 1: core workflow */}
            {tier1Items.map(item => (
              <button
                key={item.id}
                onClick={() => onNavigate(`/projects/${pid}/${item.id}`)}
                style={navBtnStyle(projectActive(item.id))}
                className="nav-btn"
              >
                <item.icon size={18} strokeWidth={projectActive(item.id) ? 2.5 : 1.8} className="flex-shrink-0" />
                <span className="truncate">{item.key}</span>
              </button>
            ))}

            {/* Tier 2: visible when project has data */}
            {hasProjectData && (
              <>
                <div className="tier-divider" />
                {tier2Items.map(item => (
                  <button
                    key={item.id}
                    onClick={() => onNavigate(`/projects/${pid}/${item.id}`)}
                    style={navBtnStyle(projectActive(item.id))}
                    className="nav-btn"
                  >
                    <item.icon size={18} strokeWidth={projectActive(item.id) ? 2.5 : 1.8} className="flex-shrink-0" />
                    <span className="truncate">{item.key}</span>
                  </button>
                ))}
              </>
            )}

            {/* Tier 3: advanced tools (collapsible) */}
            <details className="tier-details">
              <summary className="tier-summary">更多工具</summary>
              {tier3Items.map(item => (
                <button
                  key={item.id}
                  onClick={() => onNavigate(`/projects/${pid}/${item.id}`)}
                  style={navBtnStyle(projectActive(item.id))}
                  className="nav-btn"
                >
                  <item.icon size={18} strokeWidth={projectActive(item.id) ? 2.5 : 1.8} className="flex-shrink-0" />
                  <span className="truncate">{item.key}</span>
                </button>
              ))}
            </details>
          </div>
        ) : (
          /* No project selected */
          <div className="no-project-hint">
            <FolderOpen size={24} className="hint-icon" />
            <p>选择一个项目以查看工作区</p>
            <button onClick={() => onNavigate('/dashboard')} className="hint-link">前往面板</button>
          </div>
        )}
      </nav>

      {/* Bottom actions */}
      <div className="p-2.5 flex flex-col gap-0.5" style={{ borderTop: '1px solid var(--sidebar-border)' }}>
        <button
          onClick={() => onNavigate('/onboarding')}
          style={navBtnStyle(currentView === 'onboarding')}
          className="nav-btn"
        >
          <Plus size={18} strokeWidth={currentView === 'onboarding' ? 2.5 : 1.8} className="flex-shrink-0" />
          <span className="truncate">{t('nav.onboarding')}</span>
        </button>
        <button
          onClick={() => onNavigate('/settings')}
          style={navBtnStyle(currentView === 'settings')}
          className="nav-btn"
        >
          <Settings size={18} strokeWidth={currentView === 'settings' ? 2.5 : 1.8} className="flex-shrink-0" />
          <span className="truncate">{t('nav.settings')}</span>
        </button>
      </div>

      {/* scoped styles */}
      <style>{`
        .nav-btn:hover { background: var(--sidebar-active-bg); opacity: .85; }
        .sidebar-divider { height: 1px; margin: 8px 8px; background: var(--sidebar-border); opacity: .6; }
        .workspace-section { margin-top: 4px; }
        .section-label { display: flex; align-items: center; gap: 6px; padding: 6px 12px; font-size: 11px; font-weight: 600; color: var(--sidebar-foreground); opacity: .5; text-transform: uppercase; letter-spacing: .5px; }
        .no-project-hint { display: flex; flex-direction: column; align-items: center; gap: 8px; padding: 32px 16px; text-align: center; }
        .no-project-hint p { font-size: 12px; color: var(--text-muted); margin: 0; }
        .hint-icon { opacity: .3; }
        .hint-link { font-size: 12px; color: var(--accent); background: none; border: none; cursor: pointer; }
        .tier-divider { height: 1px; margin: 4px 12px; background: var(--sidebar-border); opacity: .4; }
        .tier-details { margin-top: 4px; }
        .tier-summary { font-size: 10px; padding: 4px 12px; cursor: pointer; color: var(--sidebar-foreground); opacity: .4; text-transform: uppercase; letter-spacing: .5px; user-select: none; }
        .tier-summary:hover { opacity: .7; }
        .tier-details[open] .tier-summary { opacity: .6; }
      `}</style>
    </aside>
  )
}
