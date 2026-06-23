<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import SidebarNav from './components/SidebarNav.vue'
import KanbanHeader from './components/KanbanHeader.vue'
import Toast from './components/Toast.vue'
import { useKanbanWS } from './composables/useKanbanWS'

const { t } = useI18n()
const router = useRouter()
const route = useRoute()

const savedName = localStorage.getItem('tlo-theme-name')
const savedDark = localStorage.getItem('tlo-theme')
if (savedName) document.documentElement.setAttribute('data-theme', savedName)
if (savedDark === 'dark') document.documentElement.classList.add('dark')

useKanbanWS().connect()

const viewTitles: Record<string, string> = {
  kanban: '📋', gaps: '🔍', chat: '💬', strategy: '🗺',
  execution: '▶️', reports: '📊', knowledge: '📚', settings: '⚙️',
}
const navKeys: Record<string, string> = {
  kanban: 'nav.kanban', gaps: 'nav.gaps', chat: 'nav.chat', strategy: 'nav.strategy',
  execution: 'nav.execution', reports: 'nav.reports', knowledge: 'nav.knowledge', settings: 'nav.settings',
}
const currentViewName = computed(() => String(route.name || 'kanban'))
const currentTitle = computed(() => `${viewTitles[currentViewName.value] || ''} ${t(navKeys[currentViewName.value] || '')}`)
const subtitle = computed(() => t('app.subtitle'))

function onNavigate(view: string) { router.push({ name: view }) }
</script>

<template>
  <div class="flex h-screen overflow-hidden">
    <SidebarNav :current-view="currentViewName" @navigate="onNavigate" />
    <div class="flex flex-1 flex-col overflow-hidden">
      <KanbanHeader :view-title="currentTitle" :subtitle="subtitle" />
      <main class="flex-1 overflow-y-auto p-5">
        <router-view />
      </main>
    </div>
    <Toast />
  </div>
</template>
