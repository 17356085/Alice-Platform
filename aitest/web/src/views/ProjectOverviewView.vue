<script setup lang="ts">
import { onMounted, computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProjectStore } from '../stores/project'
import { useKanbanStore } from '../stores/kanban'
import { useHealth } from '../composables/useHealth'
import { Layers, Play, BarChart3, Clock, FolderOpen, Settings } from 'lucide-vue-next'
import ProjectSelector from '../components/ProjectSelector.vue'
import StepProgress from '../components/StepProgress.vue'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()
const kanbanStore = useKanbanStore()
const { health, refresh: refreshHealth } = useHealth()

const projectId = computed(() => route.params.id as string)
const loading = ref(true)

onMounted(async () => {
  projectStore.setActive(projectId.value)
  await projectStore.fetchProjects()
  await kanbanStore.fetchModules()
  refreshHealth()
  loading.value = false
})

const modules = computed(() => {
  return Object.entries(kanbanStore.modules).map(([id, m]: [string, any]) => ({
    id,
    name: m.name || id,
    phases_done: m.phases_done || 0,
    phases_total: m.phases_total || 8,
    status: m.status || 'pending',
    pages: m.pages || 0,
    failed: m.failed || 0,
    pct: m.phases_total ? Math.round((m.phases_done / m.phases_total) * 100) : 0,
  }))
})

const sopStats = computed(() => {
  const mods = modules.value
  const total = mods.length
  const completed = mods.filter(m => m.pct >= 100).length
  const inProgress = mods.filter(m => m.pct > 0 && m.pct < 100).length
  const failed = mods.filter(m => m.status === 'failed').length
  return { total, completed, inProgress, failed }
})

function openExecution(moduleId: string) {
  router.push(`/projects/${projectId.value}/execution?module=${moduleId}`)
}
function openArtifacts(moduleId: string) {
  router.push(`/projects/${projectId.value}/artifacts?module=${moduleId}`)
}
</script>

<template>
  <div class="overview">
    <div class="overview-header">
      <div class="header-left">
        <FolderOpen :size="22" />
        <h1>{{ projectId }}</h1>
      </div>
      <ProjectSelector />
    </div>

    <!-- SOP progress ring -->
    <div class="sop-summary">
      <div class="ring-stat">
        <div class="ring-value">{{ sopStats.completed }}/{{ sopStats.total }}</div>
        <div class="ring-label">模块完成</div>
      </div>
      <div class="ring-stat in-progress">
        <div class="ring-value">{{ sopStats.inProgress }}</div>
        <div class="ring-label">进行中</div>
      </div>
      <div class="ring-stat failed" v-if="sopStats.failed > 0">
        <div class="ring-value">{{ sopStats.failed }}</div>
        <div class="ring-label">失败</div>
      </div>
    </div>

    <!-- Module grid -->
    <div class="section">
      <h2>模块</h2>
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else class="module-grid">
        <div
          v-for="m in modules"
          :key="m.id"
          class="module-card"
          :class="m.status"
          @click="openExecution(m.id)"
        >
          <div class="module-header">
            <span class="module-name">{{ m.name }}</span>
            <span class="module-status" :class="m.status">{{ m.status }}</span>
          </div>
          <div class="module-progress">
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: m.pct + '%' }" :class="m.status"></div>
            </div>
            <span class="progress-pct">{{ m.pct }}%</span>
          </div>
          <div class="module-meta">
            <span>{{ m.pages }} 页面</span>
            <span>{{ m.phases_done }}/{{ m.phases_total }} Phase</span>
          </div>
          <div class="module-actions">
            <button class="btn-sm" @click.stop="openExecution(m.id)"><Play :size="14" /> 执行</button>
            <button class="btn-sm" @click.stop="openArtifacts(m.id)"><FolderOpen :size="14" /> 产物</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Quick nav -->
    <div class="section">
      <h2>工作区</h2>
      <div class="nav-cards">
        <router-link :to="`/projects/${projectId}/execution`" class="nav-card">
          <Play :size="18" /><span>执行中心</span>
        </router-link>
        <router-link :to="`/projects/${projectId}/observability`" class="nav-card">
          <Clock :size="18" /><span>可观测性</span>
        </router-link>
        <router-link :to="`/projects/${projectId}/artifacts`" class="nav-card">
          <FolderOpen :size="18" /><span>产物</span>
        </router-link>
        <router-link :to="`/projects/${projectId}/reports`" class="nav-card">
          <BarChart3 :size="18" /><span>报告</span>
        </router-link>
        <router-link :to="`/projects/${projectId}/knowledge`" class="nav-card">
          <Layers :size="18" /><span>知识</span>
        </router-link>
        <router-link :to="`/projects/${projectId}/settings`" class="nav-card">
          <Settings :size="18" /><span>设置</span>
        </router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.overview { padding: 24px 32px; max-width: 1200px; }
.overview-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 24px; }
.header-left { display: flex; align-items: center; gap: 10px; }
.header-left h1 { font-size: 20px; font-weight: 700; margin: 0; }

.sop-summary { display: flex; gap: 24px; margin-bottom: 32px; }
.ring-stat { text-align: center; }
.ring-value { font-size: 28px; font-weight: 700; }
.ring-label { font-size: 12px; color: var(--text-muted); }
.ring-stat.in-progress .ring-value { color: #3b82f6; }
.ring-stat.failed .ring-value { color: #ef4444; }

.section { margin-bottom: 28px; }
.section h2 { font-size: 15px; font-weight: 600; margin-bottom: 14px; }

.module-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 12px; }
.module-card {
  background: var(--bg-primary); border: 1px solid var(--border);
  border-radius: 10px; padding: 16px; cursor: pointer; transition: border-color .15s;
}
.module-card:hover { border-color: var(--accent); }
.module-card.failed { border-color: #fca5a5; }
.module-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.module-name { font-weight: 600; }
.module-status { font-size: 10px; padding: 2px 6px; border-radius: 8px; text-transform: uppercase; }
.module-status.completed { background: #d4edda; color: #155724; }
.module-status.failed { background: #f8d7da; color: #721c24; }
.module-status.in_progress, .module-status.running { background: #dbeafe; color: #1e40af; }
.module-progress { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.progress-bar { flex: 1; height: 6px; background: var(--bg-secondary); border-radius: 3px; overflow: hidden; }
.progress-fill { height: 100%; background: #3b82f6; border-radius: 3px; transition: width .3s; }
.progress-fill.completed { background: #22c55e; }
.progress-fill.failed { background: #ef4444; }
.progress-pct { font-size: 12px; color: var(--text-muted); min-width: 36px; text-align: right; }
.module-meta { display: flex; gap: 12px; font-size: 12px; color: var(--text-muted); margin-bottom: 10px; }
.module-actions { display: flex; gap: 8px; }
.btn-sm { display: flex; align-items: center; gap: 4px; font-size: 12px; padding: 4px 10px; border: 1px solid var(--border); border-radius: 6px; background: var(--bg-primary); cursor: pointer; }
.btn-sm:hover { background: var(--bg-secondary); }

.nav-cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 10px; }
.nav-card {
  display: flex; align-items: center; gap: 8px; padding: 14px 16px;
  background: var(--bg-primary); border: 1px solid var(--border);
  border-radius: 10px; text-decoration: none; color: var(--text-primary); font-size: 14px;
  transition: border-color .15s;
}
.nav-card:hover { border-color: var(--accent); }

.loading { color: var(--text-muted); padding: 16px 0; }
</style>
