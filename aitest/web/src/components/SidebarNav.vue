<script setup lang="ts">
/** Segmented sidebar: Dashboard | Workspace (per-project) | Bottom actions. */
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useProjectStore } from '../stores/project'
import {
  LayoutDashboard, LayoutGrid, Search, MessageSquare, Play,
  BarChart3, BookOpen, Settings, Plus, FolderOpen, Terminal, Lightbulb, Link2, Clock, Eye,
} from 'lucide-vue-next'

const { t } = useI18n()
const projectStore = useProjectStore()
const props = defineProps<{ currentView: string }>()
const emit = defineEmits<{ navigate: [view: string] }>()

const hasActiveProject = computed(() => !!projectStore.activeId)
const pid = computed(() => projectStore.activeId || 'default')

// ★ v1.1: Progressive Disclosure — 3 tiers
// L1: always visible (core workflow)
const tier1Items = [
  { id: 'execution', icon: Play, key: '执行中心' },
  { id: 'artifacts', icon: FolderOpen, key: '产物' },
]
// L2: visible when project has activity (SOP data exists)
const tier2Items = [
  { id: 'observability', icon: Clock, key: '可观测性' },
  { id: 'reports', icon: BarChart3, key: '报告' },
  { id: 'knowledge', icon: BookOpen, key: '知识' },
  { id: 'kanban', icon: LayoutGrid, key: '看板' },
]
// L3: advanced tools
const tier3Items = [
  { id: 'terminal', icon: Terminal, key: '终端' },
  { id: 'gaps', icon: Search, key: '缺口' },
  { id: 'chat', icon: MessageSquare, key: '对话' },
  { id: 'settings', icon: Settings, key: '设置' },
]

const allItems = [...tier1Items, ...tier2Items, ...tier3Items]

// Check if project has any data (SOP runs, reports, knowledge)
const hasProjectData = computed(() => {
  try {
    const mods = JSON.parse(localStorage.getItem('tlo-modules') || '{}')
    return Object.keys(mods).length > 0
  } catch { return false }
})

function currentSection(view: string): 'dashboard' | 'project' | 'bottom' {
  if (view === 'dashboard') return 'dashboard'
  if (view.startsWith('project-') || view.startsWith('projects/')) return 'project'
  if (view.startsWith('workspace/')) return 'project'
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

        <!-- Tier 1: core workflow -->
        <button v-for="item in tier1Items" :key="item.id"
          @click="emit('navigate', `/projects/${pid}/${item.id}`)"
          :class="['nav-btn', currentView === `project-${item.id}` ? 'nav-active' : '']"
        >
          <component :is="item.icon" :size="18" :stroke-width="currentView === `project-${item.id}` ? 2.5 : 1.8" class="flex-shrink-0" />
          <span class="truncate">{{ item.key }}</span>
        </button>

        <!-- Tier 2: visible when project has data -->
        <template v-if="hasProjectData">
          <div class="tier-divider" />
          <button v-for="item in tier2Items" :key="item.id"
            @click="emit('navigate', `/projects/${pid}/${item.id}`)"
            :class="['nav-btn', currentView === `project-${item.id}` ? 'nav-active' : '']"
          >
            <component :is="item.icon" :size="18" :stroke-width="currentView === `project-${item.id}` ? 2.5 : 1.8" class="flex-shrink-0" />
            <span class="truncate">{{ item.key }}</span>
          </button>
        </template>

        <!-- Tier 3: advanced tools (collapsible) -->
        <details class="tier-details">
          <summary class="tier-summary">更多工具</summary>
          <button v-for="item in tier3Items" :key="item.id"
            @click="emit('navigate', `/projects/${pid}/${item.id}`)"
            :class="['nav-btn', currentView === `project-${item.id}` ? 'nav-active' : '']"
          >
            <component :is="item.icon" :size="18" :stroke-width="currentView === `project-${item.id}` ? 2.5 : 1.8" class="flex-shrink-0" />
            <span class="truncate">{{ item.key }}</span>
          </button>
        </details>
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

/* Progressive Disclosure tiers */
.nav-active { background: var(--sidebar-active-bg); color: var(--sidebar-active); }
.tier-divider { height: 1px; margin: 4px 12px; background: var(--sidebar-border); opacity: .4; }
.tier-details { margin-top: 4px; }
.tier-summary {
  font-size: 10px; padding: 4px 12px; cursor: pointer;
  color: var(--sidebar-foreground); opacity: .4; text-transform: uppercase; letter-spacing: .5px;
  user-select: none;
}
.tier-summary:hover { opacity: .7; }
.tier-details[open] .tier-summary { opacity: .6; }
</style>
