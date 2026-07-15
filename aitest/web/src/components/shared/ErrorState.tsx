import { AlertTriangle } from 'lucide-react'
import type { ReactNode } from 'react'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'

export function ErrorState({ title = '加载失败', message, action }: { title?: string; message: string; action?: ReactNode }) {
  return (
    <Alert variant="destructive" role="alert">
      <AlertTriangle className="size-4" />
      <AlertTitle>{title}</AlertTitle>
      <AlertDescription className="flex flex-wrap items-center gap-3">
        <span>{message}</span>
        {action}
      </AlertDescription>
    </Alert>
  )
}
