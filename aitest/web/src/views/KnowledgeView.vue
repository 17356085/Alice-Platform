<script setup lang="ts">
import { ref, onMounted } from 'vue'

const rag = ref<any>({})

onMounted(async () => {
  try {
    const res = await fetch('/health')
    rag.value = (await res.json()).components?.rag || {}
  } catch { rag.value = {} }
})
</script>

<template>
  <div class="grid grid-cols-3 gap-3.5">
    <div class="card bg-card border border-border rounded-lg">
      <div class="px-4 py-3 border-b border-border font-semibold text-[13px]">📚 Collections</div>
      <div class="p-4 text-center">
        <div class="text-[28px] font-bold text-primary">{{ rag.collections || '—' }}</div>
        <div class="text-[11px] text-muted-foreground mt-1">ChromaDB</div>
      </div>
    </div>
    <div class="card bg-card border border-border rounded-lg">
      <div class="px-4 py-3 border-b border-border font-semibold text-[13px]">📄 Documents</div>
      <div class="p-4 text-center">
        <div class="text-[28px] font-bold">{{ rag.total_docs || '—' }}</div>
        <div class="text-[11px] text-muted-foreground mt-1">indexed</div>
      </div>
    </div>
    <div class="card bg-card border border-border rounded-lg">
      <div class="px-4 py-3 border-b border-border font-semibold text-[13px]">🟢 Status</div>
      <div class="p-4 text-center">
        <div class="text-[28px] font-bold text-success">{{ rag.status || '—' }}</div>
        <div class="text-[11px] text-muted-foreground mt-1">{{ rag.names?.join(', ') || '' }}</div>
      </div>
    </div>
  </div>
</template>
