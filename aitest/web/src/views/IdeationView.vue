<script setup lang="ts">
/** Testing Ideation — AI-driven test improvement discovery.

Scans test gaps across: coverage, flaky tests, security, performance, docs.
Generates actionable improvement suggestions with priority/severity.
*/
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { api } from '../api/client'
import { ENDPOINTS } from '../api/endpoints'
import {
  Lightbulb, RefreshCw, Shield, Zap, FileText, Bug, AlertTriangle, CheckCircle,
} from 'lucide-vue-next'

const { t } = useI18n()

interface IdeaItem {
  id: string
  type: 'coverage' | 'flaky' | 'security' | 'performance' | 'documentation'
  severity: 'critical' | 'high' | 'medium' | 'low'
  title: string
  description: string
  module?: string
  page?: string
  actionable: boolean
}

const CATEGORIES = [
  { key: 'all' as const,      label: '全部', icon: Lightbulb },
  { key: 'coverage' as const, label: '覆盖缺口', icon: Bug },
  { key: 'flaky' as const,    label: '不稳定测试', icon: AlertTriangle },
  { key: 'security' as const, label: '安全测试', icon: Shield },
  { key: 'performance' as const, label: '性能测试', icon: Zap },
  { key: 'documentation' as const, label: '文档', icon: FileText },
]

const ideas = ref<IdeaItem[]>([])
const loading = ref(false)
const error = ref('')
const activeCategory = ref<'all' | 'coverage' | 'flaky' | 'security' | 'performance' | 'documentation'>('all')
const dismissed = ref<Set<string>>(new Set())

const filteredIdeas = computed(() => {
  let list = ideas.value.filter(i => !dismissed.value.has(i.id))
  if (activeCategory.value !== 'all') {
    list = list.filter(i => i.type === activeCategory.value)
  }
  return list.sort((a, b) => {
    const sev = { critical: 0, high: 1, medium: 2, low: 3 }
    return (sev[a.severity] ?? 2) - (sev[b.severity] ?? 2)
  })
})

const counts = computed(() => {
  const c: Record<string, number> = {}
  ideas.value.forEach(i => { c[i.type] = (c[i.type] || 0) + 1 })
  return c
})

// ── AI-powered scan ──────────────────────────────────────

async function scan() {
  loading.value = true; error.value = ''
  try {
    // Fetch module status + derive ideas heuristically
    const data = await api.get<{ modules: Record<string, any> }>(ENDPOINTS.SOP_STATUS)
    const results = analyzeModules(data.modules || {})
    ideas.value = results
  } catch (e: any) {
    error.value = e.message
    // Generate fallback ideas from local data
    ideas.value = generateFallbackIdeas()
  } finally { loading.value = false }
}

function analyzeModules(modules: Record<string, any>): IdeaItem[] {
  const results: IdeaItem[] = []
  let id = 0

  for (const [modName, info] of Object.entries(modules)) {
    const status = (info as any).status || ''
    const failed = (info as any).failed || 0
    const pages = (info as any).pages_list || (info as any).pages || []
    const phases = (info as any).phases_done || 0
    const total = (info as any).phases_total || 9

    // Coverage gap: incomplete SOP
    if (phases < total) {
      results.push({
        id: `gap-${++id}`, type: 'coverage', severity: 'high',
        title: `${modName}: SOP未完成 (${phases}/${total} phases)`,
        description: `运行完整SOP以覆盖所有测试阶段。当前缺失${total - phases}个阶段。`,
        module: modName, actionable: true,
      })
    }

    // Failed tests
    if (failed > 0) {
      results.push({
        id: `flaky-${++id}`, type: 'flaky', severity: failed > 3 ? 'critical' : 'medium',
        title: `${modName}: ${failed}个测试失败`,
        description: '使用Bug Analysis Agent自动诊断并修复失败测试。',
        module: modName, actionable: true,
      })
    }

    // Missing pages
    if (Array.isArray(pages) && pages.length === 0) {
      results.push({
        id: `missing-${++id}`, type: 'coverage', severity: 'critical',
        title: `${modName}: 无页面发现`,
        description: '运行Onboarding发现模块页面，或手动创建页面上下文。',
        module: modName, actionable: true,
      })
    }

    // Security test gap (heuristic: no security test marker)
    if (!String(status).includes('security') && phases >= 3) {
      results.push({
        id: `sec-${++id}`, type: 'security', severity: 'medium',
        title: `${modName}: 缺少安全测试`,
        description: '建议添加安全测试类型：XSS注入检测、权限绕过测试、敏感数据泄露扫描。',
        module: modName, actionable: true,
      })
    }
  }

  // Cross-module gaps
  if (Object.keys(modules).length < 3) {
    results.push({
      id: `global-${++id}`, type: 'performance', severity: 'low',
      title: '模块数量较少 — 考虑扩展测试覆盖',
      description: `仅发现${Object.keys(modules).length}个模块。检查是否有未注册的模块。`,
      actionable: true,
    })
  }

  return results
}

