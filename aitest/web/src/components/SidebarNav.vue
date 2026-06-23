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
const themes = ['default','dusk','lime','ocean','retro','neo','forest','oscura']
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
  <aside class="w-[232px] flex flex-col flex-shrink-0 select-none" style="background:var(--sidebar-gradient)">
    <div class="px-5 py-4 text-[17px] font-bold text-white flex items-center gap-1.5" style="border-bottom:1px solid var(--sidebar-border)">
      <span class="w-2 h-2 rounded-full flex-shrink-0" style="background:var(--primary-gradient)" />
      TLO<span class="font-light opacity-60"> Platform</span>
    </div>
    <nav class="flex-1 p-3 flex flex-col gap-0.5 overflow-y-auto">
      <button
        v-for="item in navItems" :key="item.id"
        @click="emit('navigate', item.id)"
        :class="['flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-[13px] transition-all w-full text-left border-none cursor-pointer font-sans',
          currentView === item.id ? 'font-semibold shadow-sm' : '']"
        :style="currentView === item.id
          ? { background: 'var(--sidebar-active-bg)', color: 'var(--sidebar-active)' }
          : { background: 'transparent', color: 'var(--sidebar-foreground)' }"
      >
        <span class="text-base w-7 text-center flex-shrink-0">{{ item.icon }}</span>
        <span class="truncate">{{ t(item.key) }}</span>
        <span v-if="currentView === item.id" class="ml-auto w-1 h-5 rounded-full flex-shrink-0" style="background:var(--primary-gradient)" />
      </button>
    </nav>
    <div class="p-3 space-y-2" style="border-top:1px solid var(--sidebar-border)">
      <button @click="toggleLang"
        class="flex items-center gap-2 w-full px-3 py-1.5 rounded-md text-[11px] transition-colors cursor-pointer border-none bg-transparent font-sans hover:brightness-125"
        style="color:var(--sidebar-foreground); opacity:0.6">
        <span>{{ locale === 'zh' ? '🇨🇳' : '🇺🇸' }}</span> {{ locale === 'zh' ? 'Switch to English' : '切换到中文' }}
      </button>
      <button @click="toggleDark"
        class="flex items-center gap-2 w-full px-3 py-1.5 rounded-md text-[11px] transition-colors cursor-pointer border-none bg-transparent font-sans hover:brightness-125"
        style="color:var(--sidebar-foreground); opacity:0.6">
        <span>{{ isDark ? '☀️' : '🌙' }}</span> {{ isDark ? t('theme.light') : t('theme.dark') }}
      </button>
      <div class="text-[9px] uppercase tracking-widest pt-1 px-2" style="color:var(--sidebar-foreground); opacity:0.35">{{ t('theme.label') }}</div>
      <div class="grid grid-cols-4 gap-1">
        <button
          v-for="t2 in themes" :key="t2"
          @click="selectTheme(t2)"
          class="text-[10px] py-1.5 rounded-md text-center cursor-pointer border transition-all font-sans capitalize"
          :class="currentTheme === t2 ? 'font-semibold shadow-sm' : 'border-transparent opacity-50'"
          :style="currentTheme === t2
            ? { borderColor: 'var(--sidebar-active)', color: 'var(--sidebar-active)', background: 'var(--sidebar-active-bg)' }
            : { color: 'var(--sidebar-foreground)' }"
        >{{ t2 }}</button>
      </div>
    </div>
  </aside>
</template>
