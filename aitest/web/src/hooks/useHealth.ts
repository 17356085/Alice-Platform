/** Fetch platform health — React port.
 *  Vue onMounted → useEffect with [].
 *  ref() → useState.
 */
import { useState, useEffect, useCallback } from 'react'

interface HealthComponent { status: string; [key: string]: any }
interface HealthData { status: string; components: Record<string, HealthComponent> }

export function useHealth() {
  const [health, setHealth] = useState<HealthData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const refresh = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const resp = await fetch('/api/../health')
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
      setHealth(await resp.json())
    } catch (e: any) {
      try {
        const resp = await fetch('http://localhost:8000/health')
        if (resp.ok) setHealth(await resp.json())
        else setError(e.message)
      } catch {
        setError(e.message)
      }
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { refresh() }, [refresh])

  return { health, loading, error, refresh }
}
