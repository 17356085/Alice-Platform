<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  module: string
  info: { status: string; phases: number; pages: number; failed: number; updated: string } | null
  open: boolean
}>()

const emit = defineEmits<{ close: []; run: [mod: string]; report: [mod: string] }>()

const visible = ref(false)

watch(() => props.open, (v) => {
  if (v) setTimeout(() => visible.value = true, 50)
  else visible.value = false
})

function stageLabel(s: string) {
  const m: Record<string, string> = {
    completed: '✅ 完成', completed_with_issues: '⚠️ 有问题',
    ready: '📝 就绪', in_progress: '▶️ 执行中', pending: '⏳ 待开始'
  }
  return m[s] || s
}

function stageBadge(s: string) {
  if (s === 'completed') return 'badge-ok'
  if (s === 'completed_with_issues') return 'badge-warn'
  return 'badge-info'
}
</script>

<template>
  <Teleport to="body">
    <!-- Backdrop -->
    <div
      v-if="open"
      class="fixed inset-0 bg-black/30 z-40 transition-opacity"
      :class="visible ? 'opacity-100' : 'opacity-0'"
      @click="emit('close')"
    />
    <!-- Sheet -->
    <div
      v-if="open"
      class="fixed right-0 top-0 h-full w-[420px] bg-card border-l border-border shadow-xl z-50 transition-transform duration-300 flex flex-col"
      :class="visible ? 'translate-x-0' : 'translate-x-full'"
    >
      <!-- Header -->
      <div class="flex items-center justify-between px-5 py-4 border-b border-border">
        <div>
          <h2 class="text-base font-semibold">{{ module }}</h2>
          <span v-if="info" :class="['badge text-xs mt-1', stageBadge(info.status)]">
            {{ stageLabel(info.status) }}
          </span>
        </div>
        <button @click="emit('close')" class="text-muted-foreground hover:text-foreground text-lg cursor-pointer border-none bg-none">&times;</button>
      </div>

      <!-- Body -->
      <div class="flex-1 overflow-y-auto p-5 space-y-4" v-if="info">
        <!-- Progress -->
        <div class="card rounded-lg border border-border bg-background p-4">
          <h3 class="text-xs font-semibold text-muted-foreground mb-3">Lifecycle Progress</h3>
          <div class="flex items-center gap-1">
            <div
              v-for="i in 9" :key="i"
              :class="[
                'flex-1 h-2 rounded-full transition-all',
                i <= info.phases ? (info.status === 'completed' ? 'bg-success' : info.status === 'completed_with_issues' ? 'bg-warning' : 'bg-info') : 'bg-muted'
              ]"
            />
          </div>
          <div class="text-xs text-muted-foreground mt-2 text-center">{{ info.phases }}/9 phases</div>
        </div>

        <!-- Stats -->
        <div class="grid grid-cols-2 gap-3">
          <div class="card rounded-lg border border-border bg-background p-3 text-center">
            <div class="text-2xl font-bold text-info">{{ info.pages }}</div>
            <div class="text-[11px] text-muted-foreground">Pages</div>
          </div>
          <div class="card rounded-lg border border-border bg-background p-3 text-center">
            <div class="text-2xl font-bold" :class="info.failed ? 'text-destructive' : 'text-success'">{{ info.failed || 0 }}</div>
            <div class="text-[11px] text-muted-foreground">Failed</div>
          </div>
        </div>

        <!-- Meta -->
        <div class="text-xs text-muted-foreground space-y-1">
          <div>📅 Updated: {{ info.updated || 'N/A' }}</div>
          <div>📌 Status: {{ info.status }}</div>
        </div>
      </div>

      <!-- Footer actions -->
      <div class="flex gap-2 p-4 border-t border-border">
        <button @click="emit('run', module)" class="flex-1 px-4 py-2.5 bg-primary text-primary-foreground border-none rounded-md text-[13px] font-semibold cursor-pointer font-sans hover:opacity-90 transition-opacity">
          ▶️ Run SOP
        </button>
        <button @click="emit('report', module)" class="px-4 py-2.5 border border-border bg-card text-foreground rounded-md text-[13px] cursor-pointer font-sans hover:border-ring transition-colors">
          📊 Report
        </button>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.badge { display:inline-block; padding:2px 8px; border-radius:9999px; font-weight:600; }
.badge-ok { background:var(--success-light); color:var(--success); }
.badge-warn { background:var(--warning-light); color:var(--warning); }
.badge-info { background:var(--info-light); color:var(--info); }
</style>
