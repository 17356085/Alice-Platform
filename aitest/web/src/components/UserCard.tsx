/**
 * UserCard — 用户信息卡片
 * 显示头像、用户名、角色，可展开菜单
 */
import { useTranslation } from 'react-i18next'
import { LogOut, Settings, User, ChevronRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

interface UserCardProps {
  /** 用户名 */
  username?: string
  /** 用户邮箱 */
  email?: string
  /** 角色 */
  role?: 'admin' | 'user' | 'viewer'
  /** 头像URL（可选） */
  avatarUrl?: string
  /** 点击设置 */
  onSettings?: () => void
  /** 点击退出 */
  onLogout?: () => void
}

export default function UserCard({
  username = 'alice',
  email = 'alice@lab.dev',
  role = 'admin',
  avatarUrl,
  onSettings,
  onLogout,
}: UserCardProps) {
  const { t } = useTranslation()

  // 角色颜色映射
  const roleColors: Record<string, string> = {
    admin: 'bg-primary text-primary-foreground',
    user: 'bg-secondary text-secondary-foreground',
    viewer: 'bg-muted text-muted-foreground',
  }

  return (
    <div className="p-3 rounded-lg bg-card border border-border/50">
      {/* 用户信息 */}
      <div className="flex items-center gap-3">
        {/* 头像 */}
        <div className={cn(
          'w-10 h-10 rounded-full flex items-center justify-center text-sm font-semibold',
          roleColors[role] || roleColors.user
        )}>
          {avatarUrl ? (
            <img src={avatarUrl} alt={username} className="w-full h-full rounded-full object-cover" />
          ) : (
            username.charAt(0).toUpperCase()
          )}
        </div>

        {/* 用户详情 */}
        <div className="flex-1 min-w-0">
          <div className="text-sm font-semibold text-foreground truncate">{username}</div>
          <div className="text-xs text-muted-foreground truncate">{email}</div>
          <div className="flex items-center gap-1 mt-0.5">
            <span className={cn(
              'px-1.5 py-0.5 text-[10px] font-medium rounded capitalize',
              roleColors[role] || roleColors.user
            )}>
              {role}
            </span>
          </div>
        </div>
      </div>

      {/* 操作按钮 */}
      <div className="flex items-center gap-2 mt-3 pt-3 border-t border-border/50">
        <Button
          variant="ghost"
          size="sm"
          className="flex-1 h-8 text-xs"
          onClick={onSettings}
        >
          <Settings size={14} className="mr-1.5" />
          {t('user.settings', 'Settings')}
        </Button>
        <Button
          variant="ghost"
          size="sm"
          className="flex-1 h-8 text-xs text-destructive hover:text-destructive"
          onClick={onLogout}
        >
          <LogOut size={14} className="mr-1.5" />
          {t('user.logout', 'Logout')}
        </Button>
      </div>
    </div>
  )
}
