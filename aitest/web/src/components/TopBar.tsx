/**
 * TopBar — 顶部导航栏
 * 面包屑 + 搜索 + 通知 + 时间
 * shadcn/ui edition
 */
import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Search, Bell, ChevronRight, Moon, Sun } from 'lucide-react'
import { useSettingsStore } from '../stores/settings'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { listNotifications, type StudioNotification } from '@/api/studio'

interface TopBarProps {
  /** 当前路径用于生成面包屑 */
  currentView?: string
  /** 标题（可选，覆盖自动推断） */
  title?: string
}

// ── 视图名称映射 ──
const viewNames: Record<string, string> = {
  dashboard: 'Dashboard',
  workflow: 'Workflow',
  execution: 'Execution',
  memory: 'Memory',
  knowledge: 'Knowledge',
  tools: 'Tools',
  history: 'History',
  settings: 'Settings',
}

export default function TopBar({ currentView = 'dashboard', title }: TopBarProps) {
  const { t } = useTranslation()
  const darkMode = useSettingsStore(s => s.app.darkMode)
  const updateApp = useSettingsStore(s => s.updateApp)

  const [currentTime, setCurrentTime] = useState(new Date())
  const [notifications, setNotifications] = useState<StudioNotification[]>([])
  const [notificationsOpen, setNotificationsOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')

  // ── 时钟更新 ──
  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  useEffect(() => {
    let mounted = true
    void listNotifications().then((data) => { if (mounted) setNotifications(data.notifications) }).catch(() => { if (mounted) setNotifications([]) })
    return () => { mounted = false }
  }, [])

  const displayTitle = title || viewNames[currentView] || 'Dashboard'
  const timeString = currentTime.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
  })
  const dateString = currentTime.toLocaleDateString('zh-CN', {
    month: 'short',
    day: 'numeric',
    weekday: 'short',
  })

  return (
    <header className="relative h-14 flex items-center justify-between px-6 border-b border-border bg-card/80 backdrop-blur-sm">
      {/* ── 左侧：面包屑 ── */}
      <div className="flex items-center gap-2">
        <span className="text-sm text-muted-foreground">Platform</span>
        <ChevronRight size={14} className="text-muted-foreground/50" />
        <span className="text-sm font-semibold text-foreground">{displayTitle}</span>
      </div>

      {/* ── 中间：搜索框 ── */}
      <div className="flex-1 max-w-md mx-8">
        <div className="relative">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground/60" />
          <Input
            type="text"
            placeholder={t('common.search', 'Search...')}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="h-9 pl-10 pr-4 text-sm bg-muted/50 border-transparent focus:border-primary focus:bg-background"
          />
          <kbd className="absolute right-3 top-1/2 -translate-y-1/2 px-1.5 py-0.5 text-[10px] font-mono text-muted-foreground/60 bg-muted rounded">
            /
          </kbd>
        </div>
      </div>

      {/* ── 右侧：通知 + 时间 + 主题切换 ── */}
      <div className="flex items-center gap-4">
        {/* 通知按钮 */}
        <Button
          variant="ghost"
          size="sm"
          className="relative h-9 w-9 p-0"
          aria-label={t('notifications', 'Notifications')}
          aria-expanded={notificationsOpen}
          onClick={() => setNotificationsOpen(value => !value)}
        >
          <Bell size={18} className="text-muted-foreground" />
          {notifications.length > 0 && (
            <Badge
              variant="destructive"
              className="absolute -top-1 -right-1 h-4 min-w-4 px-1 text-[10px] font-semibold rounded-full"
            >
              {notifications.length}
            </Badge>
          )}
        </Button>
        {notificationsOpen && (
          <div role="dialog" className="absolute right-20 top-12 z-30 w-80 rounded-lg border border-border bg-card p-4 shadow-xl">
            <div className="text-xs font-semibold text-foreground">{t('notifications', 'Notifications')}</div>
            {notifications.length === 0 ? <div className="mt-3 text-xs text-muted-foreground">{t('common.noNotifications', 'No new notifications')}</div> : <div className="mt-3 space-y-2">{notifications.slice(0, 5).map(item => <div key={item.id} className="rounded border border-border/70 bg-muted/30 p-2"><div className="text-xs font-medium">{item.title}</div><div className="mt-1 text-[11px] text-muted-foreground">{item.message}</div></div>)}</div>}
          </div>
        )}

        {/* 时间显示 */}
        <div className="flex flex-col items-end">
          <span className="text-sm font-semibold text-foreground font-mono">{timeString}</span>
          <span className="text-[11px] text-muted-foreground">{dateString}</span>
        </div>

        {/* 深色模式切换按钮 */}
        <Button
          variant="ghost"
          size="sm"
          className="h-9 w-9 p-0"
          onClick={() => updateApp({ darkMode: !darkMode })}
          aria-label={darkMode ? 'Switch to light mode' : 'Switch to dark mode'}
        >
          {darkMode ? (
            <Sun size={16} className="text-muted-foreground" />
          ) : (
            <Moon size={16} className="text-muted-foreground" />
          )}
        </Button>
      </div>
    </header>
  )
}
