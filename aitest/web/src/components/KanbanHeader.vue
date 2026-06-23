<script setup lang="ts">
import { useKanbanWS } from '@/composables/useKanbanWS'
import { Wifi, WifiOff } from 'lucide-vue-next'
defineProps<{ viewTitle: string; subtitle?: string }>()
const { connected } = useKanbanWS()
</script>

<template>
  <header class="h-14 flex items-center px-6 gap-4 flex-shrink-0 glass-card !rounded-none !border-x-0 !border-t-0" style="border-bottom:1px solid var(--border)">
    <h1 class="text-[15px] font-semibold tracking-tight">{{ viewTitle }}</h1>
    <span class="text-xs text-muted-foreground hidden sm:inline">{{ subtitle || 'Testing Lifecycle Orchestrator' }}</span>
    <div class="flex-1" />
    <div class="flex items-center gap-1.5 text-[10px]">
      <component :is="connected ? Wifi : WifiOff" :size="13" :stroke-width="2" :class="connected ? 'text-success' : 'text-destructive'" />
      <span :class="connected ? 'text-success font-semibold' : 'text-destructive'">{{ connected ? 'Live' : 'Offline' }}</span>
    </div>
  </header>
</template>
