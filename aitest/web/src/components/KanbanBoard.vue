<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{
  columns: Record<string, [string, { status: string; phases: number; pages: number; failed: number; updated: string; progress?: number; current_phase?: string }][]>
  running?: Set<string>
}>()
const emit = defineEmits<{ 'card-move': [mod: string, from: string, to: string]; 'card-click': [mod: string, info: any]; 'card-run': [mod: string] }>()

const dragMod = ref(''); const dragFrom = ref(''); const dragOverCol = ref('')

const colDefs: [string, string, string, string][] = [
  ['⏳', 'pending', 'Pending', 'bg-muted/50'], ['📝', 'planning', 'Planning', 'bg-blue-50/50 dark:bg-blue-950/20'],
  ['▶️', 'executing', 'Executing', 'bg-amber-50/50 dark:bg-amber-950/20'], ['🔍', 'analyzing', 'Analyzing', 'bg-red-50/50 dark:bg-red-950/20'],
  ['✅', 'completed', 'Completed', 'bg-emerald-50/50 dark:bg-emerald-950/20'],
]

function onDragStart(e: DragEvent, mod: string, stage: string) {
  dragMod.value = mod; dragFrom.value = stage
  const el = e.target as HTMLElement
  el.classList.add('scale-95', 'opacity-40', 'rotate-1', 'shadow-xl')
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
  <div class="grid grid-cols-5 gap-4 min-h-[calc(100vh-180px)] max-lg:grid-cols-3 max-md:grid-cols-1">
    <div
      v-for="[icon, key, label, bg] in colDefs" :key="key"
      :class="['rounded-2xl p-3.5 flex flex-col gap-2.5 transition-all duration-300 border-2',
        dragOverCol === key ? 'scale-[1.02] border-dashed border-ring shadow-lg ' + bg : 'border-transparent ' + bg]"
      @dragover.prevent="dragOverCol = key"
      @dragleave.prevent="dragOverCol = dragOverCol === key ? '' : dragOverCol"
      @drop.prevent="onDrop(key)"
    >
      <div class="flex items-center gap-2 px-1.5">
        <span class="text-sm">{{ icon }}</span>
        <span class="text-[11px] font-bold uppercase tracking-widest text-muted-foreground">{{ label }}</span>
        <span class="ml-auto glass-card !rounded-full !px-2 !py-0.5 text-[10px] font-bold shadow-sm">{{ columns[key]?.length || 0 }}</span>
      </div>

      <div
        v-for="[mod, info] in columns[key] || []" :key="mod"
        draggable="true"
        @dragstart="onDragStart($event, mod, key)"
        @dragend="onDragEnd"
        @click="emit('card-click', mod, info)"
        class="glass-card !rounded-xl p-4 cursor-grab active:cursor-grabbing select-none transition-all duration-200"
      >
        <div class="flex items-start justify-between mb-2.5">
          <div class="flex items-center gap-1.5 min-w-0">
            <span class="font-semibold text-[13px] truncate">{{ mod }}</span>
            <span v-if="running?.has(mod)" class="badge badge-info text-[9px] animate-pulse">LIVE</span>
          </div>
          <div class="flex items-center gap-1 flex-shrink-0">
            <span v-if="running?.has(mod)" class="w-2 h-2 rounded-full bg-success animate-pulse" title="Running" />
            <span v-else-if="info.failed" class="w-2 h-2 rounded-full bg-destructive" title="Has failures" />
          </div>
        </div>
        <div class="flex gap-3 text-[11px] text-muted-foreground mb-3">
          <span>📄 {{ info.pages }}p</span>
          <span>🔧 {{ info.phases }}/9</span>
        </div>
        <div class="h-1.5 bg-muted/50 rounded-full overflow-hidden">
          <div
            :class="['h-full rounded-full transition-all duration-1000 ease-out',
              key === 'completed' ? '!bg-success' : key === 'analyzing' ? '!bg-warning' : '!bg-primary']"
            :style="{
              width: running?.has(mod) && info.progress ? `${info.progress}%` : `${(info.phases || 0) / 9 * 100}%`,
              background: (running?.has(mod) || key === 'executing') ? 'var(--primary-gradient)' : ''
            }"
          />
        </div>
        <div v-if="running?.has(mod) && info.current_phase" class="text-[10px] text-muted-foreground mt-1 truncate">
          ▶️ {{ info.current_phase }}
        </div>
        <div v-else class="text-[10px] text-muted-foreground mt-1">
          {{ key === 'completed' ? '✅ Done' : key === 'analyzing' ? '⚠️ QA Loop' : key === 'planning' ? '📝 Planning' : key === 'executing' ? '▶️ Running' : '⏳ Pending' }}
        </div>

        <!-- Hover action bar -->
        <div v-if="!running?.has(mod)" class="flex gap-1.5 mt-3 pt-2.5 opacity-0 group-hover:opacity-100 transition-opacity" style="border-top:1px solid var(--border)">
          <button
            @click.stop="emit('card-run', mod)"
            class="flex-1 px-2.5 py-1.5 rounded-md text-[11px] font-semibold cursor-pointer transition-all border-none"
            style="background:var(--primary-gradient); color:var(--primary-foreground)"
          >▶️ Run</button>
          <button
            @click.stop="emit('card-click', mod, info)"
            class="px-2.5 py-1.5 rounded-md text-[11px] cursor-pointer transition-all border"
            style="border-color:var(--border); color:var(--muted-foreground); background:transparent"
          >⋯</button>
        </div>
      </div>

      <div v-if="!columns[key]?.length" class="py-8 text-center text-muted-foreground/30 text-xs italic">Drop here</div>
    </div>
  </div>
</template>
