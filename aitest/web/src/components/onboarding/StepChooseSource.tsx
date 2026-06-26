/** Step 1: Choose source type (URL vs local project). React port. */
import { useState, useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import { Globe, FolderOpen, FileCode, CheckCircle, AlertTriangle, Loader2 } from 'lucide-react'
import { api } from '../../api/client'
import { ENDPOINTS } from '../../api/endpoints'

interface StepChooseSourceProps {
  onChoose: (sourceType: 'url' | 'local', value: string) => void
}

interface PathResult {
  valid: boolean; exists: boolean; has_package_json: boolean
  framework: string; framework_version: string; ui_library: string
  typescript: boolean; suggestions: string[]; error: string
}

export default function StepChooseSource({ onChoose }: StepChooseSourceProps) {
  const { t } = useTranslation()
  const [selected, setSelected] = useState<'url' | 'local'>('url')
  const [urlValue, setUrlValue] = useState('https://')
  const [projectPath, setProjectPath] = useState('')
  const [pathError, setPathError] = useState('')
  const [pathValidating, setPathValidating] = useState(false)
  const [pathResult, setPathResult] = useState<PathResult | null>(null)

  const frameworkLabel = useMemo(() => {
    if (!pathResult) return ''
    const r = pathResult
    if (r.framework === 'unknown') return '⚠️ 未识别框架'
    if (r.framework === 'error') return '⚠️ 检测异常'
    let label = `✅ ${r.framework}`
    if (r.framework_version) label += ` ${r.framework_version}`
    if (r.ui_library) label += ` + ${r.ui_library}`
    if (r.typescript) label += ' + TS'
    return label
  }, [pathResult])

  async function validatePath() {
    const raw = projectPath.trim()
    if (!raw) { setPathError(t('onboarding.invalid_path')); return false }
    setPathValidating(true); setPathError(''); setPathResult(null)
    try {
      const result = await api.post<PathResult>(ENDPOINTS.ONBOARDING_VALIDATE, { project_path: raw })
      setPathResult(result)
      if (!result.exists) { setPathError(result.error || '路径不存在'); return false }
      if (!result.has_package_json) { setPathError(result.error || '未找到 package.json'); return false }
      return true
    } catch (e: any) { setPathError(`验证失败: ${e.message}`); return false }
    finally { setPathValidating(false) }
  }

  async function handleContinue() {
    if (selected === 'url') {
      if (!urlValue || !urlValue.startsWith('http')) { setPathError(t('onboarding.invalid_url')); return }
      onChoose('url', urlValue)
    } else {
      const valid = await validatePath()
      if (!valid) return
      onChoose('local', projectPath.trim())
    }
  }

  async function browseFolder() {
    if ('showDirectoryPicker' in window) {
      try {
        const handle = await (window as any).showDirectoryPicker()
        const p = handle.path || handle.name || ''
        setProjectPath(p)
        if (!handle.path) setPathError(`已选择 "${handle.name}"，请手动补全完整路径`)
      } catch { /* cancelled */ }
    } else {
      const input = document.createElement('input'); input.type = 'file'
      ;(input as any).webkitdirectory = true
      input.onchange = (e: any) => {
        if (e.target.files?.length) {
          const folder = e.target.files[0].webkitRelativePath.split('/')[0]
          setProjectPath(folder)
          setPathError(`已选择 "${folder}"，请手动补全完整路径`)
        }
      }
      input.click()
    }
  }

  return (
    <div className="step-choose">
      <h3>{t('onboarding.choose_title')}</h3>
      <div className="source-cards">
        <button className={`source-card${selected === 'url' ? ' selected' : ''}`} onClick={() => { setSelected('url'); setPathError(''); setPathResult(null) }}>
          <Globe size={32} /><div className="card-text"><strong>{t('onboarding.url_option')}</strong><span className="desc">{t('onboarding.url_desc')}</span></div>
        </button>
        <button className={`source-card${selected === 'local' ? ' selected' : ''}`} onClick={() => { setSelected('local'); setPathError('') }}>
          <FolderOpen size={32} /><div className="card-text"><strong>{t('onboarding.local_option')}</strong><span className="desc">{t('onboarding.local_desc')}</span></div>
        </button>
        <button className="source-card disabled" disabled>
          <FileCode size={32} /><div className="card-text"><strong>Import API spec</strong><span className="desc">OpenAPI/Swagger — coming soon</span></div>
        </button>
      </div>

      {selected === 'url' && (
        <div className="input-area">
          <label><Globe size={14} /> Application URL</label>
          <input value={urlValue} onChange={e => setUrlValue(e.target.value)} type="url" placeholder={t('onboarding.url_placeholder')} onKeyUp={e => e.key === 'Enter' && handleContinue()} />
        </div>
      )}

      {selected === 'local' && (
        <div className="input-area">
          <label><FolderOpen size={14} /> Project path</label>
          <div className="path-row">
            <input value={projectPath} onChange={e => { setProjectPath(e.target.value); setPathResult(null); setPathError('') }} type="text" placeholder={t('onboarding.path_placeholder')} onKeyUp={e => e.key === 'Enter' && handleContinue()} />
            <button className="btn-browse" onClick={browseFolder}>{t('onboarding.browse')}</button>
          </div>
          {pathValidating && <div className="status-row validating"><Loader2 size={14} className="spin" /> 正在验证项目路径...</div>}
          {!pathValidating && pathResult?.valid && <div className="status-row success"><CheckCircle size={14} /> {frameworkLabel}</div>}
          {!pathValidating && pathResult && !pathResult.has_package_json && (
            <div className="status-row warning">
              <AlertTriangle size={14} /> {pathError}
              {pathResult.suggestions.length > 0 && <div className="suggestions">{pathResult.suggestions.map((s, i) => <p key={i}>{s}</p>)}</div>}
            </div>
          )}
          <p className="hint">支持: Vue 3/2, React, Next.js, Nuxt, Angular</p>
        </div>
      )}

      {pathError && !pathResult && <p className="error-msg">{pathError}</p>}

      <button className="btn-continue" disabled={pathValidating} onClick={handleContinue}>
        {pathValidating && <Loader2 size={14} className="spin" />}
        {t('onboarding.continue')}
      </button>

      <style>{`
        .step-choose { padding: 16px 0; }
        .step-choose h3 { font-size: 1.05rem; font-weight: 600; margin: 0 0 20px; color: var(--foreground); }
        .source-cards { display: flex; flex-direction: column; gap: 10px; margin-bottom: 24px; }
        .source-card { display: flex; align-items: center; gap: 14px; padding: 16px; background: var(--card); border: 2px solid var(--border); border-radius: var(--radius-lg); cursor: pointer; text-align: left; transition: border-color .15s, box-shadow .15s; font-family: inherit; color: var(--foreground); }
        .source-card:hover:not(.disabled) { border-color: var(--primary); }
        .source-card.selected { border-color: var(--primary); box-shadow: var(--shadow-focus); }
        .source-card.disabled { opacity: .4; cursor: not-allowed; }
        .card-text { display: flex; flex-direction: column; gap: 2px; }
        .card-text strong { font-size: .9rem; }
        .desc { font-size: .78rem; color: var(--muted-foreground); }
        .input-area { margin-bottom: 16px; }
        .input-area label { display: flex; align-items: center; gap: 6px; font-size: .82rem; font-weight: 600; color: var(--foreground); margin-bottom: 6px; }
        .input-area input { width: 100%; padding: 10px 14px; border: 1px solid var(--border); border-radius: var(--radius-md); background: var(--card); color: var(--foreground); font-size: .9rem; box-sizing: border-box; }
        .input-area input:focus { outline: none; border-color: var(--primary); box-shadow: var(--shadow-focus); }
        .path-row { display: flex; gap: 8px; }
        .path-row input { flex: 1; }
        .btn-browse { padding: 10px 16px; background: var(--secondary); color: var(--secondary-foreground); border: 1px solid var(--border); border-radius: var(--radius-md); cursor: pointer; font-size: .85rem; white-space: nowrap; }
        .btn-browse:hover { background: var(--primary); color: var(--primary-foreground); }
        .hint { color: var(--muted-foreground); font-size: .75rem; margin: 4px 0 0; }
        .status-row { display: flex; align-items: flex-start; gap: 6px; margin-top: 8px; padding: 8px 12px; border-radius: var(--radius-md); font-size: .8rem; }
        .status-row.validating { background: var(--secondary); color: var(--secondary-foreground); }
        .status-row.success { background: #d4edda; color: #155724; }
        .status-row.warning { background: #fff3cd; color: #856404; flex-direction: column; }
        .suggestions { margin-top: 4px; }
        .suggestions p { margin: 2px 0; font-size: .75rem; opacity: .85; }
        .error-msg { color: var(--destructive); font-size: .82rem; margin: 8px 0; }
        .btn-continue { display: inline-flex; align-items: center; gap: 6px; padding: 10px 28px; background: var(--primary); color: var(--primary-foreground); border: none; border-radius: var(--radius-md); font-size: .9rem; font-weight: 600; cursor: pointer; margin-top: 8px; }
        .btn-continue:disabled { opacity: .6; cursor: not-allowed; }
        .btn-continue:hover:not(:disabled) { filter: brightness(1.1); }
        .spin { animation: spin 1s linear infinite; }
        @keyframes spin { to { transform: rotate(360deg); } }
      `}</style>
    </div>
  )
}
