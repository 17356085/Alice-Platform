<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { useProjectStore } from '../stores/project'
import { useSettingsStore } from '../stores/settings'
import { useKanbanStore } from '../stores/kanban'
import { useHealth } from '../composables/useHealth'
import { LayoutDashboard, CheckCircle, AlertTriangle, Play, BarChart3, Activity, Server } from 'lucide-vue-next'
import ProjectSelector from '../components/ProjectSelector.vue'

const projectStore = useProjectStore()
const settingsStore = useSettingsStore()
const kanbanStore = useKanbanStore()
const { health, loading: healthLoading, refresh: refreshHealth } = useHealth()

onMounted(async () => {
  await projectStore.fetchProjects()
  await kanbanStore.fetchModules()
  refreshHealth()
})

function openProject(id: string) {
  projectStore.setActive(id)
}

const stats = computed(() => {
  const mods = Object.entries(kanbanStore.modules)
  const completed = mods.filter(([, m]) => (m as any).phases_done >= (m as any).phases_total).length
  const withIssues = mods.filter(([, m]) => (m as any).failed > 0).length
  const ready = mods.filter(([, m]) => (m as any).status === 'completed_with_issues' || (m as any).status === 'ready').length
  return { total: mods.length, completed, withIssues, ready }
})

</script>

<template>
  <div class="dashboard">
    <!-- Header -->
    <div class="dashboard-header">
      <div class="header-left">
        <LayoutDashboard :size="24" />
        <h1>面板</h1>
      </div>
      <ProjectSelector />
    </div>

    <!-- Stats cards -->
    <div class="stats-grid">
      <div class="stat-card">
        <BarChart3 :size="20" class="stat-icon" />
        <div class="stat-value">{{ stats.total }}</div>
        <div class="stat-label">总模块</div>
      </div>
      <div class="stat-card green">
        <CheckCircle :size="20" class="stat-icon" />
        <div class="stat-value">{{ stats.completed }}</div>
        <div class="stat-label">已完成</div>
      </div>
      <div class="stat-card yellow">
        <AlertTriangle :size="20" class="stat-icon" />
        <div class="stat-value">{{ stats.withIssues }}</div>
        <div class="stat-label">待修复</div>
      </div>
      <div class="stat-card blue">
        <Play :size="20" class="stat-icon" />
        <div class="stat-value">{{ stats.ready }}</div>
        <div class="stat-label">就绪</div>
      </div>
    </div>

    <!-- Platform Health (from /health endpoint) -->
    <div class="section">
      <div class="section-header">
        <h2><Activity :size="16" /> 平台状态</h2>
        <button class="btn-refresh" @click="refreshHealth" :disabled="healthLoading">刷新</button>
      </div>
      <div v-if="healthLoading && !health" class="loading">加载中...</div>
      <div v-else-if="health" class="health-grid">
        <div class="health-card">
          <span class="health-dot" :class="health.status"></span>
          <span class="health-label">整体状态</span>
          <span class="health-value">{{ health.status === 'healthy' ? '正常' : '降级' }}</span>
        </div>
        <div v-if="health.components.llm" class="health-card">
          <span class="health-dot ok"></span>
          <span class="health-label">LLM</span>
          <span class="health-value">{{ health.components.llm.resolved_provider || '?' }}</span>
          <span v-if="health.components.llm.circuit_breakers?.open" class="health-warn">
            {{ health.components.llm.circuit_breakers.open }} 熔断
          </span>
        </div>
        <div v-if="health.components.worker_pool" class="health-card">
          <span class="health-dot" :class="health.components.worker_pool.status"></span>
          <span class="health-label">Worker Pool</span>
          <span class="health-value">
            活跃 {{ health.components.worker_pool.active }}/{{ health.components.worker_pool.max_workers }}
          </span>
        </div>
        <div v-if="health.components.tenants" class="health-card">
          <span class="health-dot ok"></span>
          <span class="health-label">项目数</span>
          <span class="health-value">{{ health.components.tenants.count }}</span>
        </div>
      </div>
      <div v-else class="muted">后端未连接 — 启动 <code>aitest server start</code></div>
    </div>

    <!-- Project list -->
    <div class="section">
      <h2>项目列表</h2>
      <div v-if="projectStore.loading" class="loading">加载中...</div>
      <div v-else-if="!projectStore.hasProjects" class="empty-state">
        <p>暂无项目。创建一个新项目开始。</p>
        <router-link to="/onboarding" class="btn-primary">+ 新建项目</router-link>
      </div>
      <div v-else class="project-cards">
        <div
          v-for="p in projectStore.projects"
          :key="p.id"
          class="project-card"
          :class="{ active: p.id === projectStore.activeId }"
          @click="openProject(p.id)"
        >
          <div class="card-header">
            <span class="card-name">{{ p.name || p.id }}</span>
            <span v-if="p.status" class="badge" :class="p.status">{{ p.status }}</span>
          </div>
          <div class="card-body">
            <span>模块: {{ p.modules?.length || 0 }}</span>
            <span v-if="p.updated_at">更新: {{ p.updated_at?.slice(0, 10) }}</span>
          </div>
          <div class="card-footer">
            <router-link :to="`/workspace/kanban`" class="card-link" @click.stop="openProject(p.id)">
              进入工作区 →
            </router-link>
          </div>
        </div>
      </div>
    </div>

    <!-- Quick actions -->
    <div class="section">
      <h2>快速操作</h2>
      <div class="quick-actions">
        <router-link to="/onboarding" class="action-card">
          <span class="action-icon">🔍</span>
          <span class="action-text">发现新项目</span>
        </router-link>
        <router-link to="/workspace/kanban" class="action-card">
          <span class="action-icon">▶️</span>
          <span class="action-text">运行 SOP</span>
        </router-link>
        <router-link to="/workspace/reports" class="action-card">
          <span class="action-icon">📊</span>
          <span class="action-text">查看报告</span>
        </router-link>
        <router-link to="/settings" class="action-card">
          <span class="action-icon">⚙️</span>
          <span class="action-text">平台设置</span>
        </router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard { padding: 24px 32px; max-width: 1200px; }
