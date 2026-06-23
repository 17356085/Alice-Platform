<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import SidebarNav from './components/SidebarNav.vue'
import KanbanHeader from './components/KanbanHeader.vue'
import Toast from './components/Toast.vue'
import { useKanbanWS } from './composables/useKanbanWS'

const router = useRouter()
const route = useRoute()

// Theme: init from localStorage
const savedName = localStorage.getItem('tlo-theme-name')
const savedDark = localStorage.getItem('tlo-theme')
if (savedName) document.documentElement.setAttribute('data-theme', savedName)
if (savedDark === 'dark') document.documentElement.classList.add('dark')

// WebSocket
useKanbanWS().connect()

const viewTitles: Record<string, string> = {
  kanban: '📋 Kanban 看板',
  gaps: '🔍 Test Gap Discovery',
  chat: '💬 Intelligence Chat',
  strategy: '🗺 Strategy Planner',
  execution: '▶️ 执行监控',
  reports: '📊 测试报告',
  knowledge: '📚 知识库',
  settings: '⚙️ 设置',
}
const currentViewName = computed(() => String(route.name || 'kanban'))
const currentTitle = computed(() => viewTitles[currentViewName.value] || currentViewName.value)

function onNavigate(view: string) { router.push({ name: view }) }
</script>

<template>
  <div class="flex h-screen overflow-hidden">
    <SidebarNav
      :current-view="currentViewName"
      @navigate="onNavigate"
    />
    <div class="flex flex-1 flex-col overflow-hidden">
      <KanbanHeader :view-title="currentTitle" />
      <main class="flex-1 overflow-y-auto p-5">
        <router-view />
      </main>
    </div>
    <Toast />
  </div>
</template>
