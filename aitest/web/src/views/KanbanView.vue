<script setup lang="ts">
import { onMounted } from 'vue'
import { useKanbanStore } from '@/stores/kanban'
import { useKanbanWS } from '@/composables/useKanbanWS'
import KanbanBoard from '@/components/KanbanBoard.vue'

const store = useKanbanStore()
const { sendCardMove } = useKanbanWS()

onMounted(() => store.fetchModules())

function onCardMove(mod: string, from: string, to: string) {
  store.moveCard(mod, to)
  sendCardMove(mod, from, to)
  fetch('/api/sop-status', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ module: mod, stage: to }),
  }).catch(() => {})
}
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-4">
      <span class="text-xs text-muted-foreground" v-if="!store.loading">
        {{ new Date().toLocaleTimeString('zh-CN') }}
      </span>
      <button
        @click="store.fetchModules()"
        class="px-4 py-1.5 rounded-md border border-border bg-card text-[13px] cursor-pointer hover:border-ring hover:text-primary font-sans"
      >
        🔄 刷新
      </button>
    </div>
    <div v-if="store.loading" class="text-center py-12 text-muted-foreground">加载中...</div>
    <div v-else-if="store.error" class="text-center py-12 text-destructive">{{ store.error }}</div>
    <KanbanBoard v-else :columns="store.columns" @card-move="onCardMove" />
  </div>
</template>
