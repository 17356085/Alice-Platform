<script setup lang="ts">
import { ref, onMounted } from 'vue'

const runs = ref<any[]>([])
const loading = ref(false)

async function loadRuns() {
  loading.value = true
  try {
    const res = await fetch('/api/trace/runs?limit=5')
    runs.value = (await res.json()).runs || []
  } catch { runs.value = [] }
  loading.value = false
}

onMounted(loadRuns)
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-4">
      <span class="text-xs text-muted-foreground">Agent 执行日志</span>
      <button @click="loadRuns" class="px-4 py-1.5 rounded-md border border-border bg-card text-[13px] cursor-pointer hover:border-ring font-sans">🔄 刷新</button>
    </div>
    <div class="card bg-card border border-border rounded-lg">
      <div class="px-4 py-3 border-b border-border font-semibold text-[13px]">📡 最近执行</div>
      <div class="p-4">
        <div v-if="loading" class="text-center text-muted-foreground">加载中...</div>
        <div v-else-if="!runs.length" class="py-8 text-center text-muted-foreground">
          无执行记录。运行 <code class="bg-muted px-1 rounded">aitest sop run</code> 产生数据。
        </div>
        <div v-else class="space-y-2">
          <div v-for="r in runs" :key="r.run_id" class="text-xs font-mono py-1 border-b border-border text-muted-foreground">
            <span class="mr-3">{{ r.timestamp || '' }}</span>
            <span>Run: {{ r.run_id }} — {{ r.event_count || 0 }} events</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
