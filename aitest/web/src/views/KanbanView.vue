<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useKanbanStore } from '@/stores/kanban'
import { useKanbanWS } from '@/composables/useKanbanWS'
import { RefreshCw } from 'lucide-vue-next'
import KanbanBoard from '@/components/KanbanBoard.vue'
import ModuleDetailSheet from '@/components/ModuleDetailSheet.vue'

const route = useRoute()
const store = useKanbanStore()
const { sendCardMove } = useKanbanWS()
const selectedMod = ref('')
const selectedInfo = ref<any>(null)
const sheetOpen = ref(false)

onMounted(async () => {
  try {
    const pid = (route.query.project as string) || ''
    await store.fetchModules(pid)
  } catch(e) { console.error(e) }
})

function onCardMove(mod: string, from: string, to: string) { store.moveCard(mod, to); sendCardMove(mod, from, to) }
function onCardClick(mod: string, info: any) { selectedMod.value = mod; selectedInfo.value = info; sheetOpen.value = true }
function onRun(mod: string) { store.startSOP(mod) }
function refreshModules() { store.fetchModules((route.query.project as string) || '') }
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-5">
      <div class="flex items-center gap-3">
        <div class="text-xs text-muted-foreground">{{ store.totalModules }} modules</div>
        <div v-if="store.running.size" class="badge badge-info text-[10px] animate-pulse">{{ store.running.size }} running</div>
      </div>
      <button @click="refreshModules" class="btn-outline text-xs flex items-center gap-1.5">
        <RefreshCw :size="13" :stroke-width="2" /> Refresh
      </button>
    </div>
    <div v-if="store.loading" class="flex gap-3 overflow-x-auto">
      <div v-for="i in 9" :key="i" class="skeleton h-[200px] rounded-xl flex-shrink-0 w-[170px]" />
    </div>
    <div v-else-if="store.error" class="text-center py-16 text-destructive text-sm">{{ store.error }}</div>
    <KanbanBoard v-else-if="store.totalModules > 0" :columns="store.columns" :running="store.running" @card-move="onCardMove" @card-click="onCardClick" @card-run="onRun" />
    <div v-else class="text-center py-16 text-muted-foreground text-sm">No modules loaded — check server</div>
    <ModuleDetailSheet v-if="sheetOpen" :module="selectedMod" :info="selectedInfo" :open="sheetOpen" :running="store.running.has(selectedMod)" @close="sheetOpen = false" @run="onRun" @report="() => {}" />
  </div>
</template>
