<script setup lang="ts">
defineProps<{
  currentView: string
  isDark: boolean
}>()

const emit = defineEmits<{
  'toggle-theme': []
  navigate: [view: string]
}>()

const navItems = [
  { id: 'kanban', icon: '📋', label: 'Kanban' },
  { id: 'execution', icon: '▶️', label: 'Execution' },
  { id: 'reports', icon: '📊', label: 'Reports' },
  { id: 'knowledge', icon: '🔍', label: 'Knowledge' },
  { id: 'settings', icon: '⚙️', label: 'Settings' },
]
</script>

<template>
  <aside class="w-[220px] bg-sidebar flex flex-col flex-shrink-0 select-none">
    <div class="px-4 py-3.5 text-base font-bold text-white border-b border-white/5">
      TLO<span class="text-primary">.</span> Platform
    </div>
    <nav class="flex-1 p-2 flex flex-col gap-0.5">
      <button
        v-for="item in navItems"
        :key="item.id"
        @click="emit('navigate', item.id)"
        :class="[
          'flex items-center gap-2.5 px-3 py-2 rounded-md text-[13px] transition-colors w-full text-left border-none bg-none cursor-pointer font-sans',
          currentView === item.id
            ? 'bg-primary/15 text-sidebar-active'
            : 'text-sidebar-foreground hover:bg-sidebar-hover hover:text-white'
        ]"
      >
        <span class="text-lg w-6 text-center flex-shrink-0">{{ item.icon }}</span>
        {{ item.label }}
      </button>
    </nav>
    <div class="p-2 border-t border-white/5">
      <button
        @click="emit('toggle-theme')"
        class="flex items-center gap-2 px-3 py-2 rounded-md text-xs text-sidebar-foreground hover:bg-sidebar-hover cursor-pointer w-full border-none bg-none font-sans"
      >
        <span>{{ isDark ? '☀️' : '🌙' }}</span>
        {{ isDark ? 'Light Mode' : 'Dark Mode' }}
      </button>
    </div>
  </aside>
</template>
