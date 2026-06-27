/** Onboarding Wizard — multi-step project discovery. shadcn/ui edition. */
import { useState, useMemo, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useOnboardingStore, selectIsComplete, selectIsMenuReady, selectIsFailed } from '@/stores/onboarding'
import { useOnboardingWS } from '@/hooks/useOnboardingWS'
import StepChooseSource from '@/components/onboarding/StepChooseSource'
import StepUrlInput from '@/components/onboarding/StepUrlInput'
import StepScanning from '@/components/onboarding/StepScanning'
import StepConfirmMenu from '@/components/onboarding/StepConfirmMenu'
import StepResults from '@/components/onboarding/StepResults'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { cn } from '@/lib/utils'
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
    <div className="max-w-[720px] mx-auto py-8 px-6 animate-[fade-in_0.3s_ease-out]">
      <header className="mb-8 text-center">
        <h2 className="text-2xl font-bold text-foreground mb-2">New Project Onboarding</h2>
        <p className="text-sm text-muted-foreground m-0">
          Enter a URL — TLO auto-discovers the application structure
        </p>
      </header>

      {/* Step indicators */}
      <nav className="flex justify-center gap-10 mb-6">
        {STEPS.map((step, i) => (
          <div key={step.key}
            className={cn(
              'flex flex-col items-center gap-1.5 transition-colors',
              i === currentStepIndex ? 'text-primary' :
              i < currentStepIndex ? 'text-success' :
              'text-muted-foreground',
              isFailed && i === currentStepIndex && 'text-destructive'
            )}
          >
            <step.icon size={18} />
            <span className="text-xs font-medium">{step.label}</span>
          </div>
        ))}
      </nav>

      {/* Progress bar */}
      {(isRunning || isComplete) && (
        <div className="flex items-center gap-3 mb-6">
          <Progress
            value={Math.round(progress * 100)}
            className={cn(isComplete && '[&>div]:bg-success', isFailed && '[&>div]:bg-destructive')}
          />
          <span className="text-xs font-semibold text-muted-foreground min-w-[3em] text-right">
            {Math.round(progress * 100)}%
          </span>
        </div>
      )}

      {wsError && (
        <div className="flex items-center gap-2 bg-warning-light text-warning px-4 py-2 rounded-lg mb-4 text-sm">
          <AlertTriangle size={16} />
          <span>{wsError}</span>
        </div>
      )}

      <main className="min-h-[300px]">
        {currentStepIndex === 0 && !sourceChosen && <StepChooseSource onChoose={onSourceChoose} />}
        {currentStepIndex === 1 && !isRunning && sourceType === 'url' && <StepUrlInput />}
        {currentStepIndex === 1 && isRunning && <StepScanning />}
        {currentStepIndex === 2 && <StepConfirmMenu />}
        {currentStepIndex === 3 && <StepResults />}
        {isFailed && (
          <div className="text-center py-12">
            <AlertTriangle size={48} className="text-destructive mb-4 mx-auto" />
            <h3 className="text-destructive mb-4">Onboarding failed</h3>
            {errors.length > 0 && (
              <ul className="list-none p-0 text-muted-foreground text-sm">
                {errors.map((err, i) => <li key={i} className="py-1">{err}</li>)}
              </ul>
            )}
            <div className="flex gap-3 justify-center mt-4">
              <Button variant="secondary" onClick={() => reset()}>Try Again</Button>
            </div>
          </div>
        )}
      </main>

      <footer className="flex justify-end gap-3 mt-6 pt-4 border-t border-border">
        {(isRunning || isMenuReady) && <Button variant="outline" onClick={() => cancel()}>Cancel</Button>}
        {isComplete && (
          <Button variant="gradient" onClick={openProject}>
            Open Project <ArrowRight size={16} />
          </Button>
        )}
      </footer>
    </div>
  )
}
