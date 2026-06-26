/** Onboarding Wizard — multi-step project discovery. React port.
 *  Vue computed stepIndex → React useMemo.
 *  Vue v-if → React JSX conditional rendering.
 */
import { useState, useMemo, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useOnboardingStore, selectIsComplete, selectIsMenuReady, selectIsFailed } from '@/stores/onboarding'
import { useOnboardingWS } from '@/hooks/useOnboardingWS'
import StepChooseSource from '@/components/onboarding/StepChooseSource'
import StepUrlInput from '@/components/onboarding/StepUrlInput'
import StepScanning from '@/components/onboarding/StepScanning'
import StepConfirmMenu from '@/components/onboarding/StepConfirmMenu'
import StepResults from '@/components/onboarding/StepResults'
import { Globe, Wifi, ListTree, FileSearch, CheckCircle2, AlertTriangle, ArrowRight, FolderOpen } from 'lucide-react'

const STEPS = [
  { key: 'source', label: 'Source', icon: FolderOpen },
  { key: 'discovery', label: 'Discovery', icon: Wifi },
  { key: 'confirm', label: 'Review', icon: ListTree },
  { key: 'results', label: 'Results', icon: CheckCircle2 },
]

export default function OnboardingWizardView() {
  const navigate = useNavigate()
  const store = useOnboardingStore
  const isRunning = useOnboardingStore(s => s.isRunning)
  const isComplete = useOnboardingStore(selectIsComplete)
  const isMenuReady = useOnboardingStore(selectIsMenuReady)
  const isFailed = useOnboardingStore(selectIsFailed)
  const progress = useOnboardingStore(s => s.progress)
  const errors = useOnboardingStore(s => s.errors)
  const sourceType = useOnboardingStore(s => s.sourceType)
  const projectId = useOnboardingStore(s => s.projectId)
  const cancel = useOnboardingStore(s => s.cancel)
  const reset = useOnboardingStore(s => s.reset)
  const { disconnect, wsError } = useOnboardingWS()

  const [sourceChosen, setSourceChosen] = useState(false)

  const currentStepIndex = useMemo(() => {
    if (isComplete) return 3
    if (isMenuReady) return 2
    if (isRunning || sourceChosen) return 1
    return 0
  }, [isComplete, isMenuReady, isRunning, sourceChosen])

  function onSourceChoose(type: 'url' | 'local', value: string) {
    store.setState({ sourceType: type })
    if (type === 'local') {
      const s = useOnboardingStore.getState()
      s.projectPath = value
      s.baseUrl = value
      const parts = value.replace(/\\/g, '/').replace(/\/$/, '').split('/')
      const folderName = parts[parts.length - 1] || 'local-project'
      store.setState({ projectPath: value, baseUrl: value, projectId: folderName })
      s.start(value, folderName, '', '')
    } else {
      store.setState({ baseUrl: value })
    }
    setSourceChosen(true)
  }

  function openProject() {
    navigate({ pathname: '/kanban', search: `?project=${projectId}` })
  }

  useEffect(() => {
    return () => { disconnect() }
  }, [disconnect])

  return (
    <div className="onboarding-wizard">
      <header className="wizard-header">
        <h2>New Project Onboarding</h2>
        <p className="subtitle">Enter a URL — TLO auto-discovers the application structure</p>
      </header>

      <nav className="step-indicators">
        {STEPS.map((step, i) => (
          <div key={step.key} className={`step-dot${i === currentStepIndex ? ' active' : ''}${i < currentStepIndex ? ' done' : ''}${isFailed && i === currentStepIndex ? ' error' : ''}`}>
            <step.icon size={18} /><span className="step-label">{step.label}</span>
          </div>
        ))}
      </nav>

      {(isRunning || isComplete) && (
        <div className="progress-bar-wrapper">
          <div className="progress-bar"><div className={`progress-fill${isComplete ? ' complete' : ''}${isFailed ? ' error' : ''}`} style={{ width: `${progress * 100}%` }} /></div>
          <span className="progress-text">{Math.round(progress * 100)}%</span>
        </div>
      )}

      {wsError && <div className="error-banner"><AlertTriangle size={16} /><span>{wsError}</span></div>}

      <main className="wizard-body">
        {currentStepIndex === 0 && !sourceChosen && <StepChooseSource onChoose={onSourceChoose} />}
        {currentStepIndex === 1 && !isRunning && sourceType === 'url' && <StepUrlInput />}
        {currentStepIndex === 1 && isRunning && <StepScanning />}
        {currentStepIndex === 2 && <StepConfirmMenu />}
        {currentStepIndex === 3 && <StepResults />}
        {isFailed && (
          <div className="failed-state">
            <AlertTriangle size={48} className="error-icon" />
            <h3>Onboarding failed</h3>
            {errors.length > 0 && <ul className="error-list">{errors.map((err, i) => <li key={i}>{err}</li>)}</ul>}
            <div className="btn-row"><button className="btn btn-secondary" onClick={() => reset()}>Try Again</button></div>
          </div>
        )}
      </main>

      <footer className="wizard-footer">
        {(isRunning || isMenuReady) && <button className="btn btn-outline" onClick={() => cancel()}>Cancel</button>}
        {isComplete && <button className="btn btn-primary" onClick={openProject}>Open Project <ArrowRight size={16} /></button>}
      </footer>

      <style>{`
        .onboarding-wizard { max-width: 720px; margin: 0 auto; padding: 32px 24px; animation: fade-in 0.3s ease-out; }
        .wizard-header { margin-bottom: 32px; text-align: center; }
        .wizard-header h2 { font-size: 1.5rem; font-weight: 700; color: var(--foreground); margin: 0 0 8px; }
        .subtitle { color: var(--muted-foreground); font-size: 0.9rem; margin: 0; }
        .step-indicators { display: flex; justify-content: center; gap: 40px; margin-bottom: 24px; }
        .step-dot { display: flex; flex-direction: column; align-items: center; gap: 6px; color: var(--muted-foreground); transition: color 0.2s; }
        .step-dot.active { color: var(--primary); }
        .step-dot.done { color: var(--success); }
        .step-dot.error { color: var(--destructive); }
        .step-label { font-size: 0.75rem; font-weight: 500; }
        .progress-bar-wrapper { display: flex; align-items: center; gap: 12px; margin-bottom: 24px; }
        .progress-bar { flex: 1; height: 6px; background: var(--secondary); border-radius: var(--radius-full); overflow: hidden; }
        .progress-fill { height: 100%; background: var(--primary); border-radius: var(--radius-full); transition: width 0.5s ease; }
        .progress-fill.complete { background: var(--success); }
        .progress-fill.error { background: var(--destructive); }
        .progress-text { font-size: 0.8rem; font-weight: 600; color: var(--muted-foreground); min-width: 3em; text-align: right; }
        .wizard-body { min-height: 300px; }
        .wizard-footer { display: flex; justify-content: flex-end; gap: 12px; margin-top: 24px; padding-top: 16px; border-top: 1px solid var(--border); }
        .error-banner { display: flex; align-items: center; gap: 8px; background: var(--warning-light); color: var(--warning); padding: 8px 16px; border-radius: var(--radius-md); margin-bottom: 16px; font-size: 0.85rem; }
        .failed-state { text-align: center; padding: 48px 0; }
        .error-icon { color: var(--destructive); margin-bottom: 16px; }
        .failed-state h3 { margin: 0 0 16px; color: var(--destructive); }
        .error-list { list-style: none; padding: 0; color: var(--muted-foreground); font-size: 0.85rem; }
        .error-list li { padding: 4px 0; }
        .btn { display: inline-flex; align-items: center; gap: 6px; padding: 10px 24px; border-radius: var(--radius-md); font-size: 0.9rem; font-weight: 500; cursor: pointer; border: none; transition: background 0.15s; }
        .btn-primary { background: var(--primary); color: var(--primary-foreground); }
        .btn-primary:hover { filter: brightness(1.1); }
        .btn-secondary { background: var(--secondary); color: var(--secondary-foreground); }
        .btn-outline { background: transparent; border: 1px solid var(--border); color: var(--muted-foreground); }
        .btn-outline:hover { background: var(--secondary); }
        .btn-row { display: flex; gap: 12px; justify-content: center; margin-top: 16px; }
        @keyframes fade-in { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
      `}</style>
    </div>
  )
}
