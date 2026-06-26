/** Step: URL input form for URL-based onboarding. React port. */
import { useState } from 'react'
import { useOnboardingStore } from '@/stores/onboarding'
import { Globe, Lock, Play, Loader2 } from 'lucide-react'

export default function StepUrlInput() {
  const store = useOnboardingStore
  const start = useOnboardingStore(s => s.start)
  const [url, setUrl] = useState('https://')
  const [projectId, setProjectId] = useState('')
  const [username, setUsername] = useState('admin')
  const [password, setPassword] = useState('')
  const [validating, setValidating] = useState(false)
  const [urlError, setUrlError] = useState('')

  function isValidUrl(val: string): boolean {
    try { new URL(val); return true } catch { return false }
  }

  async function handleStart() {
    setUrlError('')
    if (!url || !isValidUrl(url)) { setUrlError('Please enter a valid URL'); return }
    const pid = projectId.trim() || url.replace(/https?:\/\//, '').replace(/[.\/]/g, '-').replace(/-+$/, '').substring(0, 40)
    setValidating(true)
    await start(url, pid, username, password)
    setValidating(false)
  }

  return (
    <div className="step-url">
      <div className="form-group">
        <label><Globe size={16} /><span>Application URL</span></label>
        <input value={url} onChange={e => setUrl(e.target.value)} type="url" placeholder="https://your-app.example.com" className={urlError ? 'error' : ''} onKeyUp={e => e.key === 'Enter' && handleStart()} />
        {urlError && <p className="field-error">{urlError}</p>}
        <p className="hint">Paste the base URL of your web application</p>
      </div>
      <div className="form-group">
        <label><span>Project Name (optional)</span></label>
        <input value={projectId} onChange={e => setProjectId(e.target.value)} type="text" placeholder="auto-detected from URL" />
        <p className="hint">Short slug for this project. Auto-generated if empty.</p>
      </div>
      <div className="credentials-row">
        <div className="form-group">
          <label><Lock size={16} /><span>Username</span></label>
          <input value={username} onChange={e => setUsername(e.target.value)} type="text" placeholder="admin" />
        </div>
        <div className="form-group">
          <label><Lock size={16} /><span>Password</span></label>
          <input value={password} onChange={e => setPassword(e.target.value)} type="password" placeholder="(if login required)" />
        </div>
      </div>
      <button className="btn-start" disabled={validating || !url} onClick={handleStart}>
        {validating ? <Loader2 size={18} className="spin" /> : <Play size={18} />}
        <span>{validating ? 'Connecting...' : 'Start Discovery'}</span>
      </button>
      <style>{`
        .step-url { padding: 16px 0; }
        .form-group { margin-bottom: 20px; }
        .form-group label { display: flex; align-items: center; gap: 8px; font-size: 0.85rem; font-weight: 600; color: var(--foreground); margin-bottom: 6px; }
        .form-group input { width: 100%; padding: 10px 14px; border: 1px solid var(--border); border-radius: var(--radius-md); background: var(--card); color: var(--foreground); font-size: 0.9rem; box-sizing: border-box; }
        .form-group input:focus { outline: none; border-color: var(--primary); box-shadow: var(--shadow-focus); }
        .form-group input.error { border-color: var(--destructive); }
        .field-error { color: var(--destructive); font-size: 0.8rem; margin: 4px 0 0; }
        .hint { color: var(--muted-foreground); font-size: 0.78rem; margin: 4px 0 0; }
        .credentials-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
        .btn-start { display: inline-flex; align-items: center; gap: 8px; padding: 12px 32px; background: var(--primary); color: var(--primary-foreground); border: none; border-radius: var(--radius-md); font-size: 0.95rem; font-weight: 600; cursor: pointer; transition: filter 0.15s; margin-top: 8px; }
        .btn-start:hover:not(:disabled) { filter: brightness(1.1); }
        .btn-start:disabled { opacity: 0.5; cursor: not-allowed; }
        .spin { animation: spin 1s linear infinite; }
        @keyframes spin { to { transform: rotate(360deg); } }
      `}</style>
    </div>
  )
}
