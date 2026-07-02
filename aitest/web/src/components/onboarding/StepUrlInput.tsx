/** Step: URL input form for URL-based onboarding. React port.
 *
 * v3: Enforces network URL — must start with http:// or https://.
 *     Local file paths rejected. Clear validation errors.
 */
import { useState } from 'react'
import { useOnboardingStore } from '@/stores/onboarding'
import { Globe, Lock, Play, Loader2, AlertTriangle, FolderOpen } from 'lucide-react'
import { pickFolder } from '@/lib/browseFolder'

export default function StepUrlInput() {
  const store = useOnboardingStore
  const start = useOnboardingStore(s => s.start)
  const baseUrl = useOnboardingStore(s => s.baseUrl)
  // Inherit URL from StepChooseSource (baseUrl), not start fresh
  const [url, setUrl] = useState(baseUrl && baseUrl.startsWith('http') ? baseUrl : 'https://')
  const [projectId, setProjectId] = useState('')
  const [username, setUsername] = useState('admin')
  const [password, setPassword] = useState('')
  const [outputPath, setOutputPath] = useState('')
  const [outputError, setOutputError] = useState('')
  const [validating, setValidating] = useState(false)
  const [urlError, setUrlError] = useState('')

  function validateNetworkUrl(val: string): string {
    if (!val || val.trim().length < 8) return '请输入 URL'
    // Must start with http:// or https://
    if (!/^https?:\/\/.+/.test(val.trim())) {
      return 'URL 必须以 http:// 或 https:// 开头 — 不支持本地文件路径'
    }
    try {
      const parsed = new URL(val.trim())
      // Must have a real hostname (not just protocol)
      if (!parsed.hostname || parsed.hostname === '') {
        return 'URL 缺少主机名 (hostname)'
      }
      // File protocol explicitly rejected
      if (parsed.protocol === 'file:') {
        return '不支持 file:// 协议 — 本地项目请选择"本地项目"'
      }
      return ''
    } catch {
      return 'URL 格式无效 — 请确认格式: https://example.com'
    }
  }

  async function browseFolder() {
    const path = await pickFolder()
    if (path) {
      setOutputPath(path)
    } else {
      setOutputError('无法获取完整路径。请手动输入测试项目的存放路径，例如: D:\\TestingProject\\my-project')
    }
  }

  async function handleStart() {
    const urlErr = validateNetworkUrl(url)
    setUrlError(urlErr)
    if (urlErr) return

    // Output path is required for URL source
    if (!outputPath.trim()) {
      setOutputError('请选择测试项目存放路径')
      return
    }
    setOutputError('')

    const pid = projectId.trim() || url.replace(/https?:\/\//, '').replace(/[.\/]/g, '-').replace(/-+$/, '').substring(0, 40)
    setValidating(true)
    await start(url.trim(), pid, username, password, outputPath.trim())
    setValidating(false)
  }

  return (
    <div className="step-url">
      <div className="form-group">
        <label><Globe size={16} /><span>网络地址 (必填)</span></label>
        <input
          value={url}
          onChange={e => { setUrl(e.target.value); setUrlError('') }}
          type="url"
          placeholder="https://your-app.example.com"
          className={urlError ? 'error' : ''}
          onKeyUp={e => e.key === 'Enter' && handleStart()}
        />
        {urlError && (
          <p className="field-error">
            <AlertTriangle size={12} className="inline mr-1" />
            {urlError}
          </p>
        )}
        <p className="hint">被测应用的网络地址。必须以 http:// 或 https:// 开头。本地文件路径不支持。</p>
      </div>
      <div className="form-group">
        <label><span>项目名称 (可选)</span></label>
        <input value={projectId} onChange={e => setProjectId(e.target.value)} type="text" placeholder="从 URL 自动生成" />
        <p className="hint">简短标识符。留空则从 URL 自动提取。</p>
      </div>
      <div className="credentials-row">
        <div className="form-group">
          <label><Lock size={16} /><span>用户名</span></label>
          <input value={username} onChange={e => setUsername(e.target.value)} type="text" placeholder="admin" />
        </div>
        <div className="form-group">
          <label><Lock size={16} /><span>密码</span></label>
          <input value={password} onChange={e => setPassword(e.target.value)} type="password" placeholder="(如需登录)" />
        </div>
      </div>
      <div className="form-group">
        <label><FolderOpen size={16} /><span>测试项目存放路径 (必填)</span></label>
        <div className="path-row">
          <input
            value={outputPath}
            onChange={e => { setOutputPath(e.target.value); setOutputError('') }}
            type="text"
            placeholder="D:\Desktop\TestingProject\my-project\"
            className={outputError ? 'error' : ''}
            onKeyUp={e => e.key === 'Enter' && handleStart()}
          />
          <button className="btn-browse" type="button" onClick={browseFolder}>浏览</button>
        </div>
        {outputError && (
          <p className="field-error">
            <AlertTriangle size={12} className="inline mr-1" />
            {outputError}
          </p>
        )}
        <p className="hint">平台生成的测试脚本、Page Object、治理文档将存放在此目录</p>
      </div>
      <button className="btn-start" disabled={validating || url.length < 8} onClick={handleStart}>
        {validating ? <Loader2 size={18} className="spin" /> : <Play size={18} />}
        <span>{validating ? '连接中...' : '开始发现'}</span>
      </button>
      <style>{`
        .step-url { padding: 16px 0; }
        .form-group { margin-bottom: 20px; }
        .form-group label { display: flex; align-items: center; gap: 8px; font-size: 0.85rem; font-weight: 600; color: var(--foreground); margin-bottom: 6px; }
        .form-group input { width: 100%; padding: 10px 14px; border: 1px solid var(--border); border-radius: var(--radius-md); background: var(--card); color: var(--foreground); font-size: 0.9rem; box-sizing: border-box; }
        .form-group input:focus { outline: none; border-color: var(--primary); box-shadow: var(--shadow-focus); }
        .form-group input.error { border-color: var(--destructive); }
        .field-error { color: var(--destructive); font-size: 0.8rem; margin: 4px 0 0; display: flex; align-items: center; gap: 4px; }
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
