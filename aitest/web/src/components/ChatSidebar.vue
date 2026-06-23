<script setup lang="ts">
import { useChatStore } from '@/stores/chat'

const store = useChatStore()
</script>

<template>
  <div class="w-[240px] bg-sidebar border-r border-border flex flex-col flex-shrink-0">
    <div class="p-3 border-b border-white/5">
      <button @click="store.newSession()" class="w-full px-3 py-2 text-[13px] bg-primary/20 text-primary rounded-md border-none cursor-pointer font-sans hover:bg-primary/30 transition-colors">
        + New Chat
      </button>
    </div>
    <div class="flex-1 overflow-y-auto p-2 space-y-0.5">
      <div
        v-for="s in store.sessions" :key="s.id"
        :class="['group flex items-center gap-2 px-3 py-2 rounded-md text-xs cursor-pointer transition-colors',
          store.activeId === s.id ? 'bg-primary/15 text-sidebar-active' : 'text-sidebar-foreground/70 hover:bg-sidebar-hover hover:text-sidebar-foreground']"
        @click="store.activeId = s.id"
      >
        <span class="truncate flex-1">{{ s.name }}</span>
        <button @click.stop="store.deleteSession(s.id)" class="opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-destructive cursor-pointer border-none bg-none text-[10px]">✕</button>
      </div>
      <div v-if="store.sessions.length === 0" class="p-4 text-center text-xs text-muted-foreground/50">
        No conversations yet
      </div>
    </div>
  </div>
</template>
