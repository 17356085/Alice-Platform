<script setup lang="ts">
import { ref, watch } from 'vue'
import { Play, FileText, X } from 'lucide-vue-next'

const props = defineProps<{
  module: string
  info: { status: string; phases_done: number; phases_total: number; pages: number; failed: number; updated: string; progress?: number; current_phase?: string } | null
  open: boolean
  running?: boolean
}>()
const emit = defineEmits<{ close: []; run: [mod: string]; report: [mod: string] }>()
const visible = ref(false)
watch(() => props.open, (v) => { if (v) setTimeout(() => visible.value = true, 50); else visible.value = false })
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="fixed inset-0 bg-black/30 z-40 transition-opacity" :class="visible ? 'opacity-100' : 'opacity-0'" @click="emit('close')" />
    <div v-if="open" class="fixed right-0 top-0 h-full w-[420px] bg-card border-l border-border shadow-xl z-50 transition-transform duration-300 flex flex-col" :class="visible ? 'translate-x-0' : 'translate-x-full'">
      <div class="flex items-center justify-between px-5 py-4 border-b border-border">
        <div>
          <h2 class="text-base font-semibold">{{ module }}</h2>
          <span v-if="info" :class="['badge text-xs mt-1', info.status === 'completed' ? 'badge-ok' : info.status === 'completed_with_issues' ? 'badge-warn' : 'badge-info']">
            {{ info.status === 'completed' ? '✅ Complete' : info.status === 'completed_with_issues' ? '⚠️ Issues' : info.status === 'ready' ? '📝 Ready' : '⏳ Pending' }}
          </span>
        </div>
        <button @click="emit('close')" class="text-muted-foreground hover:text-foreground cursor-pointer border-none bg-none"><X :size="20" /></button>
      </div>

      <div class="flex-1 overflow-y-auto p-5 space-y-4" v-if="info">
        <div class="glass-card !rounded-lg p-4">
          <h3 class="text-xs font-semibold text-muted-foreground mb-3 flex items-center gap-1.5"><FileText :size="13" /> Lifecycle Progress</h3>
          <div class="flex items-center gap-1">
            <div v-for="i in (info.phases_total || 9)" :key="i"
              :class="['flex-1 h-2 rounded-full transition-all', i <= info.phases_done ? (info.status === 'completed' ? 'bg-success' : 'bg-warning') : 'bg-muted']" />
          </div>
          <div class="text-xs text-muted-foreground mt-2 text-center">{{ info.phases_done }}/{{ info.phases_total || 9 }} phases</div>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div class="glass-card !rounded-lg p-3 text-center">
            <div class="text-2xl font-bold text-info">{{ info.pages }}</div>
            <div class="text-[11px] text-muted-foreground">Pages</div>
          </div>
          <div class="glass-card !rounded-lg p-3 text-center">
            <div class="text-2xl font-bold" :class="info.failed ? 'text-destructive' : 'text-success'">{{ info.failed || 0 }}</div>
            <div class="text-[11px] text-muted-foreground">Failed</div>
          </div>
        </div>
        <div class="text-xs text-muted-foreground space-y-1">
          <div>📅 Updated: {{ info.updated || 'N/A' }}</div>
          <div>📌 Status: {{ info.status }}</div>
        </div>
      </div>

      <div v-if="running && info?.current_phase" class="px-5 py-2 bg-accent/50 border-t border-border flex items-center gap-2 text-xs">
        <span class="dot-live" />
        <span class="font-semibold text-primary">{{ info.current_phase }}</span>
        <span class="text-muted-foreground">{{ info.progress || 0 }}%</span>
      </div>

      <div class="flex gap-2 p-4 border-t border-border">
        <button @click="emit('run', module)" :disabled="running"
          :class="['flex-1 flex items-center justify-center gap-1.5 px-4 py-2.5 border-none rounded-md text-[13px] font-semibold cursor-pointer font-sans transition-all',
            running ? 'bg-muted text-muted-foreground cursor-not-allowed' : 'btn-primary']">
          <Play :size="14" :stroke-width="3" /> {{ running ? 'Running...' : 'Run SOP' }}
        </button>
        <button @click="emit('report', module)" class="btn-outline flex items-center gap-1.5 text-[13px]">
          <FileText :size="14" :stroke-width="2" /> Report
        </button>
      </div>
    </div>
  </Teleport>
</template>
