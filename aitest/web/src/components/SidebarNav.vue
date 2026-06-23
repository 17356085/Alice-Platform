<script setup lang="ts">
/** Segmented sidebar: Dashboard | Workspace (per-project) | Bottom actions. */
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useProjectStore } from '../stores/project'
import {
  LayoutDashboard, LayoutGrid, Search, MessageSquare, Play,
  BarChart3, BookOpen, Settings, Plus, FolderOpen, Terminal, Lightbulb, Link2,
} from 'lucide-vue-next'

const { t } = useI18n()
const projectStore = useProjectStore()
const props = defineProps<{ currentView: string }>()
const emit = defineEmits<{ navigate: [view: string] }>()

const hasActiveProject = computed(() => !!projectStore.activeId)

const workspaceItems = [
  { id: 'workspace/kanban',    icon: LayoutGrid,      key: 'SOP Kanban' },
  { id: 'workspace/gaps',      icon: Search,           key: 'Gap Scan' },
  { id: 'workspace/terminal',  icon: Terminal,         key: 'Agent Terminal' },
  { id: 'workspace/chat',      icon: MessageSquare,    key: 'AI Chat' },
  { id: 'workspace/execution', icon: Play,             key: 'Execution' },
  { id: 'workspace/ideation',  icon: Lightbulb,        key: 'Ideation' },
  { id: 'workspace/integrations', icon: Link2,         key: 'Integrations' },
  { id: 'workspace/reports',   icon: BarChart3,         key: 'Reports' },
  { id: 'workspace/knowledge', icon: BookOpen,          key: 'Knowledge' },
  { id: 'workspace/settings',  icon: FolderOpen,        key: 'Project Settings' },
]

function currentSection(view: string): 'dashboard' | 'workspace' | 'bottom' {
  if (view === 'dashboard') return 'dashboard'
  if (view.startsWith('workspace/')) return 'workspace'
  return 'bottom'
}
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

    <nav class="flex-1 p-2.5 flex flex-col overflow-y-auto">
      <!-- Section: Dashboard -->
      <button @click="emit('navigate', 'dashboard')"
        :style="currentSection(currentView) === 'dashboard'
          ? { background: 'var(--sidebar-active-bg)', color: 'var(--sidebar-active)' }
          : { background: 'transparent', color: 'var(--sidebar-foreground)' }"
        class="nav-btn"
      >
        <LayoutDashboard :size="18" :stroke-width="currentSection(currentView) === 'dashboard' ? 2.5 : 1.8" class="flex-shrink-0" />
        <span class="truncate">面板</span>
      </button>

      <!-- Divider -->
      <div class="sidebar-divider" />

      <!-- Section: Workspace -->
      <div v-if="hasActiveProject" class="workspace-section">
        <div class="section-label">
          <FolderOpen :size="12" />
          <span class="truncate">{{ projectStore.activeProject?.name || projectStore.activeProject?.id || 'Workspace' }}</span>
        </div>

        <button v-for="item in workspaceItems" :key="item.id" @click="emit('navigate', item.id)"
          :style="currentSection(currentView) === 'workspace' && currentView === item.id
            ? { background: 'var(--sidebar-active-bg)', color: 'var(--sidebar-active)' }
            : { background: 'transparent', color: 'var(--sidebar-foreground)' }"
          class="nav-btn"
        >
          <component :is="item.icon" :size="18" :stroke-width="currentSection(currentView) === 'workspace' && currentView === item.id ? 2.5 : 1.8" class="flex-shrink-0" />
          <span class="truncate">{{ item.key }}</span>
        </button>
      </div>

      <!-- No project selected -->
      <div v-else class="no-project-hint">
        <FolderOpen :size="24" class="hint-icon" />
        <p>选择一个项目以查看工作区</p>
        <button @click="emit('navigate', 'dashboard')" class="hint-link">前往面板</button>
      </div>
    </nav>

    <!-- Bottom actions -->
    <div class="p-2.5 flex flex-col gap-0.5" style="border-top:1px solid var(--sidebar-border)">
      <button @click="emit('navigate', 'onboarding')"
        :style="currentView === 'onboarding'
          ? { background: 'var(--sidebar-active-bg)', color: 'var(--sidebar-active)' }
          : { background: 'transparent', color: 'var(--sidebar-foreground)' }"
        class="nav-btn"
      >
        <Plus :size="18" :stroke-width="currentView === 'onboarding' ? 2.5 : 1.8" class="flex-shrink-0" />
        <span class="truncate">{{ t('nav.onboarding') }}</span>
      </button>
      <button @click="emit('navigate', 'settings')"
        :style="currentView === 'settings'
          ? { background: 'var(--sidebar-active-bg)', color: 'var(--sidebar-active)' }
          : { background: 'transparent', color: 'var(--sidebar-foreground)' }"
        class="nav-btn"
      >
        <Settings :size="18" :stroke-width="currentView === 'settings' ? 2.5 : 1.8" class="flex-shrink-0" />
        <span class="truncate">{{ t('nav.settings') }}</span>
      </button>
    </div>
  </aside>
</template>

<style scoped>
.nav-btn {
  display: flex; align-items: center; gap: 12px;
  padding: 8px 12px; border-radius: 8px; font-size: 13px;
  width: 100%; text-align: left; border: none; cursor: pointer;
  font-family: inherit; font-weight: 500; transition: all .15s;
}
.nav-btn:hover { background: var(--sidebar-active-bg); opacity: .85; }

.sidebar-divider {
  height: 1px; margin: 8px 8px;
  background: var(--sidebar-border); opacity: .6;
}

.workspace-section { margin-top: 4px; }
.section-label {
  display: flex; align-items: center; gap: 6px;
  padding: 6px 12px; font-size: 11px; font-weight: 600;
  color: var(--sidebar-foreground); opacity: .5; text-transform: uppercase;
  letter-spacing: .5px;
}

.no-project-hint {
  display: flex; flex-direction: column; align-items: center; gap: 8px;
  padding: 32px 16px; text-align: center;
}
.no-project-hint p { font-size: 12px; color: var(--text-muted); margin: 0; }
.hint-icon { opacity: .3; }
.hint-link { font-size: 12px; color: var(--accent); background: none; border: none; cursor: pointer; }
</style>
