/** Execution view — SOP control + Agent graph + Terminal + Run Inspector. */
import { useState, useEffect, useMemo, useCallback } from 'react'
import { useParams, useSearchParams, useNavigate } from 'react-router-dom'
import { useKanbanStore } from '../stores/kanban'
import { useProjectStore } from '../stores/project'
import { api } from '@/api/client'
import LiveAgentGraph from '../components/LiveAgentGraph'
import TerminalPanel from '../components/TerminalPanel'
import { Play, Pause, Square, Activity, Eye, RefreshCw, ExternalLink } from 'lucide-react'

interface DebugInfo {
  total_events: number; llm_calls: number; tool_calls: number; state_changes: number
  timeline: Array<{ event_id: string; event_type: string; timestamp: string }>
  llm_calls_detail: Array<{ event_type: string; timestamp: string }>
  tool_calls_detail: Array<{ event_type: string; timestamp: string }>
}
interface RunDetail {
  run_id: string; request_id: string; status: string; agent: string
  module: string; pages: string[]; created_at: string; completed_at: string
  total_tokens: number; total_cost: number; error_message: string
  debug: DebugInfo
}

const SOP_PHASES = [
  { id: 'project-agent', label: '项目', phase: 0 },
  { id: 'requirement-agent', label: '需求', phase: 1 },
  { id: 'test-design-agent', label: '设计', phase: 2 },
  { id: 'automation-agent', label: '自动化', phase: 4 },
  { id: 'execution-agent', label: '执行', phase: 6 },
  { id: 'bug-analysis-agent', label: '分析', phase: 7 },
  { id: 'report-agent', label: '报告', phase: 8 },
  { id: 'knowledge-agent', label: '知识', phase: 9 },
]

