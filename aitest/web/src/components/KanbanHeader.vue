<script setup lang="ts">
import { useKanbanWS } from '@/composables/useKanbanWS'

defineProps<{ viewTitle: string }>()
const { connected } = useKanbanWS()
</script>

<template>
  <header class="h-12 border-b border-border flex items-center px-5 gap-3 bg-card flex-shrink-0">
    <h1 class="text-[15px] font-semibold">{{ viewTitle }}</h1>
    <span class="text-xs text-muted-foreground">Testing Lifecycle Orchestrator</span>
    <span class="ml-auto inline-flex items-center gap-1 text-[10px]">
      <span :class="['w-1.5 h-1.5 rounded-full', connected ? 'bg-success' : 'bg-destructive']" />
      {{ connected ? 'Live' : 'Off' }}
    </span>
  </header>
</template>
