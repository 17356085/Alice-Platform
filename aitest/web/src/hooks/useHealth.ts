/** Fetch platform health — React port.
 *  Vue onMounted → useEffect with [].
 *  ref() → useState.
 */
import { useState, useEffect, useCallback } from 'react'
import { api } from '../api/client'

interface HealthComponent { status: string; [key: string]: unknown }
interface HealthData { status: string; components: Record<string, HealthComponent> }

export function useHealth() {
  const [health, setHealth] = useState<HealthData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const refresh = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const data = await api.get<HealthData>('/health')
      setHealth(data)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { refresh() }, [refresh])

  return { health, loading, error, refresh }
}
