<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useKanbanStore } from '@/stores/kanban'
import { useKanbanWS } from '@/composables/useKanbanWS'
import KanbanBoard from '@/components/KanbanBoard.vue'
import ModuleDetailSheet from '@/components/ModuleDetailSheet.vue'

const store = useKanbanStore()
const { sendCardMove } = useKanbanWS()

const selectedMod = ref('')
const selectedInfo = ref<any>(null)
const sheetOpen = ref(false)

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

function onCardClick(mod: string, info: any) {
  selectedMod.value = mod
  selectedInfo.value = info
  sheetOpen.value = true
}

function onRun(mod: string) {
  ;(window as any).__tlo_toast?.add(`Starting SOP: ${mod}...`, 'info')
}
function onReport(mod: string) {
  ;(window as any).__tlo_toast?.add(`Generating report for: ${mod}`, 'info')
}
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-4">
      <span class="text-xs text-muted-foreground">
        {{ store.totalModules }} modules · {{ new Date().toLocaleTimeString('zh-CN') }}
      </span>
      <button
        @click="store.fetchModules()"
        class="px-4 py-1.5 rounded-md border border-border bg-card text-[13px] cursor-pointer hover:border-ring hover:text-primary font-sans transition-colors"
      >
        🔄 刷新
      </button>
    </div>

    <div v-if="store.loading" class="grid grid-cols-5 gap-3.5">
      <div v-for="i in 5" :key="i" class="bg-muted/50 rounded-xl p-3 animate-pulse h-[200px]" />
    </div>
    <div v-else-if="store.error" class="text-center py-12 text-destructive">{{ store.error }}</div>
    <KanbanBoard v-else :columns="store.columns" @card-move="onCardMove" @card-click="onCardClick" />

    <ModuleDetailSheet
      :module="selectedMod"
      :info="selectedInfo"
      :open="sheetOpen"
      @close="sheetOpen = false"
      @run="onRun"
      @report="onReport"
    />
  </div>
</template>