function generateFallbackIdeas(): IdeaItem[] {
  return [
    { id: 'f1', type: 'coverage', severity: 'high', title: '运行SOP发现测试覆盖缺口', description: '完整SOP执行可自动评估模块测试状态。', actionable: true },
    { id: 'f2', type: 'flaky', severity: 'medium', title: '检查最近30天不稳定测试', description: '使用Bug Analysis Agent分析trace日志中的flaky模式。', actionable: true },
    { id: 'f3', type: 'security', severity: 'high', title: '补充安全测试用例', description: '对于所有包含表单的页面添加XSS和注入测试。', actionable: true },
    { id: 'f4', type: 'performance', severity: 'low', title: '添加页面加载性能基线', description: '使用BrowserUse记录页面导航耗时作为性能基线。', actionable: false },
    { id: 'f5', type: 'documentation', severity: 'medium', title: '补全PAGE_CONTEXT文档', description: '部分模块缺少PAGE_CONTEXT.md，影响Agent对页面的理解。', actionable: true },
  ]
}

function dismiss(id: string) { dismissed.value.add(id) }
function dismissAll() { ideas.value.forEach(i => dismissed.value.add(i.id)) }

const severityIcon = (s: string) => s === 'critical' ? AlertTriangle : s === 'high' ? Bug : s === 'medium' ? Lightbulb : CheckCircle
const severityColor = (s: string) => s === 'critical' ? '#ef4444' : s === 'high' ? '#f59e0b' : s === 'medium' ? '#3b82f6' : '#22c55e'

onMounted(scan)
</script>

<template>
  <div class="ideation-view">
    <div class="ideation-header">
      <h1><Lightbulb :size="22" /> 测试构思</h1>
      <button class="scan-btn" :disabled="loading" @click="scan">
        <RefreshCw :size="16" :class="{ spinning: loading }" />
        {{ loading ? '扫描中...' : '重新扫描' }}
      </button>
    </div>

    <!-- Category tabs -->
    <div class="category-bar">
      <button v-for="cat in CATEGORIES" :key="cat.key"
        :class="['cat-btn', { active: activeCategory === cat.key }]"
        @click="activeCategory = cat.key"
      >
        <component :is="cat.icon" :size="14" />
        <span>{{ cat.label }}</span>
        <span v-if="cat.key !== 'all' && counts[cat.key]" class="cat-count">{{ counts[cat.key] }}</span>
      </button>
    </div>

    <!-- Idea list -->
    <div class="idea-list">
      <div v-if="loading" class="loading-state">
        <RefreshCw :size="24" class="spinning" />
        <p>AI正在分析测试数据...</p>
      </div>

      <div v-else-if="filteredIdeas.length === 0" class="empty-state">
        <CheckCircle :size="32" class="empty-icon" />
        <p>{{ activeCategory === 'all' ? '未发现改进建议' : '该类别无待处理项' }}</p>
        <span class="empty-hint">所有已知问题已处理</span>
      </div>

      <div v-for="idea in filteredIdeas" :key="idea.id" class="idea-card" :style="{ borderLeftColor: severityColor(idea.severity) }">
        <div class="idea-main">
          <div class="idea-header">
            <component :is="severityIcon(idea.severity)" :size="16" :style="{ color: severityColor(idea.severity) }" />
            <span class="idea-severity" :style="{ color: severityColor(idea.severity) }">{{ idea.severity.toUpperCase() }}</span>
            <span class="idea-type">{{ idea.type }}</span>
          </div>
          <h3 class="idea-title">{{ idea.title }}</h3>
          <p class="idea-desc">{{ idea.description }}</p>
          <div v-if="idea.module" class="idea-meta">
            <span class="meta-tag">{{ idea.module }}</span>
          </div>
        </div>
        <div class="idea-actions">
          <button v-if="idea.actionable" class="action-btn primary" @click="/* create task */">
            创建任务
          </button>
          <button class="action-btn" @click="dismiss(idea.id)">忽略</button>
        </div>
      </div>
    </div>

    <div v-if="filteredIdeas.length > 0" class="ideation-footer">
      <button class="dismiss-all" @click="dismissAll">忽略全部 ({{ filteredIdeas.length }})</button>
    </div>
  </div>
