export const meta = {
  name: 'full-sop',
  description: '端到端 SOP 编排器 — 按 Phase 0→9 自动串联 8 个 Agent。与 AITest sop_graph.py 10 节点完全对齐。v5.0: 补齐 Execute & Debug + Bug Analysis + Data Sanitization',
  phases: [
    { title: 'Preflight', detail: '前置检查 + 断点恢复 + 页面发现' },
    { title: 'Orchestrate', detail: 'project → requirement → test-design (per page) → automation (per page)' },
    { title: 'Execute & Debug', detail: 'pytest + Allure 报告收集 → 失败检测' },
    { title: 'Bug Analysis', detail: '失败根因分析 + automation-agent fix → re-execute (≤3轮)', condition: 'execution_failed' },
    { title: 'Data Sanitization', detail: 'scan_and_clean.py --force 离线扫描清理残留数据' },
    { title: 'Report', detail: '/report-agent — TEST_SUMMARY + 综合 Excel' },
    { title: 'Knowledge', detail: '/knowledge-agent — 经验沉淀 + Event Bus 处理' },
  ],
}

// ═══════════════════════════════════════════════════════════
// 参数解析
// ═══════════════════════════════════════════════════════════
const PROJECT = args?.project || 'web-automation'
const MODULE = args?.module
const MODE = args?.mode || 'full'
const USER_PAGES = args?.pages

if (!MODULE) {
  log('❌ 缺少必填参数: module')
  log('用法: /full-sop module=<模块名> [mode=full|resume|status|from-requirement|from-test-design|from-automation] [pages=<页面1,页面2>]')
  throw new Error('Missing required arg: module')
}

const PROJECT_DIR = `governance/context/projects/${PROJECT}`
const MODULE_DIR = `${PROJECT_DIR}/modules/${MODULE}`
const STATUS_FILE = `governance/artifacts/sop-status/SOP_STATUS_${MODULE}.json`

// ═══════════════════════════════════════════════════════════
// Phase 1: Preflight — 前置检查 + 进度探测
// ═══════════════════════════════════════════════════════════
phase('Preflight')

// 快速检查核心文件是否存在（不消耗 LLM token）
const preflight = await agent(
  `检查模块 ${MODULE} 的 SOP 前置条件。

## 任务
1. Read ${STATUS_FILE} — 如果存在，读取当前进度
2. Read ${PROJECT_DIR}/PROJECT_CONTEXT.md 的 project-profile.md — 确认项目上下文存在
3. Read ${PROJECT_DIR}/MODULE_INDEX.md — 确认模块已注册
4. 检查 ${MODULE_DIR}/ 是否存在、包含哪些页面子目录
5. 列出 ZJSN_Test-master526/page/${MODULE}_page/ 和 script/${MODULE}/ 的现有文件

## 输出 JSON
{
  "project_ok": true,
  "module_indexed": true,
  "module_dir_exists": true/false,
  "pages": [{"slug": "...", "has_page_context": false, "has_test_cases": false, "has_tech_analysis": false}],
  "existing_page_files": [],
  "existing_test_files": [],
  "status_file": {"exists": false, "current_phase": null, "completed_phases": []}
}`,
  {
    label: 'preflight',
    model: 'haiku',
    phase: 'Preflight',
    schema: {
      type: 'object',
      properties: {
        project_ok: { type: 'boolean' },
        module_indexed: { type: 'boolean' },
        module_dir_exists: { type: 'boolean' },
        pages: { type: 'array', items: { type: 'object' } },
        existing_page_files: { type: 'array', items: { type: 'string' } },
        existing_test_files: { type: 'array', items: { type: 'string' } },
        status_file: { type: 'object' },
      },
      required: ['project_ok', 'pages'],
    },
  }
)

log(`📋 模块 "${MODULE}": ${preflight.pages?.length || 0} 页面, ` +
    `项目${preflight.project_ok ? 'OK' : '需初始化'}, ` +
    `状态${preflight.status_file?.exists ? ': ' + preflight.status_file.current_phase : ': 新模块'}`)

