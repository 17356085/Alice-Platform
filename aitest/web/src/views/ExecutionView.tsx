/** Execution view — SOP control + Agent graph + Terminal. React port. */
import { useState, useEffect, useMemo } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'
import { useKanbanStore } from '../stores/kanban'
import { useProjectStore } from '../stores/project'
import LiveAgentGraph from '../components/LiveAgentGraph'
import TerminalPanel from '../components/TerminalPanel'
import { Play, Pause, Square, Activity } from 'lucide-react'

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
  const modules = useKanbanStore(s => s.modules)
  const fetchModules = useKanbanStore(s => s.fetchModules)
  const setActive = useProjectStore(s => s.setActive)

  const [selectedModule, setSelectedModule] = useState(searchParams.get('module') || '')
  const [sopMode, setSopMode] = useState('full')
  const [running, setRunning] = useState(false)

  const moduleList = useMemo(() =>
    Object.keys(modules).map(id => ({ id, name: (modules[id] as any)?.name || id })),
    [modules]
  )

  const graphPhases = useMemo(() => {
    const mod = modules[selectedModule] as any
    const donePhases: number[] = mod?.completed_phases || []
    const currentPhase: number = mod?.current_phase ?? -1
    return SOP_PHASES.map(p => ({
      ...p,
      status: donePhases.includes(p.phase) ? 'completed'
            : p.phase === currentPhase ? 'running'
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
          <select value={selectedModule} onChange={e => setSelectedModule(e.target.value)} className="sel">
            <option value="">选择模块</option>
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
        .btn-run { background: #3b82f6; }
        .btn-run:disabled { opacity: .5; cursor: not-allowed; }
        .btn-pause { background: #eab308; color: #1e1e1e; }
        .btn-cancel { background: #ef4444; }
        .progress-bar-wrap { margin-bottom: 16px; }
        .phase-dots { display: flex; gap: 4px; align-items: center; }
        .phase-dot { width: 26px; height: 26px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 600; border: 2px solid #d1d5db; color: #9ca3af; background: #f9fafb; }
        .phase-dot.completed { border-color: #22c55e; background: #dcfce7; color: #166534; }
        .phase-dot.running { border-color: #3b82f6; background: #dbeafe; color: #1e40af; animation: pulse 1.5s infinite; }
        .phase-dot.failed { border-color: #ef4444; background: #fef2f2; color: #991b1b; }
        @keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:.5; } }
        .exec-body { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; min-height: 440px; }
        .graph-section, .terminal-section { display: flex; flex-direction: column; gap: 8px; }
        .section-label { display: flex; align-items: center; gap: 6px; font-size: 12px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: .5px; }
      `}</style>
    </div>
  )
}
