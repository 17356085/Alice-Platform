<script setup lang="ts">
import { onMounted } from 'vue'
import { useGapScanner } from '@/composables/useGapScanner'

const { gaps, scanning, progress, stats, GAP_TYPES, selectedType, showDismissed, scan, dismissGap, dismissAll, convertToTask } = useGapScanner()

onMounted(scan)

const sevBadge: Record<string, string> = { critical: 'badge-err', high: 'badge-warn', medium: 'badge-info', low: '' }
const sevLabel: Record<string, string> = { critical: 'P0', high: 'P1', medium: 'P2', low: 'P3' }
const typeIcon: Record<string, string> = Object.fromEntries(GAP_TYPES.map(t => [t.id, t.icon]))
</script>

<template>
  <div>
    <!-- Header -->
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-3">
        <h2 class="text-base font-semibold">🔍 Test Gap Discovery</h2>
        <span v-if="!scanning" class="text-xs text-muted-foreground">
          {{ stats.total }} gaps · {{ stats.critical }} critical · {{ stats.high }} high
        </span>
      </div>
      <div class="flex gap-2">
        <button @click="dismissAll" class="px-3 py-1.5 text-xs border border-border rounded-md hover:border-warning cursor-pointer font-sans" :disabled="gaps.length === 0">
          Dismiss All
        </button>
        <button @click="scan" class="px-3 py-1.5 text-xs bg-primary text-primary-foreground rounded-md border-none cursor-pointer font-sans hover:opacity-90" :disabled="scanning">
          {{ scanning ? '⏳ Scanning...' : '🔄 Rescan' }}
        </button>
      </div>
    </div>

    <!-- Type filters -->
    <div class="flex gap-1.5 mb-4 flex-wrap">
      <button
        v-for="t in [{id:'all',label:'All',icon:'📋'}, ...GAP_TYPES]"
        :key="t.id"
        @click="selectedType = t.id"
        :class="['px-2.5 py-1 rounded-full text-[11px] cursor-pointer border transition-colors font-sans',
          selectedType === t.id ? 'border-primary bg-primary/10 text-primary' : 'border-border text-muted-foreground hover:border-ring']"
      >
        {{ t.icon }} {{ t.label }}
        <span v-if="t.id !== 'all'" class="ml-1 opacity-50">{{ (stats.byType as any)[t.id] || 0 }}</span>
      </button>
    </div>

    <!-- Progress / Empty / Grid -->
    <div v-if="scanning" class="bg-card border border-border rounded-xl p-8 text-center space-y-3">
      <div class="animate-pulse text-2xl">🔍</div>
      <div class="text-sm text-muted-foreground font-mono">{{ progress }}</div>
      <div class="h-1 bg-muted rounded-full overflow-hidden max-w-md mx-auto">
        <div class="h-full bg-primary rounded-full animate-pulse" style="width:60%" />
      </div>
    </div>

    <div v-else-if="gaps.length === 0" class="bg-card border border-border rounded-xl p-12 text-center text-muted-foreground">
      <div class="text-3xl mb-3">✅</div>
      <div class="font-semibold">No gaps found</div>
      <div class="text-xs mt-1">All modules have adequate test coverage.</div>
    </div>

    <div v-else class="grid grid-cols-2 gap-3 max-lg:grid-cols-1">
      <div
        v-for="gap in gaps" :key="gap.id"
        class="card bg-card border border-border rounded-lg p-4 hover:shadow-md transition-all group cursor-pointer"
      >
        <div class="flex items-start gap-2.5 mb-2">
          <span class="text-lg">{{ typeIcon[gap.type] || '📌' }}</span>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2">
              <span :class="['badge text-[10px]', sevBadge[gap.severity] || '']">{{ sevLabel[gap.severity] }}</span>
              <span class="text-xs text-muted-foreground font-mono">{{ gap.module }}</span>
            </div>
            <div class="text-[13px] font-semibold mt-1 truncate">{{ gap.title }}</div>
          </div>
        </div>
        <p class="text-xs text-muted-foreground mb-3 line-clamp-2">{{ gap.description }}</p>
        <div class="flex gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
          <button @click.stop="convertToTask(gap.id)" class="px-2.5 py-1 text-[11px] bg-primary text-primary-foreground rounded border-none cursor-pointer font-sans">Create Task</button>
          <button @click.stop="dismissGap(gap.id)" class="px-2.5 py-1 text-[11px] border border-border rounded hover:border-destructive cursor-pointer font-sans">Dismiss</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.badge { display:inline-block; padding:1px 6px; border-radius:9999px; font-weight:600; }
.badge-err { background:var(--destructive-light); color:var(--destructive); }
.badge-warn { background:var(--warning-light); color:var(--warning); }
.badge-info { background:var(--info-light); color:var(--info); }
.line-clamp-2 { display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }
</style>
