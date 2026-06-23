<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { LayoutGrid, Search, MessageSquare, Map, Play, BarChart3, BookOpen, Settings } from 'lucide-vue-next'

const { t } = useI18n()
defineProps<{ currentView: string }>()
const emit = defineEmits<{ navigate: [view: string] }>()

const navItems = [
  { id: 'kanban', icon: LayoutGrid, key: 'nav.kanban' },
  { id: 'gaps', icon: Search, key: 'nav.gaps' },
  { id: 'chat', icon: MessageSquare, key: 'nav.chat' },
  { id: 'strategy', icon: Map, key: 'nav.strategy' },
  { id: 'execution', icon: Play, key: 'nav.execution' },
  { id: 'reports', icon: BarChart3, key: 'nav.reports' },
  { id: 'knowledge', icon: BookOpen, key: 'nav.knowledge' },
]
</script>

<template>
  <aside class="w-[232px] flex flex-col flex-shrink-0 select-none border-r" style="background:var(--sidebar); border-color:var(--sidebar-border)">
    <div class="px-5 py-4 flex items-center gap-2.5" style="border-bottom:1px solid var(--sidebar-border)">
      <div class="w-7 h-7 rounded-lg flex items-center justify-center" style="background:var(--primary-gradient)">
        <Play class="w-3.5 h-3.5 text-white" fill="white" :stroke-width="3" />
      </div>
      <span class="text-[15px] font-bold" style="color:var(--sidebar-logo)">TLO<span class="font-light opacity-50"> Platform</span></span>
    </div>

    <nav class="flex-1 p-2.5 flex flex-col gap-0.5 overflow-y-auto">
      <button v-for="item in navItems" :key="item.id" @click="emit('navigate', item.id)"
        :style="currentView === item.id
          ? { background: 'var(--sidebar-active-bg)', color: 'var(--sidebar-active)' }
          : { background: 'transparent', color: 'var(--sidebar-foreground)' }"
        class="flex items-center gap-3 px-3 py-2 rounded-lg text-[13px] transition-all w-full text-left border-none cursor-pointer font-sans font-medium"
      >
        <component :is="item.icon" :size="18" :stroke-width="currentView === item.id ? 2.5 : 1.8" class="flex-shrink-0" />
        <span class="truncate">{{ t(item.key) }}</span>
      </button>
    </nav>

    <!-- Settings at bottom -->
    <div class="p-2.5" style="border-top:1px solid var(--sidebar-border)">
      <button @click="emit('navigate', 'settings')"
        :style="currentView === 'settings'
          ? { background: 'var(--sidebar-active-bg)', color: 'var(--sidebar-active)' }
          : { background: 'transparent', color: 'var(--sidebar-foreground)' }"
        class="flex items-center gap-3 px-3 py-2 rounded-lg text-[13px] transition-all w-full text-left border-none cursor-pointer font-sans font-medium"
      >
        <component :is="Settings" :size="18" :stroke-width="currentView === 'settings' ? 2.5 : 1.8" class="flex-shrink-0" />
        <span class="truncate">{{ t('nav.settings') }}</span>
      </button>
    </div>
  </aside>
</template>
