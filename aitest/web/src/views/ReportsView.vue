<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
const { t } = useI18n()
const kpi = ref<any>({})
onMounted(async () => { try { const r = await fetch('/api/kpi/summary?days=30'); kpi.value = await r.json() } catch { kpi.value = {} } })
</script>
<template>
  <div>
    <h2 class="text-base font-semibold mb-5">{{ t('reports.title') }}</h2>
    <div class="grid grid-cols-2 gap-4">
      <div class="glass-card p-5 text-center">
        <div class="text-[28px] font-bold text-info">{{ kpi.state_drift?.audits || 0 }}</div>
        <div class="text-xs text-muted-foreground mt-1">State Audits (30d)</div>
      </div>
      <div class="glass-card p-5 text-center">
        <div class="text-[28px] font-bold text-warning">{{ kpi.sop_compliance?.audits || 0 }}</div>
        <div class="text-xs text-muted-foreground mt-1">SOP Audits (30d)</div>
      </div>
      <div class="glass-card p-5 text-center">
        <div class="text-[28px] font-bold text-success">{{ ((kpi.sop_compliance?.avg_compliance || 0) * 100).toFixed(0) }}%</div>
        <div class="text-xs text-muted-foreground mt-1">SOP Compliance</div>
      </div>
      <div class="glass-card p-5 text-center">
        <div class="text-[28px] font-bold" style="color:var(--primary)">${{ kpi.cost?.avg_cost_per_period?.toFixed(2) || '0.00' }}</div>
        <div class="text-xs text-muted-foreground mt-1">Avg Cost (30d)</div>
      </div>
    </div>
  </div>
</template>
