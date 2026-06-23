<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { LayoutGrid, Search, MessageSquare, Map, Play, BarChart3, BookOpen, Settings, Sun, Moon, Languages } from 'lucide-vue-next'

const { t, locale } = useI18n()
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
  { id: 'settings', icon: Settings, key: 'nav.settings' },
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
function onHover(e: Event) { (e.target as HTMLElement).style.background = 'var(--sidebar-hover)' }
function onLeave(e: Event) { (e.target as HTMLElement).style.background = 'transparent' }
</script>

<template>
  <aside class="w-[232px] flex flex-col flex-shrink-0 select-none border-r" style="background:var(--sidebar); border-color:var(--sidebar-border)">
    <!-- Logo -->
    <div class="px-5 py-4 flex items-center gap-2.5" style="border-bottom:1px solid var(--sidebar-border)">
      <div class="w-7 h-7 rounded-lg flex items-center justify-center" style="background:var(--primary-gradient)">
        <Play class="w-3.5 h-3.5 text-white" fill="white" :stroke-width="3" />
      </div>
      <span class="text-[15px] font-bold" style="color:var(--sidebar-logo)">TLO<span class="font-light opacity-50"> Platform</span></span>
    </div>

    <!-- Nav items -->
    <nav class="flex-1 p-2.5 flex flex-col gap-0.5 overflow-y-auto">
      <button
        v-for="item in navItems" :key="item.id"
        @click="emit('navigate', item.id)"
        :style="currentView === item.id
          ? { background: 'var(--sidebar-active-bg)', color: 'var(--sidebar-active)' }
          : { background: 'transparent', color: 'var(--sidebar-foreground)' }"
        class="flex items-center gap-3 px-3 py-2 rounded-lg text-[13px] transition-all w-full text-left border-none cursor-pointer font-sans font-medium"
      >
        <component :is="item.icon" :size="18" :stroke-width="currentView === item.id ? 2.5 : 1.8" class="flex-shrink-0" />
        <span class="truncate">{{ t(item.key) }}</span>
      </button>
    </nav>

    <!-- Footer controls -->
    <div class="p-2.5 space-y-1.5" style="border-top:1px solid var(--sidebar-border)">
      <!-- Lang toggle -->
      <button @click="toggleLang"
        class="flex items-center gap-2.5 w-full px-3 py-2 rounded-lg text-[11px] transition-all cursor-pointer border-none font-sans font-medium"
        style="color:var(--sidebar-foreground); background:transparent"
        @mouseenter="onHover" @mouseleave="onLeave"
      >
        <Languages :size="15" :stroke-width="1.8" />
        {{ locale === 'zh' ? 'English' : '中文' }}
      </button>

      <!-- Dark toggle -->
      <button @click="toggleDark"
        class="flex items-center gap-2.5 w-full px-3 py-2 rounded-lg text-[11px] transition-all cursor-pointer border-none font-sans font-medium"
        style="color:var(--sidebar-foreground); background:transparent"
        @mouseenter="onHover" @mouseleave="onLeave"
      >
        <component :is="isDark ? Sun : Moon" :size="15" :stroke-width="1.8" />
        {{ isDark ? t('theme.light') : t('theme.dark') }}
      </button>

      <!-- Theme grid -->
      <div class="text-[9px] uppercase tracking-widest pt-1.5 px-2 font-semibold" style="color:var(--sidebar-foreground); opacity:0.4">{{ t('theme.label') }}</div>
      <div class="grid grid-cols-4 gap-1">
        <button v-for="t2 in themes" :key="t2" @click="selectTheme(t2)"
          class="text-[10px] py-1.5 rounded-md text-center cursor-pointer border transition-all font-sans capitalize font-medium"
          :style="currentTheme === t2
            ? { borderColor: 'var(--sidebar-active)', color: 'var(--sidebar-active)', background: 'var(--sidebar-active-bg)' }
            : { borderColor: 'transparent', color: 'var(--sidebar-foreground)', opacity: 0.55 }"
        >{{ t2 }}</button>
      </div>
    </div>
  </aside>
</template>
