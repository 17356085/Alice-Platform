<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import SidebarNav from './components/SidebarNav.vue'
import KanbanHeader from './components/KanbanHeader.vue'
import Toast from './components/Toast.vue'
import { useKanbanWS } from './composables/useKanbanWS'

const router = useRouter()
const route = useRoute()
const isDark = ref(false)

// Theme init
const saved = localStorage.getItem('tlo-theme')
if (saved === 'dark') {
  isDark.value = true
  document.documentElement.classList.add('dark')
}

function toggleTheme() {
  isDark.value = !isDark.value
  document.documentElement.classList.toggle('dark', isDark.value)
  localStorage.setItem('tlo-theme', isDark.value ? 'dark' : 'light')
}

// WebSocket
useKanbanWS().connect()

import { computed } from 'vue'

const viewTitles: Record<string, string> = {
  kanban: '📋 Kanban 看板',
  execution: '▶️ 执行监控',
  reports: '📊 测试报告',
  knowledge: '🔍 知识库',
  settings: '⚙️ 设置',
}
const currentTitle = computed(() => viewTitles[route.name as string] || String(route.name))
</script>

<template>
  <div class="flex h-screen overflow-hidden">
    <SidebarNav
      :current-view="(route.name as string)"
      :is-dark="isDark"
      @toggle-theme="toggleTheme"
      @navigate="(v: string) => router.push({ name: v })"
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
