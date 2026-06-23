export const meta = {
  name: 'full-sop',
  description: '端到端 SOP 编排器 — 委托 aitest graph run CLI (LangGraph) 执行。Phase 0→9 串联 8 Agent，含 checkpoint + state machine + gate + code review。',
  phases: [
    { title: 'Preflight', detail: '参数验证 + gate 检查' },
    { title: 'Execute', detail: 'aitest graph run --non-interactive (LangGraph 9-Phase 状态机)' },
  ],
}

// ═══════════════════════════════════════════════════════════
// 参数解析
// ═══════════════════════════════════════════════════════════
const MODULE = args?.module
const MODE = args?.mode || 'full'
const USER_PAGES = args?.pages || ''
let PROJECT = args?.project || process.env.AITEST_PROJECT || ''
if (!PROJECT) {
  log('WARNING: No project specified. Set AITEST_PROJECT env var or pass project=<id>. Using web-automation as fallback.')
  PROJECT = 'web-automation'
}

if (!MODULE) {
  log('ERROR: 缺少必填参数: module')
  log('用法: /full-sop module=<模块名> [mode=full|resume|status|from-requirement|from-test-design|from-automation] [pages=<页面1,页面2>]')
  throw new Error('Missing required arg: module')
}

// ═══════════════════════════════════════════════════════════
// Status 模式: 快速查看进度（不调用 Python）
// ═══════════════════════════════════════════════════════════
if (MODE === 'status') {
  phase('Status')
  const statusFile = `governance/artifacts/sop-status/SOP_STATUS_${MODULE}.json`

  const statusResult = await agent(
    `Read ${statusFile}。如果不存在，依次检查:
     1. governance/artifacts/sop-status/${PROJECT}/SOP_STATUS_${MODULE}.json (per-project dir)
     2. governance/artifacts/sop-status/SOP_STATUS_${MODULE}.json (legacy flat)
     3. governance/context/projects/${PROJECT}/modules/${MODULE}/ 下的文件。

    输出模块 ${MODULE} 的 SOP 进度摘要:
    {
      "module": "${MODULE}",
      "status": "completed|in_progress|not_started",
      "completed_phases": [],
      "missing_phases": [],
      "pages": 0,
      "next_step": "建议的下一步操作"
    }`,
    {
      label: 'status:' + MODULE,
      model: 'haiku',
      schema: {
        type: 'object',
        properties: {
          module: { type: 'string' },
          status: { type: 'string' },
          completed_phases: { type: 'array', items: { type: 'string' } },
          missing_phases: { type: 'array', items: { type: 'string' } },
          pages: { type: 'number' },
          next_step: { type: 'string' },
        },
        required: ['module', 'status'],
      },
    }
  )

  log('')
  log('Module: ' + MODULE)
  log('Status: ' + (statusResult?.status || 'unknown'))
  log('Completed: ' + (statusResult?.completed_phases || []).join(', ') || 'none')
  if (statusResult?.missing_phases?.length) {
    log('Missing:  ' + statusResult.missing_phases.join(', '))
  }
  log('Next:    ' + (statusResult?.next_step || '/full-sop module=' + MODULE))

  return {
    module: MODULE,
    mode: 'status',
    ...statusResult,
  }
}

// ═══════════════════════════════════════════════════════════
// Run 模式: 委托 Python LangGraph CLI
// ═══════════════════════════════════════════════════════════
phase('Execute')

// 构建 CLI 命令
let cmd = `aitest graph run --module=${MODULE} --mode=${MODE} --non-interactive`
if (USER_PAGES) {
  cmd += ` --pages=${USER_PAGES}`
}

log('Delegating to LangGraph engine...')
log('  ' + cmd)
log('')

// 执行 Python CLI（通过 Bash tool）
const execResult = await agent(
  `Run the following command and capture its output:

  cd d:\\Desktop\\Alice && ${cmd}

  The command will output a JSON result at the end (non-interactive mode).
  Parse the JSON and report back the structured result.

  If the command fails, report the error message.`,
  {
    label: 'langgraph:' + MODULE,
    schema: {
      type: 'object',
      properties: {
        ok: { type: 'boolean' },
        status: { type: 'string' },
        module: { type: 'string' },
        run_id: { type: 'string' },
        completed_phases: { type: 'array', items: { type: 'string' } },
        failed_phases: { type: 'array', items: { type: 'string' } },
        pages_processed: { type: 'array', items: { type: 'string' } },
        fatal_error: { type: 'string' },
        hitl_decisions: { type: 'array', items: { type: 'object' } },
        error: { type: 'string' },
      },
      required: ['ok'],
    },
  }
)

// ═══════════════════════════════════════════════════════════
// 结果展示
// ═══════════════════════════════════════════════════════════
const ok = execResult?.ok ?? false
const sopStatus = execResult?.status || 'unknown'
const completed = execResult?.completed_phases || []
const failed = execResult?.failed_phases || []

log('')
log('========================================================')
log(`  Module "${MODULE}" SOP ${ok ? 'complete' : 'completed with issues'}`)
log(`  Status:  ${sopStatus}`)
log(`  Phases:  ${completed.length} completed`)
if (completed.length) log(`           ${completed.join(' → ')}`)
if (failed.length) log(`  Failed:  ${failed.join(', ')}`)
if (execResult?.fatal_error) log(`  ERROR:   ${execResult.fatal_error}`)
log(`  Engine:  LangGraph (checkpoint: ${execResult?.run_id || 'N/A'})`)
log(`  Status:  governance/artifacts/sop-status/SOP_STATUS_${MODULE}.json`)
log('========================================================')

return {
  module: MODULE,
  mode: MODE,
  ok,
  status: sopStatus,
  run_id: execResult?.run_id,
  completed_phases: completed,
  failed_phases: failed,
  pages_processed: execResult?.pages_processed || [],
  fatal_error: execResult?.fatal_error,
  next_step: ok && sopStatus === 'completed'
    ? `Module "${MODULE}" complete. /report-agent module=${MODULE} for summary.`
    : ok
      ? `Resume with: /full-sop module=${MODULE} mode=resume`
      : `Check fatal_error above. Retry with: /full-sop module=${MODULE}`,
}
