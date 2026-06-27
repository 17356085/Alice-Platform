/** Toast utility — wraps Sonner. Keeps window.__tlo_toast for non-React callers. */
import { toast as sonnerToast, Toaster as SonnerToaster } from 'sonner'

type ToastType = 'success' | 'error' | 'warning' | 'info'

export function toast(text: string, type: ToastType = 'info', duration = 3000) {
  switch (type) {
    case 'success': return sonnerToast.success(text, { duration })
    case 'error':   return sonnerToast.error(text, { duration })
    case 'warning': return sonnerToast.warning(text, { duration })
    default:        return sonnerToast(text, { duration })
  }
}

export function Toaster() {
  return (
    <SonnerToaster
      position="bottom-right"
      toastOptions={{
        className: '!rounded-lg !border !border-border !bg-card !text-foreground',
      }}
    />
  )
}

// Expose globally for non-React callers
if (typeof window !== 'undefined') {
  (window as any).__tlo_toast = { add: toast }
}
