/** Step: Results — shows discovered pages, registers project. React port. */
import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { useOnboardingStore } from '@/stores/onboarding'
import { useProjectStore } from '@/stores/project'
import { CheckCircle2, FolderOpen, FileText, Layers, ArrowRight } from 'lucide-react'

export default function StepResults() {
  const navigate = useNavigate()
  const pages = useOnboardingStore(s => s.pages)
  const projectId = useOnboardingStore(s => s.projectId)
  const projectPath = useOnboardingStore(s => s.projectPath)
  const baseUrl = useOnboardingStore(s => s.baseUrl)
  const addProject = useProjectStore(s => s.addProject)
  const setActive = useProjectStore(s => s.setActive)

  const pagesByGroup = useMemo(() => {
    const groups: Record<string, any[]> = {}
    for (const p of pages) {
      const key = p.menu_path?.[0] || 'Other'
      if (!groups[key]) groups[key] = []
      groups[key].push(p)
    }
    return groups
  }, [pages])

  const groupCount = Object.keys(pagesByGroup).length

  function openProject() {
    if (projectId) {
      addProject({
        id: projectId, name: projectId,
        path: projectPath || baseUrl,
        modules: Object.keys(pagesByGroup),
        status: 'discovered',
      })
      setActive(projectId)
    }
    navigate({ pathname: '/kanban', search: `?project=${projectId}` })
  }

  return (
    <div className="step-results">
      <div className="success-icon"><CheckCircle2 size={56} /></div>
      <h3>Project Ready!</h3>
      <p className="summary"><strong>{projectId}</strong> has been onboarded successfully.</p>
      <div className="stats-grid">
        <div className="stat"><Layers size={20} /><div><span className="stat-value">{groupCount}</span><span className="stat-label">Menu Groups</span></div></div>
        <div className="stat"><FileText size={20} /><div><span className="stat-value">{pages.length}</span><span className="stat-label">Pages Discovered</span></div></div>
        <div className="stat"><FolderOpen size={20} /><div><span className="stat-value">{groupCount}</span><span className="stat-label">Modules Created</span></div></div>
      </div>
      <div className="actions">
        <button className="btn-open" onClick={openProject}><ArrowRight size={16} /> Open Project Kanban</button>
      </div>
      <style>{`
        .step-results { text-align: center; padding: 16px 0; }
        .success-icon { color: var(--success); margin-bottom: 16px; }
        h3 { font-size: 1.25rem; font-weight: 700; color: var(--foreground); margin: 0 0 6px; }
        .summary { color: var(--muted-foreground); font-size: 0.9rem; margin: 0 0 24px; }
        .stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 24px; }
        .stat { background: var(--card); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 16px; display: flex; align-items: center; gap: 10px; color: var(--primary); }
        .stat-value { display: block; font-size: 1.4rem; font-weight: 700; color: var(--foreground); }
        .stat-label { display: block; font-size: 0.75rem; color: var(--muted-foreground); }
        .actions { margin-top: 8px; }
        .btn-open { display: inline-flex; align-items: center; gap: 8px; padding: 12px 32px; background: var(--primary); color: var(--primary-foreground); border: none; border-radius: var(--radius-md); font-size: 0.95rem; font-weight: 600; cursor: pointer; }
        .btn-open:hover { filter: brightness(1.1); }
      `}</style>
    </div>
  )
}
