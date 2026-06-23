<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{
  columns: Record<string, [string, { status: string; phases: number; pages: number; failed: number; updated: string }][]>
}>()

const emit = defineEmits<{
  'card-move': [mod: string, from: string, to: string]
  'card-click': [mod: string, info: any]
}>()

const dragMod = ref('')
const dragFrom = ref('')
const dragOverCol = ref('')
const draggedEl = ref<HTMLElement | null>(null)

const colDefs: [string, string, string][] = [
  ['⏳ Pending', 'pending', '模块待测试'],
  ['📝 Planning', 'planning', '策略制定中'],
  ['▶️ Executing', 'executing', 'Agent 执行中'],
  ['🔍 Analyzing', 'analyzing', 'QA Loop 分析'],
  ['✅ Completed', 'completed', '报告已生成'],
]

function onDragStart(e: DragEvent, mod: string, stage: string) {
  dragMod.value = mod
  dragFrom.value = stage
  draggedEl.value = e.target as HTMLElement
  draggedEl.value?.classList.add('scale-95', 'opacity-50', 'rotate-1', 'shadow-lg')
  e.dataTransfer!.effectAllowed = 'move'
}

function onDragEnd() {
  draggedEl.value?.classList.remove('scale-95', 'opacity-50', 'rotate-1', 'shadow-lg')
  draggedEl.value = null
  dragOverCol.value = ''
}

function onDrop(stage: string) {
  dragOverCol.value = ''
  if (dragMod.value && dragFrom.value !== stage) {
    emit('card-move', dragMod.value, dragFrom.value, stage)
    ;(window as any).__tlo_toast?.add(
      `${dragMod.value}: ${dragFrom.value} → ${stage}`,
      'success'
    )
  }
  dragMod.value = ''
  dragFrom.value = ''
}
</script>

<template>
  <div class="grid grid-cols-5 gap-3.5 min-h-[calc(100vh-160px)] max-lg:grid-cols-3 max-md:grid-cols-1">
    <div
      v-for="[title, key, desc] in colDefs"
      :key="key"
      :class="[
        'rounded-xl p-3 flex flex-col gap-2.5 transition-all duration-200',
        dragOverCol === key
          ? 'bg-accent/50 scale-[1.02] border-2 border-dashed border-ring shadow-lg'
          : 'bg-muted/70 border-2 border-transparent'
      ]"
      @dragover.prevent="dragOverCol = key"
      @dragleave.prevent="dragOverCol = dragOverCol === key ? '' : dragOverCol"
      @drop.prevent="onDrop(key)"
    >
      <div class="text-[11px] font-bold uppercase tracking-wider text-muted-foreground px-1.5 py-1 flex items-center gap-1.5">
        {{ title }}
        <span class="text-[10px] text-muted-foreground/50 hidden sm:inline">{{ desc }}</span>
        <span class="ml-auto bg-card border border-border px-1.5 py-px rounded-full text-[11px] font-semibold shadow-sm">
          {{ columns[key]?.length || 0 }}
        </span>
      </div>

      <div
        v-for="[mod, info] in columns[key] || []"
        :key="mod"
        draggable="true"
        @dragstart="onDragStart($event, mod, key)"
        @dragend="onDragEnd"
        @click="emit('card-click', mod, info)"
        class="bg-card border border-border rounded-lg p-3.5 cursor-grab active:cursor-grabbing
               hover:border-ring hover:shadow-md hover:-translate-y-0.5
               transition-all duration-200 select-none"
      >
        <div class="font-semibold text-[13px] mb-2 flex items-center gap-1.5">
          {{ mod }}
          <span v-if="info.failed" class="ml-auto w-1.5 h-1.5 rounded-full bg-destructive" title="Has failures" />
        </div>

        <div class="text-[11px] text-muted-foreground flex gap-3 mb-2.5">
          <span>📄 {{ info.pages || 0 }}p</span>
          <span>🔧 {{ info.phases }}/9</span>
        </div>

        <div class="h-1.5 bg-muted rounded-full overflow-hidden">
          <div
            :class="[
              'h-full rounded-full transition-all duration-700 ease-out',
              key === 'completed' ? 'bg-success' : key === 'analyzing' ? 'bg-warning' : 'bg-info'
            ]"
            :style="{ width: `${(info.phases || 0) / 9 * 100}%` }"
          />
        </div>
      </div>

      <div v-if="!columns[key]?.length" class="py-6 text-center text-muted-foreground/40 text-xs italic">
        Drop modules here
      </div>
    </div>
  </div>
</template>
