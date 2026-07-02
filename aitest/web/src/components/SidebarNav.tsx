/** Segmented sidebar: Dashboard | Workspace (per-project) | Bottom actions.
 *  shadcn/ui edition — Button + Collapsible + Separator.
 */
import { useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useProjectStore } from '../stores/project'
import { useSettingsStore } from '../stores/settings'
import {
  LayoutDashboard, LayoutGrid, Search, MessageSquare, Play,
  BarChart3, BookOpen, Settings, Plus, FolderOpen, Terminal,
  Lightbulb, Link2, Clock, Eye, ChevronDown, Moon, Zap, TreePine, Network,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import { cn } from '@/lib/utils'

interface SidebarNavProps {
  currentView: string
  onNavigate: (view: string) => void
}

type TierItem = { id: string; icon: React.ComponentType<{ className?: string }>; key: string }

const tier1Items: TierItem[] = [
  { id: 'timeline', icon: Clock, key: '时间线' },
  { id: 'execution', icon: Play, key: '执行中心' },
  { id: 'artifacts', icon: FolderOpen, key: '产物' },
]

const tier2Items: TierItem[] = [
  { id: 'observability', icon: Clock, key: '可观测性' },
  { id: 'reports', icon: BarChart3, key: '报告' },
  { id: 'knowledge', icon: BookOpen, key: '知识' },
  { id: 'knowledgegraph', icon: Network, key: '知识图谱' },
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
  if (view === 'onboarding') return 'bottom'
  if (view === 'settings') return 'bottom'
  return 'project'
}

const themeIcon: Record<string, any> = {
  default:   Moon,
  aoko:      Zap,
  soujuurou: TreePine,
}

export default function SidebarNav({ currentView, onNavigate }: SidebarNavProps) {
  const { t } = useTranslation()
  const activeId = useProjectStore(s => s.activeId)
  const activeProject = useProjectStore(s => s.activeProject())
  const hasActiveProject = !!activeId
  const pid = activeId || 'default'
  const [toolsOpen, setToolsOpen] = useState(false)
  const theme = useSettingsStore(s => s.app.theme)
  const LogoIcon = themeIcon[theme] || Moon

  const hasProjectData = useMemo(() => {
    // Check if active project has modules or if any project exists
    return (activeProject?.modules?.length ?? 0) > 0 || !!activeId
  }, [activeProject, activeId])

  const section = currentSection(currentView)
  const projectActive = (itemId: string) => currentView === itemId

  const NavBtn = ({ active, onClick, icon: Icon, label }: {
    active: boolean; onClick: () => void; icon: React.ComponentType<{ className?: string }>; label: string
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
    <aside className="w-[232px] flex flex-col shrink-0 select-none border-r border-sidebar-border bg-sidebar">
      {/* Logo */}
      <div className="px-5 py-4 flex items-center gap-2.5 border-b border-sidebar-border">
        <div className="w-7 h-7 rounded-lg flex items-center justify-center"
          style={{ background: 'var(--primary-gradient)' }}>
          <LogoIcon size={14} className="text-white" strokeWidth={2.5} />
        </div>
        <span className="text-[15px] font-bold text-sidebar-logo">
          TLO<span className="font-light opacity-50"> Platform</span>
        </span>
      </div>

      <nav className="flex-1 p-2.5 flex flex-col overflow-y-auto gap-0.5">
        {/* Dashboard */}
        <NavBtn
          active={section === 'dashboard'}
          onClick={() => onNavigate('/dashboard')}
          icon={LayoutDashboard}
          label="面板"
        />

        <div className="h-px mx-2 my-2 bg-sidebar-border opacity-60" />

        {/* Workspace */}
        {hasActiveProject ? (
          <div className="mt-1">
            <div className="flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-semibold text-sidebar-foreground/50 uppercase tracking-wider">
              <FolderOpen size={12} />
              <span className="truncate">{activeProject?.name || activeProject?.id || 'Workspace'}</span>
            </div>

            {tier1Items.map(item => (
              <NavBtn
                key={item.id}
                active={projectActive(item.id)}
                onClick={() => onNavigate(`/projects/${pid}/${item.id}`)}
                icon={item.icon}
                label={item.key}
              />
            ))}

            {hasProjectData && (
              <>
                <div className="h-px mx-3 my-1 bg-sidebar-border opacity-40" />
                {tier2Items.map(item => (
                  <NavBtn
                    key={item.id}
                    active={projectActive(item.id)}
                    onClick={() => onNavigate(`/projects/${pid}/${item.id}`)}
                    icon={item.icon}
                    label={item.key}
                  />
                ))}
              </>
            )}

            {/* Tier 3: collapsible */}
            <Collapsible open={toolsOpen} onOpenChange={setToolsOpen} className="mt-1">
              <CollapsibleTrigger asChild>
                <button className={cn(
                  'flex items-center gap-1 w-full px-3 py-1 text-[10px] uppercase tracking-wider text-sidebar-foreground/40 hover:text-sidebar-foreground/70 transition-colors cursor-pointer',
                  toolsOpen && 'text-sidebar-foreground/60'
                )}>
                  <ChevronDown size={10} className={cn('transition-transform', toolsOpen && 'rotate-180')} />
                  更多工具
                </button>
              </CollapsibleTrigger>
              <CollapsibleContent>
                {tier3Items.map(item => (
                  <NavBtn
                    key={item.id}
                    active={projectActive(item.id)}
                    onClick={() => onNavigate(`/projects/${pid}/${item.id}`)}
                    icon={item.icon}
                    label={item.key}
                  />
                ))}
              </CollapsibleContent>
            </Collapsible>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2 py-8 px-4 text-center">
            <FolderOpen size={24} className="opacity-30" />
            <p className="text-xs text-muted-foreground m-0">选择一个项目以查看工作区</p>
            <button onClick={() => onNavigate('/dashboard')} className="text-xs text-primary bg-transparent border-none cursor-pointer hover:underline">
              前往面板
            </button>
          </div>
        )}
      </nav>

      {/* Bottom actions */}
      <div className="p-2.5 flex flex-col gap-0.5 border-t border-sidebar-border">
        <NavBtn
          active={currentView === 'onboarding'}
          onClick={() => onNavigate('/onboarding')}
          icon={Plus}
          label={t('nav.onboarding')}
        />
        <NavBtn
          active={currentView === 'settings'}
          onClick={() => onNavigate('/settings')}
          icon={Settings}
          label={t('nav.settings')}
        />
      </div>
    </aside>
  )
}
