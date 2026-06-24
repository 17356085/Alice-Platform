/** Composable: fetch platform health from /health endpoint. */
import { ref, onMounted } from 'vue'

interface HealthComponent {
  status: string
  [key: string]: any
}

interface HealthData {
  status: string
  components: Record<string, HealthComponent>
}

export function useHealth() {
  const health = ref<HealthData | null>(null)
  const loading = ref(false)
  const error = ref('')

  async function fetch() {
    loading.value = true
    error.value = ''
    try {
      const resp = await fetch('/api/../health')  // relative to backend proxy
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
      health.value = await resp.json()
    } catch (e: any) {
      // Fallback: try direct backend
      try {
        const resp = await fetch('http://localhost:8000/health')
        if (resp.ok) health.value = await resp.json()
        else error.value = e.message
      } catch {
        error.value = e.message
      }
    } finally {
      loading.value = false
    }
  }

  onMounted(fetch)

  return { health, loading, error, refresh: fetch }
}
