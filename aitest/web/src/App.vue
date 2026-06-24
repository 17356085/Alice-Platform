<script setup lang="ts">
/** Root layout — v1.0: Segmented sidebar + project selector in header. */
import { computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { LayoutDashboard } from 'lucide-vue-next'
import SidebarNav from './components/SidebarNav.vue'
import KanbanHeader from './components/KanbanHeader.vue'
import ProjectSelector from './components/ProjectSelector.vue'
import Toast from './components/Toast.vue'
import { useKanbanWS } from './composables/useKanbanWS'
import { useProjectStore } from './stores/project'

const { t } = useI18n()
const router = useRouter()
const route = useRoute()

// Theme init
const savedTheme = localStorage.getItem('tlo-theme-name') || 'default'
const savedDark = localStorage.getItem('tlo-theme') === 'dark'
document.documentElement.setAttribute('data-theme', savedTheme)
if (savedDark) document.documentElement.classList.add('dark')
window.addEventListener('storage', (e) => {
  if (e.key === 'tlo-theme-name' && e.newValue) document.documentElement.setAttribute('data-theme', e.newValue)
  if (e.key === 'tlo-theme') document.documentElement.classList.toggle('dark', e.newValue === 'dark')
})

// Init
// v2.5 Stabilization: skip WebSocket when ?nosock=1 for memory isolation
if (!location.search.includes('nosock=1')) {
  useKanbanWS().connect()
}
const projectStore = useProjectStore()
onMounted(() => projectStore.init())

// Header title mapping
const viewTitles: Record<string, string> = {
  dashboard: '面板',
  kanban: 'SOP 看板',
  gaps: '缺口发现',
  chat: '智能对话',
  execution: '执行监控',
  terminal: 'Agent 终端',
  ideation: '测试构思',
  integrations: '项目集成',
  reports: '测试报告',
  knowledge: '知识库',
  'project-settings': '项目设置',
  settings: '应用设置',
  onboarding: '新建项目',
  strategy: '策略规划',
}
const currentViewName = computed(() => String(route.name || 'dashboard'))
const currentTitle = computed(() => viewTitles[currentViewName.value] || currentViewName.value)

function onNavigate(view: string) {
  router.push({ name: view }).catch((e) => console.warn('[App] Nav error:', e))
}
</script>

<template>
  <div class="flex h-screen overflow-hidden">
    <SidebarNav :current-view="currentViewName" @navigate="onNavigate" />

    <div class="flex flex-1 flex-col overflow-hidden">
      <KanbanHeader
        :view-title="currentTitle"
        :view-icon="LayoutDashboard"
        :subtitle="t('app.subtitle')"
      >
        <template #extra>
          <ProjectSelector v-if="currentViewName.startsWith('workspace') || currentViewName === 'dashboard'" />
        </template>
      </KanbanHeader>

      <main class="flex-1 overflow-y-auto">
        <router-view />
      </main>
    </div>

    <Toast />
  </div>
</template>
