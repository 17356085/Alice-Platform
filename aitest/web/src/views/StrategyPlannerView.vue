<script setup lang="ts">
import { ref, onMounted } from 'vue'

const modules = ref<Record<string, any>>({})
const riskMatrix = ref<{ module: string; score: number; diff: number; defect: number; passRate: number; rec: string }[]>([])

onMounted(async () => {
  try {
    const res = await fetch('/api/sop-status')
    modules.value = (await res.json()).modules || {}
  } catch { modules.value = {} }
  // Compute risk scores from module data
  riskMatrix.value = Object.entries(modules.value).map(([mod, info]: [string, any]) => {
    const diffScore = info.pages > 10 ? 0.8 : info.pages > 5 ? 0.5 : 0.2
    const defectScore = info.status === 'completed_with_issues' ? 0.9 : info.failed > 0 ? 0.6 : 0.1
    const passScore = info.status === 'completed' ? 0.9 : info.status === 'completed_with_issues' ? 0.5 : 0.3
    const score = diffScore * 0.4 + defectScore * 0.35 + (1 - passScore) * 0.25
    return {
      module: mod, score: Math.round(score * 100),
      diff: Math.round(diffScore * 100), defect: Math.round(defectScore * 100),
      passRate: Math.round(passScore * 100),
      rec: score > 0.7 ? 'P0: Must Test' : score > 0.4 ? 'P1: Should Test' : 'P2: Optional'
    }
  }).sort((a, b) => b.score - a.score)
})

const cols = ['module', 'risk', 'diff', 'defect', 'pass', 'action']
const colLabels = ['Module', 'Risk Score', 'Change Impact', 'Defect Heat', 'Pass Rate', 'Recommendation']
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-base font-semibold">🗺 Test Strategy Planner</h2>
      <span class="text-xs text-muted-foreground">Risk_Score = diff(0.4) + defect_heat(0.35) + fail_rate(0.25)</span>
    </div>

    <!-- Risk Heatmap -->
    <div class="grid grid-cols-6 gap-2 mb-6">
      <div
        v-for="m in riskMatrix" :key="m.module"
        class="card rounded-lg border p-3 text-center cursor-pointer hover:shadow-md transition-all"
        :class="m.score >= 70 ? 'border-destructive/30 bg-destructive/5' : m.score >= 40 ? 'border-warning/30 bg-warning/5' : 'border-success/30 bg-success/5'"
      >
        <div class="text-xs font-mono text-muted-foreground mb-1 truncate">{{ m.module }}</div>
        <div :class="['text-xl font-bold', m.score >= 70 ? 'text-destructive' : m.score >= 40 ? 'text-warning' : 'text-success']">
          {{ m.score }}%
        </div>
        <div class="text-[10px] text-muted-foreground mt-1">{{ m.rec.split(':')[0] }}</div>
      </div>
    </div>

    <!-- Strategy table -->
    <div class="card bg-card border border-border rounded-xl overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-xs">
          <thead>
            <tr class="bg-muted/50">
              <th v-for="(l, i) in colLabels" :key="i" class="text-left px-4 py-2.5 font-semibold text-muted-foreground">
                {{ l }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="m in riskMatrix" :key="m.module" class="border-t border-border hover:bg-muted/30 transition-colors">
              <td class="px-4 py-2.5 font-semibold font-mono">{{ m.module }}</td>
              <td class="px-4 py-2.5">
                <div class="flex items-center gap-2">
                  <div class="flex-1 h-1.5 bg-muted rounded-full overflow-hidden max-w-[80px]">
                    <div :class="['h-full rounded-full', m.score >= 70 ? 'bg-destructive' : m.score >= 40 ? 'bg-warning' : 'bg-success']" :style="{ width: `${m.score}%` }" />
                  </div>
                  <span class="font-semibold">{{ m.score }}%</span>
                </div>
              </td>
              <td class="px-4 py-2.5 text-muted-foreground">{{ m.diff }}%</td>
              <td class="px-4 py-2.5 text-muted-foreground">{{ m.defect }}%</td>
              <td class="px-4 py-2.5 text-muted-foreground">{{ m.passRate }}%</td>
              <td class="px-4 py-2.5">
                <span :class="['badge text-[10px]', m.score >= 70 ? 'badge-err' : m.score >= 40 ? 'badge-warn' : 'badge-ok']">
                  {{ m.rec }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<style scoped>
.badge { display:inline-block; padding:1px 6px; border-radius:9999px; font-weight:600; }
.badge-err { background:var(--destructive-light); color:var(--destructive); }
.badge-warn { background:var(--warning-light); color:var(--warning); }
.badge-ok { background:var(--success-light); color:var(--success); }
</style>