.dashboard-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 24px; }
.header-left { display: flex; align-items: center; gap: 10px; }
.header-left h1 { font-size: 22px; font-weight: 700; margin: 0; }

.stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 32px; }
.stat-card {
  background: var(--bg-primary); border: 1px solid var(--border);
  border-radius: 12px; padding: 20px; text-align: center;
}
.stat-icon { margin-bottom: 8px; opacity: .7; }
.stat-value { font-size: 28px; font-weight: 700; }
.stat-label { font-size: 12px; color: var(--text-muted); margin-top: 4px; }
.stat-card.green .stat-icon { color: #22c55e; }
.stat-card.yellow .stat-icon { color: #eab308; }
.stat-card.blue .stat-icon { color: #3b82f6; }

.section { margin-bottom: 32px; }
.section h2 { font-size: 16px; font-weight: 600; margin-bottom: 16px; }

.project-cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px; }
.project-card {
  background: var(--bg-primary); border: 2px solid var(--border);
  border-radius: 12px; padding: 16px; cursor: pointer; transition: border-color .15s, box-shadow .15s;
}
.project-card:hover { border-color: var(--accent); box-shadow: 0 2px 8px rgba(0,0,0,.08); }
.project-card.active { border-color: var(--accent); }
.card-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
.card-name { font-weight: 600; }
.badge { font-size: 10px; padding: 2px 8px; border-radius: 10px; text-transform: uppercase; }
.badge.completed { background: #d4edda; color: #155724; }
.badge.issues, .badge.completed_with_issues { background: #fff3cd; color: #856404; }
.card-body { display: flex; gap: 16px; font-size: 12px; color: var(--text-muted); margin-bottom: 12px; }
.card-footer { text-align: right; }
.card-link { font-size: 13px; color: var(--accent); text-decoration: none; }

.quick-actions { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.action-card {
  display: flex; flex-direction: column; align-items: center; gap: 8px;
  padding: 20px; background: var(--bg-primary); border: 1px solid var(--border);
  border-radius: 12px; text-decoration: none; color: var(--text-primary);
  transition: background .15s;
}
.action-card:hover { background: var(--bg-secondary); }

/* Platform health */
.section-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.section-header h2 { display: flex; align-items: center; gap: 6px; margin: 0; }
.btn-refresh { font-size: 12px; padding: 4px 12px; border: 1px solid var(--border); border-radius: 6px; background: var(--bg-primary); cursor: pointer; }
.health-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; }
.health-card {
  display: flex; align-items: center; gap: 8px;
  padding: 12px 16px; background: var(--bg-primary); border: 1px solid var(--border); border-radius: 10px;
}
.health-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.health-dot.healthy, .health-dot.ok { background: #22c55e; }
.health-dot.degraded { background: #eab308; }
.health-dot.error { background: #ef4444; }
.health-label { font-size: 12px; color: var(--text-muted); min-width: 60px; }
.health-value { font-size: 13px; font-weight: 600; }
.health-warn { font-size: 11px; color: #ef4444; background: #fef2f2; padding: 1px 6px; border-radius: 4px; margin-left: auto; }
.loading { color: var(--text-muted); padding: 12px 0; }
.muted { color: var(--text-muted); font-size: 13px; padding: 12px 0; }
.muted code { background: var(--bg-secondary); padding: 2px 6px; border-radius: 3px; }
.action-icon { font-size: 24px; }
.action-text { font-size: 13px; font-weight: 500; }

.loading, .empty-state { text-align: center; padding: 40px; color: var(--text-muted); }
.btn-primary {
  display: inline-block; margin-top: 12px; padding: 8px 20px;
  background: var(--accent); color: #fff; border-radius: 8px; text-decoration: none; font-size: 13px;
}
</style>
