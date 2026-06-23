<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useGapScanner } from '@/composables/useGapScanner'
const { t } = useI18n()
const { gaps, scanning, progress, stats, GAP_TYPES, selectedType, showDismissed, scan, dismissGap, dismissAll, convertToTask } = useGapScanner()
onMounted(scan)
const sevBadge: Record<string, string> = { critical: 'badge-err', high: 'badge-warn', medium: 'badge-info', low: '' }
const typeIcons: Record<string, string> = { missing_test:'❌', missing_type:'⚠️', low_coverage:'📉', flaky_test:'🔄', untested_component:'🧩' }
const filterTabs = computed(() => [{id:'all',label:t('gaps.types.all'),icon:'📋'}, ...GAP_TYPES.map(tp => ({id:tp.id, label:t('gaps.types.'+tp.id), icon:tp.icon}))])
function statCount(typeId: string) { const b = stats.value.byType as Record<string,number>; return b[typeId] || 0 }
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-5">
      <h2 class="text-base font-semibold">{{ t('gaps.title') }}</h2>
      <div class="flex gap-2">
        <button @click="dismissAll" class="btn-outline text-xs" :disabled="gaps.length === 0">{{ t('gaps.dismiss_all') }}</button>
        <button @click="scan" class="btn-primary text-xs" :disabled="scanning">{{ scanning ? t('gaps.scanning') : t('gaps.rescan') }}</button>
      </div>
    </div>

    <div v-if="!scanning" class="flex gap-1.5 mb-4 flex-wrap">
      <button v-for="t2 in filterTabs" :key="t2.id"
        @click="selectedType = t2.id"
        :class="['px-2.5 py-1 rounded-full text-[11px] cursor-pointer border transition-all font-sans',
          selectedType === t2.id ? 'btn-primary !py-1 !text-[11px]' : 'btn-outline !py-1 !text-[11px]']"
      >{{ t2.icon }} {{ t2.label }}
        <span v-if="t2.id !== 'all'" class="ml-1 opacity-50">{{ statCount(t2.id) }}</span>
      </button>
    </div>

    <div v-if="scanning" class="glass-card p-8 text-center space-y-3">
      <div class="text-2xl animate-pulse">🔍</div>
      <div class="text-sm text-muted-foreground font-mono">{{ progress }}</div>
      <div class="h-1.5 bg-muted rounded-full overflow-hidden max-w-md mx-auto"><div class="h-full rounded-full animate-pulse" style="background:var(--primary-gradient); width:60%" /></div>
    </div>

    <div v-else-if="gaps.length === 0" class="glass-card p-16 text-center text-muted-foreground">
      <div class="text-4xl mb-3">✅</div>
      <div class="font-semibold text-lg">{{ t('gaps.no_gaps') }}</div>
      <div class="text-xs mt-1">{{ t('gaps.no_gaps_desc') }}</div>
    </div>

    <div v-else class="grid grid-cols-2 gap-4 max-lg:grid-cols-1">
      <div v-for="gap in gaps" :key="gap.id" class="glass-card !rounded-xl p-5 group cursor-pointer transition-all duration-200">
        <div class="flex items-start gap-3 mb-3">
          <span class="text-xl">{{ typeIcons[gap.type] || '📌' }}</span>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-1">
              <span :class="['badge text-[10px] font-bold', sevBadge[gap.severity] || 'badge-info']">{{ t('gaps.severity.'+gap.severity) }}</span>
              <span class="text-[11px] text-muted-foreground font-mono">{{ gap.module }}</span>
            </div>
            <div class="text-[13px] font-semibold truncate">{{ gap.title }}</div>
          </div>
        </div>
        <p class="text-xs text-muted-foreground mb-4 line-clamp-2 leading-relaxed">{{ gap.description }}</p>
        <div class="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
          <button @click.stop="convertToTask(gap.id)" class="btn-primary !text-[11px] !py-1.5 !px-3">{{ t('gaps.create_task') }}</button>
          <button @click.stop="dismissGap(gap.id)" class="btn-outline !text-[11px] !py-1.5 !px-3">{{ t('gaps.dismiss') }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.line-clamp-2 { display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }
</style>
