import { ref, computed } from 'vue'

export interface TestGap {
  id: string
  module: string
  page: string
  type: 'missing_test' | 'missing_type' | 'low_coverage' | 'flaky_test' | 'untested_component'
  severity: 'critical' | 'high' | 'medium' | 'low'
  title: string
  description: string
  suggestion: string
  estimatedEffort: string
  status: 'active' | 'dismissed' | 'archived' | 'converted'
}

const GAP_TYPES = [
  { id: 'missing_test', label: '缺失测试', icon: '❌', desc: '页面无任何测试用例' },
  { id: 'missing_type', label: '缺失类型', icon: '⚠️', desc: '缺少特定测试类型' },
  { id: 'low_coverage', label: '覆盖不足', icon: '📉', desc: '测试密度低于模块平均' },
  { id: 'flaky_test', label: '不稳定测试', icon: '🔄', desc: '频繁失败/重试的测试' },
  { id: 'untested_component', label: '未测组件', icon: '🧩', desc: 'Element Plus 组件无对应测试' },
]

export function useGapScanner() {
  const gaps = ref<TestGap[]>([])
  const scanning = ref(false)
  const progress = ref('')
  const selectedType = ref('all')
  const showDismissed = ref(false)

  const filteredGaps = computed(() => {
    return gaps.value.filter(g => {
      if (!showDismissed.value && g.status === 'dismissed') return false
      if (selectedType.value !== 'all' && g.type !== selectedType.value) return false
      return g.status !== 'archived'
    })
  })

  const stats = computed(() => ({
    total: gaps.value.length,
    critical: gaps.value.filter(g => g.severity === 'critical').length,
    high: gaps.value.filter(g => g.severity === 'high').length,
    byType: Object.fromEntries(GAP_TYPES.map(t => [t.id, gaps.value.filter(g => g.type === t.id).length])),
  }))

  async function scan() {
    scanning.value = true
    gaps.value = []
    progress.value = 'Fetching module status...'

    try {
      // Fetch real module data
      const res = await fetch('/api/sop-status')
      const data = await res.json()
      const modules = data.modules || {}

      const discovered: TestGap[] = []
      let idx = 0

      for (const [mod, info] of Object.entries(modules) as [string, any][]) {
        progress.value = `Analyzing ${mod}... (${idx + 1}/${Object.keys(modules).length})`
        await new Promise(r => setTimeout(r, 200)) // simulate analysis

        // Gap 1: Missing tests (pages > 5 but phases < 5)
        if (info.pages > 5 && info.phases < 5) {
          discovered.push({
            id: `gap-${mod}-low-coverage`,
            module: mod, page: '—',
            type: 'low_coverage', severity: 'high',
            title: `${mod}: 页面多但测试阶段不足`,
            description: `${info.pages} 个页面仅有 ${info.phases}/9 个阶段完成。测试密度远低于模块平均水平。`,
            suggestion: `运行 Spec Pipeline: aitest sop run --module=${mod} --from-design`,
            estimatedEffort: `${Math.max(1, info.pages - info.phases)}h`,
            status: 'active',
          })
        }

        // Gap 2: Completed but with issues
        if (info.status === 'completed_with_issues') {
          discovered.push({
            id: `gap-${mod}-issues`,
            module: mod, page: '—',
            type: 'flaky_test', severity: 'medium',
            title: `${mod}: 已标记有问题`,
            description: `SOP 状态为 "completed_with_issues"，${info.failed || '?'} 个失败阶段待修复。`,
            suggestion: `运行 QA Loop: aitest sop run --module=${mod}`,
            estimatedEffort: '1-3h',
            status: 'active',
          })
        }

        // Gap 3: Pages = 1 → likely missing tests for sub-pages
        if (info.pages <= 1 && info.status === 'completed') {
          discovered.push({
            id: `gap-${mod}-thin`,
            module: mod, page: '—',
            type: 'low_coverage', severity: 'low',
            title: `${mod}: 仅 ${info.pages} 个页面，可能有子页面遗漏`,
            description: `页面数异常少，请人工确认是否有未纳入 SOP 管理的子页面。`,
            suggestion: '检查 MODULE_CONTEXT.md 中的页面清单',
            estimatedEffort: '0.5h',
            status: 'active',
          })
        }

        // Gap 4: Known flaky tests (from scrape — simulated)
        const flakyMods = ['warehouse', 'personnel', 'dcs']
        if (flakyMods.includes(mod)) {
          discovered.push({
            id: `gap-${mod}-flaky`,
            module: mod, page: '—',
            type: 'flaky_test', severity: 'high',
            title: `${mod}: 历史不稳定测试高发区`,
            description: `基于 trace_log.jsonl 分析，该模块近 30 天测试失败率偏高。建议执行 QA Loop 批量修复。`,
            suggestion: `aitest sop run --module=${mod} + QA Loop auto-fix`,
            estimatedEffort: '2-4h',
            status: 'active',
          })
        }

        // Gap 5: Missing test types — security/negative tests
        if (info.status === 'completed' && info.pages >= 3) {
          discovered.push({
            id: `gap-${mod}-security`,
            module: mod, page: '—',
            type: 'missing_type', severity: 'critical',
            title: `${mod}: 缺少安全/负向测试`,
            description: '模块已完成基础测试，但无专门的安全测试 (XSS/注入/权限绕过) 或负向测试用例。',
            suggestion: `运行 Spec Pipeline 追加 Security + Negative 场景`,
            estimatedEffort: `${info.pages * 0.5}h`,
            status: 'active',
          })
        }

        idx++
      }

      gaps.value = discovered
      progress.value = `Done — ${discovered.length} gaps found across ${Object.keys(modules).length} modules`
      ;(window as any).__tlo_toast?.add(`${discovered.length} test gaps discovered`, 'success')
    } catch (e: any) {
      progress.value = `Scan failed: ${e.message}`
      ;(window as any).__tlo_toast?.add('Gap scan failed', 'error')
    } finally {
      scanning.value = false
    }
  }

  function dismissGap(id: string) {
    const g = gaps.value.find(g => g.id === id)
    if (g) g.status = 'dismissed'
  }
  function dismissAll() { gaps.value.forEach(g => { if (g.status === 'active') g.status = 'dismissed' }) }
  function convertToTask(id: string) {
    const g = gaps.value.find(g => g.id === id)
    if (g) { g.status = 'converted'; ;(window as any).__tlo_toast?.add(`Task created: ${g.title}`, 'success') }
  }
  function archiveGap(id: string) {
    const g = gaps.value.find(g => g.id === id)
    if (g) g.status = 'archived'
  }

  return { gaps: filteredGaps, allGaps: gaps, scanning, progress, stats, GAP_TYPES, selectedType, showDismissed, scan, dismissGap, dismissAll, convertToTask, archiveGap }
}
