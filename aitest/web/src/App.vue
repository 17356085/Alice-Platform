<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { LayoutGrid, Search, MessageSquare, Map, Play, BarChart3, BookOpen, Settings } from 'lucide-vue-next'
import SidebarNav from './components/SidebarNav.vue'
import KanbanHeader from './components/KanbanHeader.vue'
import Toast from './components/Toast.vue'
import { useKanbanWS } from './composables/useKanbanWS'

const { t } = useI18n()
const router = useRouter()
const route = useRoute()

const savedTheme = localStorage.getItem('tlo-theme-name') || 'default'
const savedDark = localStorage.getItem('tlo-theme') === 'dark'
document.documentElement.setAttribute('data-theme', savedTheme)
if (savedDark) document.documentElement.classList.add('dark')

window.addEventListener('storage', (e) => {
  if (e.key === 'tlo-theme-name' && e.newValue) document.documentElement.setAttribute('data-theme', e.newValue)
  if (e.key === 'tlo-theme') document.documentElement.classList.toggle('dark', e.newValue === 'dark')
})

useKanbanWS().connect()

const viewIcons: Record<string, any> = {
  kanban: LayoutGrid, gaps: Search, chat: MessageSquare, strategy: Map,
  execution: Play, reports: BarChart3, knowledge: BookOpen, settings: Settings,
}
const navKeys: Record<string, string> = {
  kanban: 'nav.kanban', gaps: 'nav.gaps', chat: 'nav.chat', strategy: 'nav.strategy',
  execution: 'nav.execution', reports: 'nav.reports', knowledge: 'nav.knowledge', settings: 'nav.settings',
}
const currentViewName = computed(() => String(route.name || 'kanban'))
const currentTitle = computed(() => t(navKeys[currentViewName.value]))
const currentIcon = computed(() => viewIcons[currentViewName.value])

function onNavigate(view: string) {
  router.push({ name: view }).catch((e) => console.warn('[App] Nav error:', e))
}
</script>

<template>
  <div class="flex h-screen overflow-hidden">
    <SidebarNav :current-view="currentViewName" @navigate="onNavigate" />
    <div class="flex flex-1 flex-col overflow-hidden">
      <KanbanHeader :view-title="currentTitle" :view-icon="currentIcon" :subtitle="t('app.subtitle')" />
      <main class="flex-1 overflow-y-auto p-6">
        <router-view />
      </main>
    </div>
    <Toast />
  </div>
</template>
