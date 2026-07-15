import type { LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'

interface EmptyStateProps {
  icon?: LucideIcon
  title: string
  description?: string
  action?: ReactNode
  className?: string
}

export function EmptyState({ icon: Icon, title, description, action, className }: EmptyStateProps) {
  return (
    <div className={cn('flex min-h-40 flex-col items-center justify-center gap-2 rounded-lg border border-dashed border-border px-6 py-10 text-center', className)}>
      {Icon ? <Icon className="mb-1 size-5 text-muted-foreground" aria-hidden="true" /> : null}
      <p className="m-0 text-sm font-medium text-foreground">{title}</p>
      {description ? <p className="m-0 max-w-md text-sm text-muted-foreground">{description}</p> : null}
      {action ? <div className="mt-2">{action}</div> : null}
    </div>
  )
}
