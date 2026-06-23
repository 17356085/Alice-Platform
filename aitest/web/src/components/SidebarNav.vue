<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

const { t, locale } = useI18n()

defineProps<{ currentView: string }>()
const emit = defineEmits<{ navigate: [view: string] }>()

const navItems = [
  { id: 'kanban', icon: '📋', key: 'nav.kanban' },
  { id: 'gaps', icon: '🔍', key: 'nav.gaps' },
  { id: 'chat', icon: '💬', key: 'nav.chat' },
  { id: 'strategy', icon: '🗺', key: 'nav.strategy' },
  { id: 'execution', icon: '▶️', key: 'nav.execution' },
  { id: 'reports', icon: '📊', key: 'nav.reports' },
  { id: 'knowledge', icon: '📚', key: 'nav.knowledge' },
  { id: 'settings', icon: '⚙️', key: 'nav.settings' },
]

const themes = [
  { id: 'default', label: 'Default' }, { id: 'dusk', label: 'Dusk' },
  { id: 'lime', label: 'Lime' }, { id: 'ocean', label: 'Ocean' },
  { id: 'retro', label: 'Retro' }, { id: 'neo', label: 'Neo' },
  { id: 'forest', label: 'Forest' }, { id: 'oscura', label: 'Oscura' },
]
const currentTheme = ref(localStorage.getItem('tlo-theme-name') || 'default')
const isDark = ref(localStorage.getItem('tlo-theme') === 'dark')

function selectTheme(id: string) {
  currentTheme.value = id
  document.documentElement.setAttribute('data-theme', id)
  if (id === 'oscura') { isDark.value = true; document.documentElement.classList.add('dark'); localStorage.setItem('tlo-theme', 'dark') }
  localStorage.setItem('tlo-theme-name', id)
}
function toggleDark() {
  isDark.value = !isDark.value
  document.documentElement.classList.toggle('dark', isDark.value)
  localStorage.setItem('tlo-theme', isDark.value ? 'dark' : 'light')
}
function toggleLang() {
  const next = locale.value === 'zh' ? 'en' : 'zh'
  locale.value = next
  localStorage.setItem('tlo-lang', next)
}
</script>

<template>
  <aside class="w-[220px] bg-sidebar flex flex-col flex-shrink-0 select-none">
    <div class="px-4 py-3.5 text-base font-bold text-white border-b border-white/5">
      TLO<span class="text-primary">.</span> Platform
    </div>
    <nav class="flex-1 p-2 flex flex-col gap-0.5 overflow-y-auto">
      <button v-for="item in navItems" :key="item.id" @click="emit('navigate', item.id)"
        :class="['flex items-center gap-2.5 px-3 py-2 rounded-md text-[13px] transition-colors w-full text-left border-none bg-none cursor-pointer font-sans',
          currentView === item.id ? 'bg-primary/15 text-sidebar-active' : 'text-sidebar-foreground hover:bg-sidebar-hover hover:text-white']">
        <span class="text-lg w-6 text-center flex-shrink-0">{{ item.icon }}</span> {{ t(item.key) }}
      </button>
    </nav>

    <div class="p-2 border-t border-white/5 space-y-1.5">
      <!-- Language -->
      <button @click="toggleLang"
        class="flex items-center gap-2 w-full px-3 py-1.5 rounded text-[11px] text-sidebar-foreground/60 hover:text-sidebar-foreground hover:bg-sidebar-hover cursor-pointer border-none bg-none font-sans">
        <span>{{ locale === 'zh' ? '🇨🇳' : '🇺🇸' }}</span> {{ locale === 'zh' ? 'English' : '中文' }}
      </button>
      <!-- Dark toggle -->
      <button @click="toggleDark"
        class="flex items-center gap-2 w-full px-3 py-1.5 rounded text-[11px] text-sidebar-foreground/60 hover:text-sidebar-foreground hover:bg-sidebar-hover cursor-pointer border-none bg-none font-sans">
        <span>{{ isDark ? '☀️' : '🌙' }}</span> {{ isDark ? t('theme.light') : t('theme.dark') }}
      </button>
      <!-- Theme grid -->
      <div class="text-[10px] text-sidebar-foreground/40 px-2 uppercase tracking-wider pt-1">{{ t('theme.label') }}</div>
      <div class="grid grid-cols-4 gap-1">
        <button v-for="t2 in themes" :key="t2.id" @click="selectTheme(t2.id)"
          :class="['text-[10px] py-1 px-0.5 rounded text-center cursor-pointer border transition-colors font-sans truncate',
            currentTheme === t2.id ? 'border-primary text-primary bg-primary/10' : 'border-transparent text-sidebar-foreground/50 hover:text-sidebar-foreground hover:bg-sidebar-hover']">
          {{ t2.label }}
        </button>
      </div>
    </div>
  </aside>
</template>
