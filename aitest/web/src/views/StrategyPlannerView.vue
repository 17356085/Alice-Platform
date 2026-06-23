<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
const { t } = useI18n()
const riskMatrix = ref<{ module: string; score: number; diff: number; defect: number; passRate: number; rec: string }[]>([])
onMounted(async () => {
  try {
    const r = await fetch('/api/sop-status'); const modules = (await r.json()).modules || {}
    riskMatrix.value = Object.entries(modules).map(([mod, info]: [string, any]) => {
      const diffScore = info.pages > 10 ? 0.8 : info.pages > 5 ? 0.5 : 0.2
      const defectScore = info.status === 'completed_with_issues' ? 0.9 : info.failed > 0 ? 0.6 : 0.1
      const passScore = info.status === 'completed' ? 0.9 : info.status === 'completed_with_issues' ? 0.5 : 0.3
      const score = diffScore * 0.4 + defectScore * 0.35 + (1 - passScore) * 0.25
      return { module: mod, score: Math.round(score * 100), diff: Math.round(diffScore * 100), defect: Math.round(defectScore * 100), passRate: Math.round(passScore * 100), rec: score > 0.7 ? t('strategy.p0') : score > 0.4 ? t('strategy.p1') : t('strategy.p2') }
    }).sort((a, b) => b.score - a.score)
  } catch { riskMatrix.value = [] }
})
</script>
<template>
  <div>
    <div class="flex items-center justify-between mb-5">
      <h2 class="text-base font-semibold">{{ t('strategy.title') }}</h2>
      <span class="text-[11px] text-muted-foreground font-mono">{{ t('strategy.formula') }}</span>
    </div>
    <div class="grid grid-cols-6 gap-3 mb-6">
      <div v-for="m in riskMatrix" :key="m.module"
        :class="['glass-card !rounded-xl p-4 text-center cursor-pointer transition-all duration-200',
          m.score >= 70 ? '!border-destructive/20' : m.score >= 40 ? '!border-warning/20' : '!border-success/20']">
        <div class="text-[11px] font-mono text-muted-foreground mb-1.5 truncate">{{ m.module }}</div>
        <div :class="['text-2xl font-bold', m.score >= 70 ? 'text-destructive' : m.score >= 40 ? 'text-warning' : 'text-success']">{{ m.score }}%</div>
        <div class="text-[10px] text-muted-foreground mt-1">{{ m.rec.split(':')[0] }}</div>
      </div>
    </div>
    <div class="glass-card !rounded-xl overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-xs">
          <thead><tr class="bg-muted/30">
            <th class="text-left px-4 py-3 font-semibold text-muted-foreground">{{ t('strategy.table.module') }}</th>
            <th class="text-left px-4 py-3 font-semibold text-muted-foreground">{{ t('strategy.table.risk') }}</th>
            <th class="text-left px-4 py-3 font-semibold text-muted-foreground">{{ t('strategy.table.diff') }}</th>
            <th class="text-left px-4 py-3 font-semibold text-muted-foreground">{{ t('strategy.table.defect') }}</th>
            <th class="text-left px-4 py-3 font-semibold text-muted-foreground">{{ t('strategy.table.pass') }}</th>
            <th class="text-left px-4 py-3 font-semibold text-muted-foreground">{{ t('strategy.table.action') }}</th>
          </tr></thead>
          <tbody>
            <tr v-for="m in riskMatrix" :key="m.module" class="border-t border-border hover:bg-muted/20 transition-colors">
              <td class="px-4 py-3 font-semibold font-mono">{{ m.module }}</td>
              <td class="px-4 py-3"><div class="flex items-center gap-2"><div class="flex-1 h-1.5 bg-muted rounded-full overflow-hidden max-w-[80px]"><div :class="['h-full rounded-full', m.score>=70?'bg-destructive':m.score>=40?'bg-warning':'bg-success']" :style="{width:m.score+'%'}" /></div><span class="font-semibold">{{ m.score }}%</span></div></td>
              <td class="px-4 py-3 text-muted-foreground">{{ m.diff }}%</td>
              <td class="px-4 py-3 text-muted-foreground">{{ m.defect }}%</td>
              <td class="px-4 py-3 text-muted-foreground">{{ m.passRate }}%</td>
              <td class="px-4 py-3"><span :class="['badge text-[10px] font-bold', m.score>=70?'badge-err':m.score>=40?'badge-warn':'badge-ok']">{{ m.rec }}</span></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
