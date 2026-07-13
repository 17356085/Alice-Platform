/** Onboarding Wizard — multi-step project discovery. shadcn/ui edition. */
import { useState, useMemo, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useOnboardingStore, selectIsComplete, selectIsMenuReady, selectIsFailed, getStoredSession } from '@/stores/onboarding'
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

export default function OnboardingWizardView() {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const store = useOnboardingStore
  const isRunning = useOnboardingStore(s => s.isRunning)
  const isComplete = useOnboardingStore(selectIsComplete)
  const isMenuReady = useOnboardingStore(selectIsMenuReady)
  const isFailed = useOnboardingStore(selectIsFailed)
  const isCancelled = useOnboardingStore(s => s.step === 'cancelled')
  const progress = useOnboardingStore(s => s.progress)
  const errors = useOnboardingStore(s => s.errors)
  const sourceType = useOnboardingStore(s => s.sourceType)
  const projectId = useOnboardingStore(s => s.projectId)
  const checkpoint = useOnboardingStore(s => s.checkpoint)
  const baseUrl = useOnboardingStore(s => s.baseUrl)
  const start = useOnboardingStore(s => s.start)
  const cancel = useOnboardingStore(s => s.cancel)
  const reset = useOnboardingStore(s => s.reset)
  const restore = useOnboardingStore(s => s.restore)
  const pollStatus = useOnboardingStore(s => s.pollStatus)
  const { disconnect, wsError } = useOnboardingWS()
  const steps = [
    { key: 'source', label: t('onboarding.step_source'), icon: FolderOpen },
    { key: 'discovery', label: t('onboarding.step_discovery'), icon: Wifi },
    { key: 'confirm', label: t('onboarding.step_review'), icon: ListTree },
    { key: 'results', label: t('onboarding.step_results'), icon: CheckCircle2 },
  ]

  const [sourceChosen, setSourceChosen] = useState(false)
  const [restored, setRestored] = useState(false)

  // Restore session on mount (page refresh recovery)
  useEffect(() => {
    const saved = getStoredSession()
    if (saved && saved.sessionId && !restored) {
      restore(saved)
      setSourceChosen(true)
      setRestored(true)
      // Resume polling immediately
      pollStatus()
    }
  }, [restore, pollStatus, restored])

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

  function handleBack() {
    // Only back from URL input to source selection (before scanning starts)
    if (currentStepIndex === 1 && !isRunning && sourceType === 'url') {
      setSourceChosen(false)
      store.setState({ baseUrl: '' })
    }
  }

  function openProject() {
    navigate(`/projects/${projectId}/kanban`)
  }

  useEffect(() => {
    return () => { disconnect() }
  }, [disconnect])

  return (
    <div className="max-w-[720px] mx-auto py-8 px-6 animate-[fade-in_0.3s_ease-out]">
      <header className="mb-8 text-center">
        <h2 className="text-2xl font-bold text-foreground mb-2">{t('onboarding.wizard_title')}</h2>
        <p className="text-sm text-muted-foreground m-0">
          {t('onboarding.wizard_desc')}
        </p>
      </header>

      {/* Step indicators */}
      <nav className="flex justify-center gap-10 mb-6">
        {steps.map((step, i) => (
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
          <span>{/api[_ -]?key|api key/i.test(wsError) ? t('onboarding.api_key_error') : wsError}</span>
        </div>
      )}

      <main className="min-h-[300px]">
        {!isCancelled && (
          <>
        {currentStepIndex === 0 && !sourceChosen && <StepChooseSource onChoose={onSourceChoose} />}
        {currentStepIndex === 1 && !isRunning && sourceType === 'url' && <StepUrlInput />}
        {currentStepIndex === 1 && isRunning && <StepScanning />}
        {currentStepIndex === 2 && <StepConfirmMenu />}
        {currentStepIndex === 3 && <StepResults />}
          </>
        )}
        {isFailed && (
          <div className="text-center py-12">
            <AlertTriangle size={48} className="text-destructive mb-4 mx-auto" />
            <h3 className="text-destructive mb-4">{t('onboarding.onboarding_failed')}</h3>
            {errors.length > 0 && (
              <ul className="list-none p-0 text-muted-foreground text-sm">
                {errors.map((err, i) => <li key={i} className="py-1">{err}</li>)}
              </ul>
            )}
            <div className="flex gap-3 justify-center mt-4">
              <Button variant="secondary" onClick={() => reset()}>{t('onboarding.try_again')}</Button>
            </div>
          </div>
        )}
        {isCancelled && (
          <div className="text-center py-12">
            <FolderOpen size={48} className="text-warning mb-4 mx-auto" />
            <h3 className="text-warning mb-2">{t('onboarding.onboarding_cancelled')}</h3>
            <p className="text-muted-foreground text-sm mb-4">
              {checkpoint
                ? `Partial results saved — ${checkpoint.pages?.length || 0} pages discovered. You can resume from where you left off.`
                : t('onboarding.no_partial_results')}
            </p>
            <div className="flex gap-3 justify-center mt-4">
              {checkpoint && (
                <Button variant="gradient" onClick={() => {
                  start(baseUrl, projectId, '', '', '', true)
                  setSourceChosen(true)
                }}>
                  {t('onboarding.resume_progress')} <ArrowRight size={16} />
                </Button>
              )}
              <Button variant="secondary" onClick={() => reset()}>{t('onboarding.restart')}</Button>
            </div>
          </div>
        )}
      </main>

      <footer className="flex justify-between gap-3 mt-6 pt-4 border-t border-border">
        <div>
          {/* Back button: only from URL input → source selection */}
          {currentStepIndex === 1 && !isRunning && sourceType === 'url' && (
            <Button variant="outline" onClick={handleBack}>← 上一步</Button>
          )}
        </div>
        <div className="flex gap-3">
        {(isRunning || isMenuReady) && <Button variant="outline" onClick={() => cancel()}>{t('onboarding.cancel')}</Button>}
        {isComplete && (
          <Button variant="gradient" onClick={openProject}>
            {t('onboarding.open_project')} <ArrowRight size={16} />
          </Button>
        )}
        </div>
      </footer>
    </div>
  )
}