// status 模式: 仅展示进度
if (MODE === 'status') {
  log(`页面详情:`)
  for (const p of (preflight.pages || [])) {
    const docs = [p.has_page_context, p.has_test_cases, p.has_tech_analysis].filter(Boolean).length
    log(`  ${p.slug}: ${docs}/3 核心文档`)
  }
  return { module: MODULE, mode: 'status', preflight }
}

// 收集页面列表
let pages = USER_PAGES || (preflight.pages || []).filter(p => p.slug).map(p => p.slug) || []
log(`📋 页面清单 (${pages.length}): ${pages.join(', ') || '(无页面)'}`)

// ═══════════════════════════════════════════════════════════
// Phase 2: Orchestrate — workflow_engine DAG + AgentLoop
// ═══════════════════════════════════════════════════════════
phase('Orchestrate')

// 确定需要执行的 Agent 阶段
const SKIP_PROJECT = ['from-requirement', 'from-test-design', 'from-automation'].includes(MODE)
const SKIP_REQUIREMENT = ['from-test-design', 'from-automation'].includes(MODE)
const SKIP_TEST_DESIGN = ['from-automation'].includes(MODE)

// 构建执行计划
const executionPlan = []

if (!SKIP_PROJECT && !preflight.project_ok) {
  executionPlan.push({ agent: 'project-agent', phase: 'Project Init', args: 'mode=init' })
}
if (!SKIP_REQUIREMENT && !preflight.module_dir_exists) {
  executionPlan.push({ agent: 'requirement-agent', phase: 'Module Modeling', args: `module=${MODULE}` })
}

// 对每个页面执行 test-design → automation pipeline
for (const page of pages) {
  if (!SKIP_TEST_DESIGN) {
    const pageInfo = (preflight.pages || []).find(p => p.slug === page || p.name === page) || {}
    if (!pageInfo.has_page_context || !pageInfo.has_test_cases) {
      executionPlan.push({ agent: 'test-design-agent', phase: 'Test Design', args: `module=${MODULE} page=${page}` })
    }
  }
  const pageInfo = (preflight.pages || []).find(p => p.slug === page || p.name === page) || {}
  if (!pageInfo.has_tech_analysis) {
    executionPlan.push({ agent: 'automation-agent', phase: 'Automation', args: `module=${MODULE} pageName=${page}` })
  }
}

// 执行计划
let completed = 0
let failed = 0

if (executionPlan.length === 0) {
  log('✅ 所有前置产物已就绪，跳过编排')
} else {
  log(`🔄 执行计划: ${executionPlan.length} 步骤`)

  for (const step of executionPlan) {
    log(`  ▶ ${step.phase}: ${step.agent} ${step.args}`)

    try {
      const result = await agent(
        `调用 Skill 工具执行斜杠命令: /${step.agent} ${step.args}

完成后汇报 JSON:
{
  "agent": "${step.agent}",
  "phase": "${step.phase}",
  "status": "completed",
  "summary": ""
}`,
        {
          label: `${step.agent.split('-')[0]}:${step.args}`,
          phase: 'Orchestrate',
          schema: {
            type: 'object',
            properties: {
              agent: { type: 'string' },
              phase: { type: 'string' },
              status: { type: 'string' },
              summary: { type: 'string' },
            },
            required: ['status'],
          },
        }
      )
      completed++
      log(`  ✅ ${step.phase} 完成`)
    } catch (e) {
      failed++
      log(`  ❌ ${step.phase} 失败: ${e.message?.substring(0, 100)}`)
    }
  }

  log(`📊 编排结果: ${completed} 完成 / ${failed} 失败`)
}

// 写入进度状态
const statusPayload = {
  module: MODULE,
  status: failed > 0 ? 'completed_with_issues' : 'completed',
  current_phase: 'Report',
  completed_phases: ['Preflight', 'Orchestrate'],
  pages_processed: pages,
  steps: { completed, failed },
}

await agent(
  `Write SOP status to ${STATUS_FILE}:
\`\`\`json
${JSON.stringify(statusPayload, null, 2)}
\`\`\`
用 Write 工具写入。完成后返回 {"written": true}`,
  {
    label: 'write-status',
    model: 'haiku',
    schema: { type: 'object', properties: { written: { type: 'boolean' } }, required: ['written'] },
  }
)

// ═══════════════════════════════════════════════════════════
// Phase 3: Execute & Debug — 测试执行 + 失败检测
// ═══════════════════════════════════════════════════════════
phase('Execute & Debug')

