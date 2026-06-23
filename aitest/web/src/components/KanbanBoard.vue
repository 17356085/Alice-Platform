<script setup lang="ts">
import { ref } from 'vue'
import { useKanbanStore } from '@/stores/kanban'

const store = useKanbanStore()
const props = defineProps<{
  columns: Record<string, [string, any][]>
  running?: Set<string>
}>()
const emit = defineEmits<{ 'card-move': [mod: string, from: string, to: string]; 'card-click': [mod: string, info: any]; 'card-run': [mod: string] }>()

const dragMod = ref(''); const dragFrom = ref(''); const dragOverCol = ref('')

const colBg: Record<string, string> = {
  'Project Init': 'bg-slate-50/50 dark:bg-slate-950/20',
  'Requirement': 'bg-blue-50/50 dark:bg-blue-950/20',
  'Test Design': 'bg-indigo-50/50 dark:bg-indigo-950/20',
  'Automation': 'bg-amber-50/50 dark:bg-amber-950/20',
  'Execute & Debug': 'bg-purple-50/50 dark:bg-purple-950/20',
  'Bug Analysis': 'bg-red-50/50 dark:bg-red-950/20',
  'Data Sanitization': 'bg-teal-50/50 dark:bg-teal-950/20',
  'Report': 'bg-emerald-50/50 dark:bg-emerald-950/20',
  'Knowledge': 'bg-cyan-50/50 dark:bg-cyan-950/20',
}

function onDragStart(e: DragEvent, mod: string, stage: string) {
  dragMod.value = mod; dragFrom.value = stage
  ;(e.target as HTMLElement).classList.add('scale-95', 'opacity-40', 'rotate-1', 'shadow-xl')
  e.dataTransfer!.effectAllowed = 'move'
}
function onDragEnd(e: DragEvent) { (e.target as HTMLElement).classList.remove('scale-95', 'opacity-40', 'rotate-1', 'shadow-xl'); dragOverCol.value = '' }
function onDrop(stage: string) {
  dragOverCol.value = ''
  if (dragMod.value && dragFrom.value !== stage) {
    emit('card-move', dragMod.value, dragFrom.value, stage)
    ;(window as any).__tlo_toast?.add(`${dragMod.value}: ${dragFrom.value} → ${stage}`, 'success')
  }
  dragMod.value = ''; dragFrom.value = ''
}
</script>

<template>
  <div class="flex gap-3 overflow-x-auto pb-3 min-h-[calc(100vh-180px)]" style="scroll-snap-type:x mandatory">
    <div v-for="col in store.SOP_COLS" :key="col.key"
      :class="['rounded-2xl p-2.5 flex flex-col gap-2 transition-all duration-300 border-2 flex-shrink-0 w-[170px]',
        dragOverCol === col.key ? 'scale-[1.02] border-dashed border-ring shadow-lg ' + (colBg[col.key]||'') : 'border-transparent ' + (colBg[col.key]||'')]"
      @dragover.prevent="dragOverCol = col.key"
      @dragleave.prevent="dragOverCol = dragOverCol === col.key ? '' : dragOverCol"
      @drop.prevent="onDrop(col.key)"
    >
      <!-- Column header -->
      <div class="flex items-center gap-2 px-1.5">
        <span class="text-sm">{{ col.icon }}</span>
        <span class="text-[11px] font-bold uppercase tracking-widest text-muted-foreground">{{ col.label }}</span>
        <span class="text-[9px] text-muted-foreground/40 hidden xl:inline">{{ col.phases.join(', ') }}</span>
        <span class="ml-auto glass-card !rounded-full !px-2 !py-0.5 text-[10px] font-bold shadow-sm">{{ (columns[col.key] || []).length }}</span>
      </div>

      <!-- Cards -->
      <div
        v-for="[mod, info] in (columns[col.key] || [])" :key="mod"
        draggable="true"
        @dragstart="onDragStart($event, mod, col.key)"
        @dragend="onDragEnd"
        @click="emit('card-click', mod, info)"
        class="glass-card !rounded-lg p-2.5 cursor-grab active:cursor-grabbing select-none transition-all duration-200 group"
      >
        <!-- Module name + status -->
        <div class="flex items-start justify-between mb-2">
          <div class="flex items-center gap-1.5 min-w-0">
            <span class="font-semibold text-[13px] truncate">{{ mod }}</span>
            <span v-if="running?.has(mod)" class="badge badge-info text-[9px] animate-pulse">LIVE</span>
          </div>
          <div class="flex items-center gap-1 flex-shrink-0">
            <span v-if="running?.has(mod)" class="w-2 h-2 rounded-full bg-success animate-pulse" />
            <span v-else-if="info.failed" class="w-2 h-2 rounded-full bg-destructive" title="Has failures" />
          </div>
        </div>

        <!-- SOP phase dots -->
        <div class="flex gap-px mb-2">
          <span v-for="(ok, phase) in (info.phase_status || {})" :key="phase"
            :class="['w-1 h-1 rounded-full flex-shrink-0', ok ? 'bg-success' : 'bg-muted-foreground/15']"
            :title="phase + (ok ? ' ✅' : '')" />
        </div>
        <div class="flex flex-wrap gap-x-2 gap-y-0.5 text-[10px] text-muted-foreground mb-2">
          <span>📄{{ info.pages }}</span>
          <span>📦{{ info.artifacts || 0 }}</span>
          <span class="font-mono">{{ info.phases_done }}/{{ info.phases_total }}</span>
        </div>

        <!-- Progress bar -->
        <div class="h-1.5 bg-muted/50 rounded-full overflow-hidden">
          <div
            :class="['h-full rounded-full transition-all duration-1000 ease-out',
              col.key === 'complete' ? '!bg-success' : col.key === 'execution' ? '!bg-primary' : '!bg-primary/60']"
            :style="{ width: running?.has(mod) && info.progress ? `${info.progress}%` : `${info.phases_done / info.phases_total * 100}%`,
              background: running?.has(mod) ? 'var(--primary-gradient)' : '' }"
          />
        </div>
        <div v-if="running?.has(mod) && info.current_phase" class="text-[10px] text-muted-foreground mt-1 truncate">▶️ {{ info.current_phase }}</div>
        <div v-else class="text-[10px] text-muted-foreground mt-1 truncate">{{ info.note || (col.key === 'complete' ? '✅ 完成' : info.phases_done + ' phases done') }}</div>

        <!-- Hover action -->
        <div v-if="!running?.has(mod)" class="flex gap-1.5 mt-3 pt-2.5 opacity-0 group-hover:opacity-100 transition-opacity" style="border-top:1px solid var(--border)">
          <button @click.stop="emit('card-run', mod)"
            class="flex-1 px-2.5 py-1.5 rounded-md text-[11px] font-semibold cursor-pointer transition-all border-none"
            style="background:var(--primary-gradient); color:var(--primary-foreground)">▶️ Run SOP</button>
        </div>
      </div>

      <div v-if="!(columns[col.key] || []).length" class="py-8 text-center text-muted-foreground/30 text-xs italic">Drop here</div>
    </div>
  </div>
</template>