export default function ExecutionView() {
  const { id } = useParams<{ id: string }>()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const modules = useKanbanStore(s => s.modules)
  const modulesLoading = useKanbanStore(s => s.loading)
  const fetchModules = useKanbanStore(s => s.fetchModules)
  const setActive = useProjectStore(s => s.setActive)

  const [selectedModule, setSelectedModule] = useState(searchParams.get('module') || '')
  const [sopMode, setSopMode] = useState('full')
  const [running, setRunning] = useState(false)

  // ── Run Inspector state ──
  const [runs, setRuns] = useState<Array<{ run_id: string; status: string; agent: string; module: string }>>([])
  const [selectedRun, setSelectedRun] = useState<RunDetail | null>(null)
  const [inspectorOpen, setInspectorOpen] = useState(false)

  const fetchRuns = useCallback(async () => {
    try {
      const data = await api.get<{ runs: Array<{ run_id: string; status: string; agent: string; module: string }> }>('/api/runs?limit=10')
      setRuns(data.runs || [])
    } catch {}
  }, [])

  const inspectRun = useCallback(async (runId: string) => {
    try {
      const data = await api.get<RunDetail>(`/api/runs/${runId}/debug`)
      setSelectedRun(data)
      setInspectorOpen(true)
    } catch {}
  }, [])

  useEffect(() => { fetchRuns() }, [fetchRuns])

  const moduleList = useMemo(() =>
    Object.keys(modules).map(id => ({ id, name: id })),
    [modules]
  )

  const graphPhases = useMemo(() => {
    const mod = modules[selectedModule]
    // TODO: ModuleInfo uses phase_status (string→bool map), not completed_phases.
    // SOP_PHASES uses numeric indices. Need backend data model alignment.
    // For now: derive done from phase_status entries.
    const phaseStatus: Record<string, boolean> = mod?.phase_status || {}
    const donePhaseNames = Object.entries(phaseStatus)
      .filter(([, done]) => done)
      .map(([name]) => name)
    const currentPhaseName: string = mod?.current_phase || ''
    return SOP_PHASES.map(p => ({
      ...p,
      status: donePhaseNames.includes(p.label) ? 'completed'
            : p.label === currentPhaseName ? 'running'
            : 'pending',
    }))
  }, [modules, selectedModule])

  useEffect(() => {
    if (id) setActive(id)
    fetchModules()
  }, [id, setActive, fetchModules])

  return (
    <div className="execution">
      <div className="exec-header">
        <div className="header-left">
          <Play size={20} />
          <h1>执行中心</h1>
        </div>
        <div className="header-controls">
          <select value={selectedModule} onChange={e => setSelectedModule(e.target.value)} className="sel" disabled={modulesLoading}>
            <option value="">{modulesLoading ? '加载中...' : moduleList.length === 0 ? '无可用模块' : '选择模块'}</option>
            {moduleList.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}
          </select>
          <select value={sopMode} onChange={e => setSopMode(e.target.value)} className="sel sel-sm">
            <option value="full">完整 SOP</option>
            <option value="from-automation">从自动化开始</option>
            <option value="resume">恢复上次</option>
          </select>
          {!running ? (
            <button className="btn-run" onClick={() => setRunning(true)} disabled={!selectedModule}>
              <Play size={14} /> 运行
            </button>
          ) : (
            <>
              <button className="btn-pause" onClick={() => setRunning(false)}><Pause size={14} /> 暂停</button>
              <button className="btn-cancel" onClick={() => setRunning(false)}><Square size={14} /> 取消</button>
            </>
          )}
        </div>
      </div>

      {selectedModule && (
        <div className="progress-bar-wrap">
          <div className="phase-dots">
            {SOP_PHASES.map(p => {
              const gs = graphPhases.find(g => g.id === p.id)?.status || 'pending'
              return (
                <span key={p.phase} className={`phase-dot ${gs}`} title={p.label}>{p.phase}</span>
              )
            })}
          </div>
        </div>
      )}

      {/* ── Run Inspector (v2.6 DX) ── */}
      <div className="run-inspector-section">
        <div className="ri-header">
          <h3><Eye size={14} /> Run Inspector</h3>
          <button className="ri-refresh" onClick={fetchRuns}><RefreshCw size={12} /></button>
        </div>
        <div className="ri-body">
          <div className="ri-list">
            {runs.length === 0 ? (
              <div className="ri-empty">No runs yet</div>
            ) : (
              runs.map(r => (
                <div key={r.run_id} className={`ri-row ${selectedRun?.run_id === r.run_id ? 'active' : ''}`}
                  onClick={() => inspectRun(r.run_id)}>
                  <span className={`ri-status ${r.status}`}>{r.status}</span>
                  <span className="ri-agent">{r.agent}</span>
                  <span className="ri-module">{r.module}</span>
                </div>
              ))
            )}
          </div>
          {inspectorOpen && selectedRun && (
            <div className="ri-detail">
              <div className="ri-detail-header">
                <span>Run: {selectedRun.run_id.slice(0, 20)}...</span>
                <div className="flex items-center gap-2">
                  <button className="ri-full" title="Open full inspector"
                    onClick={() => navigate(`/projects/${id}/runs/${selectedRun.run_id}`)}>
                    <ExternalLink size={14} />
                  </button>
                  <button className="ri-close" onClick={() => setInspectorOpen(false)}>×</button>
                </div>
              </div>
              <div className="ri-detail-grid">
                <div><span>Status:</span> {selectedRun.status}</div>
                <div><span>Agent:</span> {selectedRun.agent}</div>
                <div><span>Module:</span> {selectedRun.module}</div>
                <div><span>Tokens:</span> {selectedRun.total_tokens?.toLocaleString()}</div>
                <div><span>Cost:</span> ${selectedRun.total_cost?.toFixed(4)}</div>
                <div><span>Events:</span> {selectedRun.debug?.total_events}</div>
                <div><span>LLM Calls:</span> {selectedRun.debug?.llm_calls}</div>
                <div><span>Tool Calls:</span> {selectedRun.debug?.tool_calls}</div>
              </div>
              {selectedRun.debug?.llm_calls > 0 && (
                <details className="ri-detail-events">
                  <summary>LLM Calls ({selectedRun.debug.llm_calls})</summary>
                  {selectedRun.debug.llm_calls_detail.slice(0, 20).map((e, i) => (
                    <div key={i} className="ri-event">
                      <span className="ri-ts">{e.timestamp?.slice(11, 19) || '—'}</span>
                      <span>{e.event_type}</span>
                    </div>
                  ))}
                </details>
              )}
              {selectedRun.debug?.tool_calls > 0 && (
                <details className="ri-detail-events">
                  <summary>Tool Calls ({selectedRun.debug.tool_calls})</summary>
                  {selectedRun.debug.tool_calls_detail.slice(0, 20).map((e, i) => (
                    <div key={i} className="ri-event">
                      <span className="ri-ts">{e.timestamp?.slice(11, 19) || '—'}</span>
                      <span>{e.event_type}</span>
                    </div>
                  ))}
                </details>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="exec-body">
        <div className="graph-section">
          <div className="section-label"><Activity size={12} /> Agent 执行图</div>
          <LiveAgentGraph phases={graphPhases} currentPhase={0} />
        </div>
        <div className="terminal-section">
          <div className="section-label">Agent 终端</div>
          <TerminalPanel autoConnect />
        </div>
      </div>

      <style>{`
        .execution { padding: 20px 28px; max-width: 1400px; }
        .exec-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
        .header-left { display: flex; align-items: center; gap: 10px; }
        .header-left h1 { font-size: 19px; font-weight: 700; margin: 0; }
        .header-controls { display: flex; gap: 8px; align-items: center; }
        .sel { font-size: 13px; padding: 6px 10px; border: 1px solid var(--border); border-radius: 6px; background: var(--bg-primary); }
        .sel-sm { width: 130px; }
        .btn-run, .btn-pause, .btn-cancel { display: flex; align-items: center; gap: 4px; font-size: 13px; padding: 6px 14px; border: none; border-radius: 6px; cursor: pointer; color: white; font-weight: 500; }
        .btn-run { background: hsl(var(--info)); }
        .btn-run:disabled { opacity: .5; cursor: not-allowed; }
        .btn-pause { background: hsl(var(--warning)); color: hsl(var(--warning-foreground)); }
        .btn-cancel { background: hsl(var(--destructive)); }
        .progress-bar-wrap { margin-bottom: 16px; }
        .phase-dots { display: flex; gap: 4px; align-items: center; }
        .phase-dot { width: 26px; height: 26px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 600; border: 2px solid hsl(var(--border)); color: hsl(var(--muted-foreground)); background: hsl(var(--card)); }
        .phase-dot.completed { border-color: hsl(var(--success)); background: hsl(var(--success-light)); color: hsl(var(--success)); }
        .phase-dot.running { border-color: hsl(var(--info)); background: hsl(var(--info-light)); color: hsl(var(--info)); animation: pulse 1.5s infinite; }
        .phase-dot.failed { border-color: hsl(var(--destructive)); background: hsl(var(--destructive-light)); color: hsl(var(--destructive)); }
        @keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:.5; } }
        .exec-body { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; min-height: 440px; }
        .graph-section, .terminal-section { display: flex; flex-direction: column; gap: 8px; }
        .section-label { display: flex; align-items: center; gap: 6px; font-size: 12px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: .5px; }

        /* ── Run Inspector ── */
        .run-inspector-section { margin-top: 24px; border-top: 1px solid hsl(var(--border)); padding-top: 16px; }
        .ri-header { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; }
        .ri-header h3 { margin: 0; font-size: 15px; font-weight: 600; display: flex; align-items: center; gap: 6px; }
        .ri-refresh { background: none; border: 1px solid hsl(var(--border)); border-radius: 4px; padding: 3px 6px; cursor: pointer; }
        .ri-body { display: grid; grid-template-columns: 280px 1fr; gap: 12px; }
        .ri-list { max-height: 200px; overflow-y: auto; }
        .ri-empty { font-size: 13px; color: hsl(var(--muted-foreground)); padding: 12px; text-align: center; }
        .ri-row { display: flex; align-items: center; gap: 8px; padding: 6px 8px; cursor: pointer; border-radius: 4px; font-size: 12px; }
        .ri-row:hover { background: hsl(var(--accent)); }
        .ri-row.active { background: hsl(var(--accent)); }
        .ri-status { font-weight: 600; width: 72px; text-transform: uppercase; font-size: 10px; padding: 1px 4px; border-radius: 3px; text-align: center; }
        .ri-status.completed { background: hsl(var(--success-light)); color: hsl(var(--success)); }
        .ri-status.failed { background: hsl(var(--destructive-light)); color: hsl(var(--destructive)); }
        .ri-status.running { background: hsl(var(--info-light)); color: hsl(var(--info)); }
        .ri-status.timed_out { background: hsl(var(--warning-light)); color: hsl(var(--warning)); }
        .ri-agent { color: hsl(var(--muted-foreground)); width: 80px; overflow: hidden; text-overflow: ellipsis; }
        .ri-module { color: hsl(var(--muted-foreground)); }
        .ri-detail { background: hsl(var(--card)); border: 1px solid hsl(var(--border)); border-radius: 6px; padding: 12px; font-size: 12px; max-height: 300px; overflow-y: auto; }
        .ri-detail-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; font-weight: 600; }
        .ri-close { background: none; border: none; font-size: 18px; cursor: pointer; color: hsl(var(--muted-foreground)); }
        .ri-detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 4px 16px; }
        .ri-detail-grid div span { color: hsl(var(--muted-foreground)); }
        .ri-detail-events { margin-top: 8px; }
        .ri-detail-events summary { cursor: pointer; font-weight: 500; margin-bottom: 4px; }
        .ri-event { display: flex; gap: 8px; padding: 2px 0; font-size: 11px; font-family: monospace; }
        .ri-ts { color: hsl(var(--muted-foreground)); width: 60px; }
      `}</style>
    </div>
  )
}