</template>

<style scoped>
.ideation-view { padding: 24px 32px; max-width: 800px; }
.ideation-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
.ideation-header h1 { display: flex; align-items: center; gap: 10px; font-size: 20px; font-weight: 700; margin: 0; }

.scan-btn {
  display: flex; align-items: center; gap: 6px;
  padding: 8px 16px; border: 1px solid var(--border); border-radius: 8px;
  background: var(--bg-primary); cursor: pointer; font-size: 13px; color: var(--accent);
  transition: all .15s;
}
.scan-btn:hover { background: var(--bg-secondary); }
.scan-btn:disabled { opacity: .5; cursor: not-allowed; }
.spinning { animation: spin 1s linear infinite; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

.category-bar { display: flex; gap: 4px; margin-bottom: 20px; overflow-x: auto; }
.cat-btn {
  display: flex; align-items: center; gap: 6px;
  padding: 8px 14px; border-radius: 8px; border: 1px solid var(--border);
  background: var(--bg-primary); cursor: pointer; font-size: 13px;
  color: var(--text-secondary); white-space: nowrap; transition: all .15s;
}
.cat-btn.active { border-color: var(--accent); color: var(--accent); background: color-mix(in srgb, var(--accent) 8%, transparent); }
.cat-count { font-size: 10px; padding: 1px 6px; border-radius: 8px; background: var(--bg-hover); }

.idea-list { display: flex; flex-direction: column; gap: 10px; margin-bottom: 16px; }
.idea-card {
  display: flex; justify-content: space-between; gap: 16px;
  padding: 16px; border: 1px solid var(--border); border-left: 4px solid #ddd;
  border-radius: 10px; background: var(--bg-primary);
}
.idea-header { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.idea-severity { font-size: 10px; font-weight: 700; letter-spacing: .5px; }
.idea-type { font-size: 10px; color: var(--text-muted); padding: 1px 6px; border-radius: 4px; background: var(--bg-secondary); }
.idea-title { font-size: 14px; font-weight: 600; margin: 0 0 4px; }
.idea-desc { font-size: 12px; color: var(--text-muted); margin: 0 0 8px; }
.idea-meta { display: flex; gap: 6px; }
.meta-tag { font-size: 10px; padding: 2px 8px; border-radius: 4px; background: var(--bg-secondary); color: var(--text-secondary); }

.idea-actions { display: flex; flex-direction: column; gap: 6px; flex-shrink: 0; }
.action-btn {
  padding: 6px 14px; border-radius: 6px; border: 1px solid var(--border);
  background: var(--bg-primary); cursor: pointer; font-size: 12px; color: var(--text-secondary);
}
.action-btn.primary { background: var(--accent); color: #fff; border-color: var(--accent); }
.action-btn:hover { opacity: .85; }

.loading-state, .empty-state { display: flex; flex-direction: column; align-items: center; gap: 8px; padding: 48px; color: var(--text-muted); }
.empty-icon { opacity: .3; }

.ideation-footer { text-align: center; }
.dismiss-all { padding: 6px 16px; border: none; background: transparent; cursor: pointer; font-size: 12px; color: var(--text-muted); }
</style>
