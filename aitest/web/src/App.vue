<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import SidebarNav from './components/SidebarNav.vue'
import KanbanHeader from './components/KanbanHeader.vue'
import KanbanWS from './composables/useKanbanWS'

const router = useRouter()
const route = useRoute()
const isDark = ref(false)

// Init theme
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

// WebSocket connection
KanbanWS.connect()
</script>

<template>
  <div class="flex h-screen overflow-hidden">
    <SidebarNav
      :current-view="route.name as string"
      :is-dark="isDark"
      @toggle-theme="toggleTheme"
      @navigate="(v: string) => router.push({ name: v })"
    />
    <div class="flex flex-1 flex-col overflow-hidden">
      <KanbanHeader :view-title="(route.meta?.title as string) || route.name as string" />
      <main class="flex-1 overflow-y-auto p-5">
        <router-view />
      </main>
    </div>
  </div>
</template>
