<script setup lang="ts">
import TerminalPanel from '@/components/TerminalPanel.vue'
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-4">
      <span class="text-xs text-muted-foreground">Agent 执行日志 — xterm.js PTY</span>
      <button @click="() => {}" class="px-4 py-1.5 rounded-md border border-border bg-card text-[13px] cursor-pointer hover:border-ring font-sans transition-colors">
        🔄 刷新
      </button>
    </div>
    <TerminalPanel auto-connect />
    <div class="mt-4 text-xs text-muted-foreground text-center">
      终端连接到 WebSocket <code class="bg-muted px-1 rounded">/ws/kanban</code> — 运行 <code class="bg-muted px-1 rounded">aitest sop run</code> 查看实时日志
    </div>
  </div>
</template>