log('▶ 执行测试...')
const execResult = await agent(
  `调用 Skill 工具执行斜杠命令: /execution-agent module=${MODULE}

执行完成后汇报 JSON:
{
  "status": "completed",
  "execution_failed": false,
  "failed_count": 0,
  "allure_results_exist": true,
  "summary": ""
}`,
  {
    label: `exec:${MODULE}`,
    phase: 'Execute & Debug',
    schema: {
      type: 'object',
      properties: {
        status: { type: 'string' },
        execution_failed: { type: 'boolean' },
        failed_count: { type: 'number' },
        allure_results_exist: { type: 'boolean' },
        summary: { type: 'string' },
      },
      required: ['status', 'execution_failed'],
    },
  }
)

let execFailed = execResult?.execution_failed || false
const failedCount = execResult?.failed_count || 0
log(`  ${execFailed ? '❌ ' + failedCount + ' failed' : '✅ All passed'}`)

// ═══════════════════════════════════════════════════════════
// Phase 4: Bug Analysis — 失败根因分析 + 自动修复循环 (≤3轮)
// ═══════════════════════════════════════════════════════════
let fixRounds = 0
const MAX_FIX_ROUNDS = 3
const fixLog = []

while (execFailed && fixRounds < MAX_FIX_ROUNDS) {
  fixRounds++
  phase('Bug Analysis')
  log('🔍 Bug Analysis 第 ' + fixRounds + '/' + MAX_FIX_ROUNDS + ' 轮')

  // Step 4a: 分析失败原因
  const bugResult = await agent(
    `调用 Skill 工具执行斜杠命令: /bug-analysis-agent module=${MODULE}

完成后汇报 JSON:
{
  "analyzed": true,
  "total_failures": 0,
  "auto_fixable": 0,
  "not_auto_fixable": 0,
  "auto_fixable_items": ["file:reason", ...],
  "summary": ""
}`,
    {
      label: 'bug:' + MODULE + ':r' + fixRounds,
      phase: 'Bug Analysis',
      schema: {
        type: 'object',
        properties: {
          analyzed: { type: 'boolean' },
          total_failures: { type: 'number' },
          auto_fixable: { type: 'number' },
          not_auto_fixable: { type: 'number' },
          auto_fixable_items: { type: 'array', items: { type: 'string' } },
          summary: { type: 'string' },
        },
        required: ['analyzed'],
      },
    }
  )

  const autoFixable = bugResult?.auto_fixable || 0
  log('  ' + (bugResult?.total_failures || 0) + ' failures: ' + autoFixable + ' auto-fixable, ' + (bugResult?.not_auto_fixable || 0) + ' not fixable')

  // Step 4b: 如果有可自动修复的 → 调用 automation-agent fix 模式
  if (autoFixable > 0) {
    log('🔧 自动修复 ' + autoFixable + ' 项...')
    const fixResult = await agent(
      `调用 Skill 工具执行斜杠命令: /automation-agent module=${MODULE} mode=fix

修复完成后汇报 JSON:
{
  "fixed": true,
  "files_fixed": [],
  "summary": ""
}`,
      {
        label: 'fix:' + MODULE + ':r' + fixRounds,
        phase: 'Bug Analysis',
        schema: {
          type: 'object',
          properties: {
            fixed: { type: 'boolean' },
            files_fixed: { type: 'array', items: { type: 'string' } },
            summary: { type: 'string' },
          },
          required: ['fixed'],
        },
      }
    )
    fixLog.push({ round: fixRounds, fixed: fixResult?.files_fixed || [] })
    log('  修复文件: ' + (fixResult?.files_fixed || []).join(', ') || 'none')

    // Step 4c: 重新执行测试验证修复
    log('🔄 重新执行验证...')
    const reExec = await agent(
      `调用 Skill 工具执行斜杠命令: /execution-agent module=${MODULE}

执行完成后汇报 JSON:
{
  "status": "completed",
  "execution_failed": false,
  "failed_count": 0,
  "summary": ""
}`,
      {
        label: 'reexec:' + MODULE + ':r' + fixRounds,
        phase: 'Bug Analysis',
        schema: {
          type: 'object',
          properties: {
            status: { type: 'string' },
            execution_failed: { type: 'boolean' },
            failed_count: { type: 'number' },
            summary: { type: 'string' },
          },
          required: ['status', 'execution_failed'],
        },
      }
    )
    execFailed = reExec?.execution_failed || false
    log('  ' + (execFailed ? '❌ Still ' + (reExec?.failed_count || 0) + ' failures' : '✅ All fixed!'))
  } else {
    // 没有可自动修复的 → 退出循环，留到 Report 阶段汇总
    log('  ⚠️ ' + (bugResult?.not_auto_fixable || 0) + ' non-fixable failures — 需要人工处理')
    break
  }
}

