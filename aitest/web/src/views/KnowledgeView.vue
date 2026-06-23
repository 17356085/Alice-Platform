<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
const { t } = useI18n()
const rag = ref<any>({})
onMounted(async () => { try { const r = await fetch('/health'); rag.value = (await r.json()).components?.rag || {} } catch { rag.value = {} } })
</script>
<template>
  <div>
    <h2 class="text-base font-semibold mb-5">{{ t('knowledge.title') }}</h2>
    <div class="grid grid-cols-3 gap-4">
      <div class="glass-card p-5 text-center">
        <div class="text-[28px] font-bold" style="color:var(--primary)">{{ rag.collections || '—' }}</div>
        <div class="text-xs text-muted-foreground mt-1">{{ t('knowledge.collections') }}</div>
      </div>
      <div class="glass-card p-5 text-center">
        <div class="text-[28px] font-bold">{{ rag.total_docs || '—' }}</div>
        <div class="text-xs text-muted-foreground mt-1">{{ t('knowledge.documents') }}</div>
      </div>
      <div class="glass-card p-5 text-center">
        <div class="text-[28px] font-bold text-success">{{ rag.status || '—' }}</div>
        <div class="text-xs text-muted-foreground mt-1">{{ t('knowledge.status') }}</div>
      </div>
    </div>
  </div>
</template>
