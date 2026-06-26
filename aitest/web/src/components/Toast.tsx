/** Toast notification system — React port.
 *  Exposes add() globally via window.__tlo_toast for non-React callers.
 */
import { useState, useEffect, useCallback } from 'react'

interface ToastMsg {
  id: number
  text: string
  type: 'success' | 'error' | 'warning' | 'info'
  ts: number
}

let nextId = 0

export default function Toast() {
  const [toasts, setToasts] = useState<ToastMsg[]>([])

  const addToast = useCallback((text: string, type: ToastMsg['type'] = 'info', duration = 3000) => {
    const id = nextId++
    setToasts(prev => [...prev, { id, text, type, ts: Date.now() }])
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id))
    }, duration)
  }, [])

  // Expose globally
  useEffect(() => {
    (window as any).__tlo_toast = { add: addToast }
  }, [addToast])

  const icon = (type: ToastMsg['type']) => {
    switch (type) {
      case 'success': return '✅'
      case 'error': return '❌'
      case 'warning': return '⚠️'
      default: return 'ℹ️'
    }
  }

  return (
    <div className="fixed bottom-5 right-5 z-[100] flex flex-col gap-2 pointer-events-none">
      {toasts.map(t => (
        <div
          key={t.id}
          className={`px-4 py-2.5 rounded-lg text-sm font-medium shadow-lg pointer-events-auto animate-slide-up max-w-[360px] ${
            t.type === 'success' ? 'bg-success text-success-foreground' :
            t.type === 'error' ? 'bg-destructive text-destructive-foreground' :
            t.type === 'warning' ? 'bg-warning text-warning-foreground' :
            'bg-card text-foreground border border-border'
          }`}
        >
          <span className="mr-2">{icon(t.type)}</span>
          {t.text}
        </div>
      ))}
      <style>{`
        @keyframes slide-up {
          from { transform: translateY(16px); opacity: 0; }
          to { transform: translateY(0); opacity: 1; }
        }
        .animate-slide-up { animation: slide-up 0.3s ease-out; }
      `}</style>
    </div>
  )
}
