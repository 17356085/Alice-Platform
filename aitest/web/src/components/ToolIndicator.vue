<script setup lang="ts">
defineProps<{ tool: string; input: string }>()
const toolMeta: Record<string, { icon: string; color: string; label: string }> = {
  Read: { icon: '📄', color: 'text-blue-400', label: 'Reading file' },
  Glob: { icon: '📁', color: 'text-amber-400', label: 'Searching files' },
  Grep: { icon: '🔎', color: 'text-green-400', label: 'Searching code' },
}
</script>

<template>
  <div class="flex items-center gap-2 px-3 py-1.5 text-xs animate-pulse" v-if="tool">
    <span :class="toolMeta[tool]?.color || 'text-muted-foreground'">{{ toolMeta[tool]?.icon || '🔧' }}</span>
    <span class="text-muted-foreground">{{ toolMeta[tool]?.label || tool }}</span>
    <span class="text-muted-foreground/50 font-mono truncate max-w-[200px]">{{ input }}</span>
  </div>
</template>
