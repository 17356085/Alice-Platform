/** Segmented sidebar: Dashboard | Workspace (per-project) | Bottom actions.
 *  shadcn/ui edition — Button + Collapsible + Separator.
 *
 *  Updated to match Figma design: Alice 有珠 platform
 */
import { useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useProjectStore } from '../stores/project'
import { useSettingsStore } from '../stores/settings'
import {
  LayoutDashboard, Workflow, Play, Brain, BookOpen, Wrench, Clock,
  Settings, Plus,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

interface SidebarNavProps {
  currentView: string
  onNavigate: (view: string) => void
}

type TierItem = { id: string; icon: LucideIcon; key: string }

// ── 主导航菜单（7个功能模块）─────────────────────────────────────
const mainNavItems: TierItem[] = [
  { id: 'dashboard', icon: LayoutDashboard, key: 'Dashboard' },
  { id: 'workflow', icon: Workflow, key: 'Workflow' },
  { id: 'execution', icon: Play, key: 'Execution' },
  { id: 'memory', icon: Brain, key: 'Memory' },
  { id: 'knowledge', icon: BookOpen, key: 'Knowledge' },
  { id: 'tools', icon: Wrench, key: 'Tools' },
  { id: 'history', icon: Clock, key: 'History' },
]

function currentSection(view: string): 'main' | 'bottom' {
  if (view === 'settings') return 'bottom'
  return 'main'
}

const themeIcon: Record<string, any> = {
  default:   Brain,
  aoko:      Play,
  soujuurou: Workflow,
}

export default function SidebarNav({ currentView, onNavigate }: SidebarNavProps) {
  const { t } = useTranslation()
  const activeId = useProjectStore(s => s.activeId)
  const activeProject = useProjectStore(s => s.activeProject())
  const hasActiveProject = !!activeId
  const theme = useSettingsStore(s => s.app.theme)
  const LogoIcon = themeIcon[theme] || Brain

  // ── 运行中的Agent数量（模拟数据，实际应从store获取）──
  const runningAgentCount = 3

  const section = currentSection(currentView)

  const NavBtn = ({ active, onClick, icon: Icon, label }: {
    active: boolean; onClick: () => void; icon: LucideIcon; label: string
  }) => (
    <Button
      variant="ghost"
      size="sm"
      onClick={onClick}
      aria-label={label}
      aria-current={active ? 'page' : undefined}
      className={cn(
        'justify-start gap-3 w-full h-9 pl-2.5 pr-3 text-[13px] font-medium relative border-l-[3px]',
        'transition-all duration-300 ease-out',
        active
          ? 'bg-sidebar-active-bg text-sidebar-active border-l-sidebar-active [&>svg]:stroke-[2.5]'
          : 'text-sidebar-foreground border-l-transparent hover:bg-sidebar-hover hover:text-sidebar-foreground/90 hover:border-l-sidebar-foreground/20 [&>svg]:stroke-[1.8]'
      )}
    >
      <Icon size={18} className="shrink-0" aria-hidden="true" />
      <span className="truncate">{label}</span>
    </Button>
  )

  return (
    <aside className="w-[240px] flex flex-col shrink-0 select-none border-r border-sidebar-border bg-sidebar">
      {/* ── Logo区域 ── */}
      <div className="px-5 py-4 flex items-center gap-2.5 border-b border-sidebar-border">
        <div className="w-8 h-8 rounded-lg flex items-center justify-center bg-primary">
          <LogoIcon size={16} className="text-white" strokeWidth={2.5} />
        </div>
        <div className="flex flex-col">
          <span className="text-[15px] font-bold text-sidebar-logo">Alice</span>
          <span className="text-[11px] text-sidebar-foreground/60 -mt-0.5">有珠</span>
        </div>
      </div>

      {/* ── 实时状态指示器 ── */}
      <div className="px-4 py-2.5">
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-success/10 border border-success/20">
          <div className="w-2 h-2 rounded-full bg-success animate-pulse" />
          <span className="text-[12px] font-medium text-success">
            {runningAgentCount} agents running
          </span>
        </div>
      </div>

      {/* ── 主导航菜单 ── */}
      <nav className="flex-1 p-2.5 flex flex-col overflow-y-auto gap-0.5">
        {mainNavItems.map(item => (
          <NavBtn
            key={item.id}
            active={currentView === item.id}
            onClick={() => onNavigate(`/${item.id}`)}
            icon={item.icon}
            label={item.key}
          />
        ))}
      </nav>

      {/* ── 底部区域 ── */}
      <div className="p-2.5 flex flex-col gap-0.5 border-t border-sidebar-border">
        <NavBtn
          active={currentView === 'settings'}
          onClick={() => onNavigate('/settings')}
          icon={Settings}
          label={t('nav.settings')}
        />

        {/* ── 用户信息 ── */}
        <div className="flex items-center gap-3 px-3 py-2 mt-2 rounded-lg hover:bg-sidebar-hover transition-colors cursor-pointer">
          <div className="w-8 h-8 rounded-full flex items-center justify-center bg-primary text-primary-foreground text-[12px] font-semibold">
            A
          </div>
          <div className="flex flex-col flex-1 min-w-0">
            <span className="text-[12px] font-medium text-sidebar-foreground truncate">alice@lab.dev</span>
            <span className="text-[10px] text-sidebar-foreground/60">Admin</span>
          </div>
        </div>
      </div>
    </aside>
  )
}