if (fixRounds >= MAX_FIX_ROUNDS && execFailed) {
  log('⚠️ 已达最大修复轮数 (' + MAX_FIX_ROUNDS + ')，仍有失败。请人工介入。')
}
if (!execFailed) {
  log('✅ 所有测试通过！' + (fixRounds > 0 ? ' (' + fixRounds + ' 轮修复)' : ''))
}

// 写入进度状态（更新）
const statusPayload2 = {
  module: MODULE,
  status: execFailed ? 'completed_with_failures' : 'completed',
  current_phase: 'Report',
  completed_phases: ['Preflight', 'Orchestrate', 'Execute & Debug'].concat(fixRounds > 0 ? ['Bug Analysis'] : []),
  pages_processed: pages,
  execution: { failed: execFailed, failed_count: failedCount, fix_rounds: fixRounds, fix_log: fixLog },
}

await agent(
  'Write SOP status to ' + STATUS_FILE + ':\n```json\n' + JSON.stringify(statusPayload2, null, 2) + '\n```\n用 Write 工具写入。完成后返回 {"written": true}',
  {
    label: 'write-status-2',
    model: 'haiku',
    schema: { type: 'object', properties: { written: { type: 'boolean' } }, required: ['written'] },
  }
)

// ═══════════════════════════════════════════════════════════
// Phase 5: Data Sanitization — 离线扫描清理残留数据
// ═══════════════════════════════════════════════════════════
phase('Data Sanitization')

log('🧹 扫描残留数据...')
const sanitizeResult = await agent(
  `Run: cd ZJSN_Test-master526 && python tools/cleanup/scan_and_clean.py --force

读取命令输出，汇报 JSON:
{
  "residual_count": 0,
  "cleaned_count": 0,
  "threshold_exceeded": false,
  "output_summary": ""
}`,
  {
    label: 'sanitize:' + MODULE,
    model: 'haiku',
    phase: 'Data Sanitization',
    schema: {
      type: 'object',
      properties: {
        residual_count: { type: 'number' },
        cleaned_count: { type: 'number' },
        threshold_exceeded: { type: 'boolean' },
        output_summary: { type: 'string' },
      },
      required: ['residual_count', 'cleaned_count'],
    },
  }
)

const residualCount = sanitizeResult?.residual_count || 0
const cleanedCount = sanitizeResult?.cleaned_count || 0
const thresholdExceeded = sanitizeResult?.threshold_exceeded || false

if (residualCount === 0) {
  log('  ✅ 无残留数据')
} else {
  log('  🧹 清理 ' + cleanedCount + ' / ' + residualCount + ' 条残留数据')
}
if (thresholdExceeded) {
  log('  ⚠️ 残留数据超过阈值 (50)，请检查')
}

// 更新进度状态
const statusPayload3 = {
  module: MODULE,
  status: execFailed ? 'completed_with_failures' : 'completed',
  current_phase: 'Report',
  completed_phases: ['Preflight', 'Orchestrate', 'Execute & Debug'].concat(fixRounds > 0 ? ['Bug Analysis'] : []).concat(['Data Sanitization']),
  pages_processed: pages,
  execution: { failed: execFailed, failed_count: failedCount, fix_rounds: fixRounds, fix_log: fixLog },
  sanitization: { residual_count: residualCount, cleaned_count: cleanedCount, threshold_exceeded: thresholdExceeded },
}

