<script setup lang="ts">
import { ref, onMounted } from 'vue'

const kpi = ref<any>({})

onMounted(async () => {
  try {
    const res = await fetch('/api/kpi/summary?days=30')
    kpi.value = await res.json()
  } catch { kpi.value = {} }
})
</script>

<template>
  <div class="grid grid-cols-2 gap-3.5">
    <div class="card bg-card border border-border rounded-lg">
      <div class="px-4 py-3 border-b border-border font-semibold text-[13px]">📊 State Audits (30d)</div>
      <div class="p-4 text-center">
        <div class="text-[28px] font-bold text-info">{{ kpi.state_drift?.audits || 0 }}</div>
        <div class="text-[11px] text-muted-foreground mt-1">state audits</div>
      </div>
    </div>
    <div class="card bg-card border border-border rounded-lg">
      <div class="px-4 py-3 border-b border-border font-semibold text-[13px]">📋 SOP Audits (30d)</div>
      <div class="p-4 text-center">
        <div class="text-[28px] font-bold text-warning">{{ kpi.sop_compliance?.audits || 0 }}</div>
        <div class="text-[11px] text-muted-foreground mt-1">sop audits</div>
      </div>
    </div>
    <div class="card bg-card border border-border rounded-lg">
      <div class="px-4 py-3 border-b border-border font-semibold text-[13px]">✅ SOP 合规率</div>
      <div class="p-4 text-center">
        <div class="text-[28px] font-bold text-success">{{ ((kpi.sop_compliance?.avg_compliance || 0) * 100).toFixed(0) }}%</div>
        <div class="text-[11px] text-muted-foreground mt-1">compliance rate</div>
      </div>
    </div>
    <div class="card bg-card border border-border rounded-lg">
      <div class="px-4 py-3 border-b border-border font-semibold text-[13px]">💰 30d 平均成本</div>
      <div class="p-4 text-center">
        <div class="text-[28px] font-bold text-primary">${{ kpi.cost?.avg_cost_per_period?.toFixed(2) || '0.00' }}</div>
        <div class="text-[11px] text-muted-foreground mt-1">avg cost</div>
      </div>
    </div>
  </div>
</template>
