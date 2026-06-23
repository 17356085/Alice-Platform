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
  fetch('/api/sop-status', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ module: mod, stage: to }) }).catch(() => {})
}
function onCardClick(mod: string, info: any) { selectedMod.value = mod; selectedInfo.value = info; sheetOpen.value = true }
function onRun() { (window as any).__tlo_toast?.add('Starting SOP...', 'info') }
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-5">
      <div>
        <div class="text-xs text-muted-foreground">{{ store.totalModules }} modules</div>
      </div>
      <button @click="store.fetchModules()" class="btn-outline text-xs">🔄 Refresh</button>
    </div>
    <div v-if="store.loading" class="grid grid-cols-5 gap-3.5">
      <div v-for="i in 5" :key="i" class="skeleton h-[200px] rounded-xl" />
    </div>
    <div v-else-if="store.error" class="text-center py-16 text-destructive text-sm">{{ store.error }}</div>
    <KanbanBoard v-else :columns="store.columns" @card-move="onCardMove" @card-click="onCardClick" />
    <ModuleDetailSheet :module="selectedMod" :info="selectedInfo" :open="sheetOpen" @close="sheetOpen = false" @run="onRun" @report="() => {}" />
  </div>
</template>