await agent(
  'Write SOP status to ' + STATUS_FILE + ':\n```json\n' + JSON.stringify(statusPayload3, null, 2) + '\n```\n用 Write 工具写入。完成后返回 {"written": true}',
  {
    label: 'write-status-3',
    model: 'haiku',
    schema: { type: 'object', properties: { written: { type: 'boolean' } }, required: ['written'] },
  }
)

// ═══════════════════════════════════════════════════════════
// Phase 6: Report — 测试报告生成
// ═══════════════════════════════════════════════════════════
phase('Report')

log('Generating report...')
const reportResult = await agent(
  `调用 Skill 工具: Skill skill="report-agent" args="module=${MODULE} mode=summary"

完成后汇报 JSON:
{
  "summary_done": true,
  "excel_exported": true,
  "report_paths": []
}`,
  {
    label: `report:${MODULE}`,
    phase: 'Report',
    schema: {
      type: 'object',
      properties: {
        summary_done: { type: 'boolean' },
        excel_exported: { type: 'boolean' },
        report_paths: { type: 'array', items: { type: 'string' } },
      },
      required: ['summary_done', 'excel_exported'],
    },
  }
)
log(`Report: ${reportResult.report_paths?.join(', ') || 'done'}`)

// ═══════════════════════════════════════════════════════════
// Phase 6: Knowledge — 知识沉淀 + Event Bus 处理
// ═══════════════════════════════════════════════════════════
phase('Knowledge')

log('Processing events + knowledge sync...')

// 处理 Event Bus 积压事件
const eventResult = await agent(
  `Run: python -m aitest.event_bus process

读取命令输出，汇报处理的 events 数量。
完成后汇报 JSON:
{
  "events_processed": 0,
  "events_skipped": 0
}`,
  {
    label: 'event-process',
    model: 'haiku',
    phase: 'Knowledge',
    schema: {
      type: 'object',
      properties: {
        events_processed: { type: 'number' },
        events_skipped: { type: 'number' },
      },
      required: ['events_processed'],
    },
  }
)
log(`Events: ${eventResult.events_processed || 0} processed`)

// Knowledge Agent
const knowledgeResult = await agent(
  `调用 Skill 工具: Skill skill="knowledge-agent" args="source=test-cycle module=${MODULE}"

完成后汇报 JSON:
{
  "new_known_issues": 0,
  "total_known_issues": 0,
  "knowledge_synced": true
}`,
  {
    label: `knowledge:${MODULE}`,
    phase: 'Knowledge',
    schema: {
      type: 'object',
      properties: {
        new_known_issues: { type: 'number' },
        total_known_issues: { type: 'number' },
        knowledge_synced: { type: 'boolean' },
      },
      required: ['knowledge_synced'],
    },
  }
)
log(`Knowledge: ${knowledgeResult.total_known_issues || 0} issues (${knowledgeResult.new_known_issues || 0} new)`)

// ═══════════════════════════════════════════════════════════
// 完成
// ═══════════════════════════════════════════════════════════
log('')
log('════════════════════════════════════════════')
log(`  Module "${MODULE}" SOP complete`)
log(`  Phases: Preflight → Orchestrate → Execute & Debug${fixRounds > 0 ? ' → Bug Analysis(' + fixRounds + ' rounds)' : ''} → Data Sanitization → Report → Knowledge`)
log(`  Tests: ${execFailed ? '❌ ' + failedCount + ' failures (auto-fix exhausted)' : '✅ All passed'}`)
log(`  Sanitization: ${residualCount > 0 ? '🧹 cleaned ' + cleanedCount + '/' + residualCount : '✅ clean'}`)
log(`  Status: ${STATUS_FILE}`)
log('════════════════════════════════════════════')

return {
  module: MODULE,
  mode: MODE,
  pages,
  orchestrate_steps: { completed, failed },
  execution: {
    failed: execFailed,
    failed_count: failedCount,
    fix_rounds: fixRounds,
    fix_log: fixLog,
  },
  sanitization: {
    residual_count: residualCount,
    cleaned_count: cleanedCount,
    threshold_exceeded: thresholdExceeded,
  },
  status_file: STATUS_FILE,
  next_step: execFailed
    ? '仍有失败用例需要人工处理。检查 BUG_ANALYSIS.md 和 allure-results 后手动修复。'
    : 'SOP complete. Use /knowledge-agent for continuous improvement.',
}
