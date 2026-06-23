<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{
  columns: Record<string, [string, { status: string; phases: number; pages: number }][]>
}>()

const emit = defineEmits<{ 'card-move': [mod: string, from: string, to: string] }>()

const dragMod = ref('')
const dragFrom = ref('')
const dragOverCol = ref('')

const colDefs: [string, string, string][] = [
  ['⏳ Pending', 'pending', '待开始'],
  ['📝 Planning', 'planning', '策略制定中'],
  ['▶️ Executing', 'executing', '执行中'],
  ['🔍 Analyzing', 'analyzing', '失败分析/QA Loop'],
  ['✅ Completed', 'completed', '报告已生成'],
]

function onDragStart(e: DragEvent, mod: string, stage: string) {
  dragMod.value = mod
  dragFrom.value = stage
  ;(e.target as HTMLElement)?.classList.add('opacity-40')
  e.dataTransfer!.effectAllowed = 'move'
}

function onDragEnd(e: DragEvent) {
  ;(e.target as HTMLElement)?.classList.remove('opacity-40')
  dragOverCol.value = ''
}

function onDrop(stage: string) {
  dragOverCol.value = ''
  if (dragMod.value && dragFrom.value !== stage) {
    emit('card-move', dragMod.value, dragFrom.value, stage)
  }
  dragMod.value = ''
  dragFrom.value = ''
}
</script>

<template>
  <div class="grid grid-cols-5 gap-3.5 min-h-[calc(100vh-140px)] max-lg:grid-cols-3 max-md:grid-cols-1">
    <div
      v-for="[title, key, desc] in colDefs"
      :key="key"
      :class="[
        'bg-muted rounded-lg p-3 flex flex-col gap-2.5 transition-colors',
        dragOverCol === key ? '!bg-accent border-2 border-dashed border-ring' : ''
      ]"
      @dragover.prevent="dragOverCol = key"
      @dragleave="dragOverCol = dragOverCol === key ? '' : dragOverCol"
      @drop.prevent="onDrop(key)"
    >
      <div class="text-xs font-bold uppercase tracking-wide text-muted-foreground px-1.5 py-1 flex items-center gap-1.5">
        {{ title }}
        <span class="ml-auto bg-card px-1.5 py-px rounded-full text-[11px]">{{ columns[key]?.length || 0 }}</span>
      </div>

      <!-- Cards -->
      <div
        v-for="[mod, info] in columns[key] || []"
        :key="mod"
        draggable="true"
        @dragstart="onDragStart($event, mod, key)"
        @dragend="onDragEnd"
        class="bg-card border border-border rounded-md p-3 cursor-grab active:cursor-grabbing hover:border-ring transition-all"
      >
        <div class="font-semibold text-[13px] mb-1.5">{{ mod }}</div>
        <div class="text-[11px] text-muted-foreground flex gap-2">
          <span>📄 {{ info.pages || 0 }} pages</span>
          <span>🔧 {{ info.phases || 0 }}/9</span>
        </div>
        <div class="mt-2 h-1 bg-muted rounded-sm overflow-hidden">
          <div
            :class="[
              'h-full rounded-sm transition-all',
              key === 'completed' ? 'bg-success' : key === 'analyzing' ? 'bg-warning' : 'bg-info'
            ]"
            :style="{ width: `${(info.phases || 0) / 9 * 100}%` }"
          />
        </div>
        <div class="text-[10px] text-muted-foreground mt-1">
          {{ key === 'completed' ? '✅ 完成' : key === 'analyzing' ? '⚠️ 有问题' : key === 'planning' ? '📝 就绪' : key === 'executing' ? '▶️ 执行中' : '⏳ 待开始' }}
        </div>
      </div>

      <div v-if="!columns[key]?.length" class="py-4 text-center text-muted-foreground text-xs">— 空 —</div>
    </div>
  </div>
</template>
