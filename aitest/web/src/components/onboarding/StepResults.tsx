/** Step: Results — project config summary + finalize.
 *
 * Shows: tech stack, test categories, test tech stack, test path, network address.
 * Replaces minimal "X pages found" with actionable project setup.
 */
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useOnboardingStore } from '@/stores/onboarding'
import { useProjectStore } from '@/stores/project'
import { api } from '@/api/client'
import {
  CheckCircle2, FolderOpen, Globe, Monitor, Server, Code, TestTube,
  Wrench, MapPin, ArrowRight, AlertTriangle, Loader2, Info, Search
} from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Separator } from '@/components/ui/separator'

// ── Constants ──────────────────────────────────────────────────────────

const TEST_CATEGORIES = [
  { id: 'smoke', label: '冒烟测试', desc: '核心流程快速验证' },
  { id: 'functional', label: '功能测试', desc: '全部页面功能验证' },
  { id: 'regression', label: '回归测试', desc: '已有功能回归验证' },
  { id: 'ui', label: 'UI 测试', desc: '页面元素、布局验证' },
  { id: 'performance', label: '性能测试', desc: '页面加载、响应时间' },
  { id: 'security', label: '安全测试', desc: 'XSS、权限、认证' },
]

const TEST_TECH_STACKS = [
  { id: 'pytest-selenium', label: 'Pytest + Selenium', desc: 'Python 标准方案，兼容现有 SOP' },
  { id: 'pytest-playwright', label: 'Pytest + Playwright', desc: '现代方案，更快更稳定' },
  { id: 'jest-playwright', label: 'Jest + Playwright', desc: 'Node.js 方案' },
  { id: 'cypress', label: 'Cypress', desc: '前端友好，实时重载' },
]

export default function StepResults() {
  const navigate = useNavigate()
  const pages = useOnboardingStore(s => s.pages)
  const projectId = useOnboardingStore(s => s.projectId)
  const projectPath = useOnboardingStore(s => s.projectPath)
  const baseUrl = useOnboardingStore(s => s.baseUrl)
  const sourceType = useOnboardingStore(s => s.sourceType)
  const result = useOnboardingStore(s => s.result)
  const errors = useOnboardingStore(s => s.errors)
  const addProject = useProjectStore(s => s.addProject)
  const setActive = useProjectStore(s => s.setActive)

  // ── Local config state ──
  const [testCategories, setTestCategories] = useState<string[]>(['smoke', 'functional'])
  const [testTech, setTestTech] = useState('pytest-selenium')
  const [testPath, setTestPath] = useState(() => {
    // Default: under project root
    if (projectPath) return `${projectPath.replace(/\\/g, '/').replace(/\/$/, '')}/tests`
    return ''
  })
  const [networkUrl, setNetworkUrl] = useState(baseUrl)
  const [urlConfirmed, setUrlConfirmed] = useState(sourceType !== 'url') // URL type requires explicit confirm
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState('')

  const isUrlType = sourceType === 'url'
  const canSave = isUrlType ? (urlConfirmed && !!networkUrl && !!testPath) : !!testPath

  // Group pages by module
  const pagesByModule: Record<string, typeof pages> = {}
  for (const p of pages) {
    const key = p.menu_path?.[0] || 'Other'
    if (!pagesByModule[key]) pagesByModule[key] = []
    pagesByModule[key].push(p)
  }
  const moduleNames = Object.keys(pagesByModule)

  async function handleSave() {
    if (!canSave) return
    setSaving(true)
    setSaveError('')

    try {
      // Register project in store
      addProject({
        id: projectId,
        name: projectId,
        path: projectPath || networkUrl,
        modules: moduleNames,
        status: 'discovered',
      })
      setActive(projectId)

      // Save project config to backend
      await api.post('/api/v1/onboarding/config', {
        project_id: projectId,
        test_categories: testCategories,
        test_tech: testTech,
        test_path: testPath,
        network_url: networkUrl,
        source_type: sourceType,
      }).catch(() => {
        // Non-critical — config save is best-effort during migration
      })

      // Navigate to kanban
      navigate(`/projects/${projectId}/kanban`)
    } catch (e: unknown) {
      setSaveError((e instanceof Error ? e.message : String(e)) || 'Failed to save')
    } finally {
      setSaving(false)
    }
  }

  function toggleCategory(cat: string) {
    setTestCategories(prev =>
      prev.includes(cat) ? prev.filter(c => c !== cat) : [...prev, cat]
    )
  }

  return (
    <div className="step-results">
      {/* Success banner */}
      <div className="success-banner">
        <CheckCircle2 size={48} className="text-emerald-400" />
        <h3>发现完成</h3>
        <p>
          <strong>{projectId}</strong> — {moduleNames.length} 个模块, {pages.length} 个页面
        </p>
      </div>

      {/* ── Diagnostics (0 pages warning) ── */}
      {pages.length === 0 && (
        <Card className="mb-4 border-amber-500/30 bg-amber-500/5">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <AlertTriangle size={18} className="text-amber-400 shrink-0 mt-0.5" />
              <div className="space-y-2 text-sm">
                <div className="font-medium text-amber-400">发现 0 个页面</div>
                <div className="text-muted-foreground text-xs space-y-1">
                  {result?.diagnostics ? (
                    <>
                      <div>发现方式: {result.diagnostics.discovery_method === 'none' ? '未找到任何页面来源' : result.diagnostics.discovery_method}</div>
                      {result.diagnostics.login_attempted && (
                        <div>登录状态: {result.diagnostics.login_succeeded === true ? '✅ 成功' :
                          result.diagnostics.login_succeeded === false ? '❌ 失败' : '⚠️ 未知'}</div>
                      )}
                      <div>浏览器页面: {result.diagnostics.browser_pages || 0} | 源码路由: {result.diagnostics.source_routes || 0}</div>
                    </>
                  ) : (
                    <div>BrowserUse 未能从目标 URL 发现任何菜单或页面结构。</div>
                  )}
                </div>
                {errors.filter((e: string) => e.includes('⚠️')).map((e: string, i: number) => (
                  <div key={i} className="text-xs text-amber-400 bg-amber-500/5 p-2 rounded">{e}</div>
                ))}
                <div className="text-xs text-muted-foreground">
                  💡 建议: 检查目标 URL 是否正确、是否需要 VPN、登录凭据是否有效。
                  如果页面需要特定认证方式（如微信扫码、OAuth），请使用"本地项目"方式手动配置。
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="config-grid">
        {/* ── 1. Project Info ── */}
        <Card>
          <CardContent className="p-4">
            <h4 className="config-title"><Monitor size={16} /> 项目信息</h4>
            <div className="config-rows">
              <div className="config-row">
                <span className="config-label">项目 ID</span>
                <code>{projectId}</code>
              </div>
              <div className="config-row">
                <span className="config-label">类型</span>
                <Badge variant="secondary">{sourceType === 'url' ? 'URL (远程)' : '本地项目'}</Badge>
              </div>
              {sourceType === 'local' && projectPath && (
                <div className="config-row">
                  <span className="config-label">路径</span>
                  <code className="text-[11px]">{projectPath}</code>
                </div>
              )}
              <div className="config-row">
                <span className="config-label">发现页面</span>
                <span>{pages.length} 个</span>
              </div>
              <div className="config-row">
                <span className="config-label">模块</span>
                <div className="flex flex-wrap gap-1">
                  {moduleNames.map(m => <Badge key={m} variant="outline" className="text-[10px]">{m}</Badge>)}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* ── 2. Network Address (mandatory for URL) ── */}
        <Card className={isUrlType && !urlConfirmed ? 'border-amber-500/50' : ''}>
          <CardContent className="p-4">
            <h4 className="config-title"><Globe size={16} /> 网络地址 {isUrlType && <Badge variant="destructive" className="text-[9px]">必填</Badge>}</h4>
            {isUrlType ? (
              <div className="space-y-3">
                <Input
                  value={networkUrl}
                  onChange={e => { setNetworkUrl(e.target.value); setUrlConfirmed(false) }}
                  placeholder="https://your-app.example.com"
                  className="h-8 text-xs font-mono"
                />
                {!urlConfirmed && (
                  <div className="flex items-center gap-2 text-xs text-amber-400 bg-amber-500/5 border border-amber-500/20 rounded-md p-2">
                    <AlertTriangle size={14} />
                    <span>请确认网络地址正确 — 这是测试执行的目标地址</span>
                    <Button variant="outline" size="sm" className="text-[10px] h-6 ml-auto"
                      onClick={() => setUrlConfirmed(true)}
                      disabled={!networkUrl}>
                      确认地址
                    </Button>
                  </div>
                )}
                {urlConfirmed && (
                  <div className="flex items-center gap-2 text-xs text-emerald-400 bg-emerald-500/5 border border-emerald-500/20 rounded-md p-2">
                    <CheckCircle2 size={14} />
                    <span>网络地址已确认: <code>{networkUrl}</code></span>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-sm text-muted-foreground">
                <Globe size={14} className="inline mr-1" />
                本地项目 — 测试在本地执行
              </div>
            )}
          </CardContent>
        </Card>

        {/* ── 3. Test Categories ── */}
        <Card>
          <CardContent className="p-4">
            <h4 className="config-title"><TestTube size={16} /> 测试类别</h4>
            <div className="grid grid-cols-2 gap-2 mt-2">
              {TEST_CATEGORIES.map(cat => {
                const selected = testCategories.includes(cat.id)
                return (
                  <button
                    key={cat.id}
                    onClick={() => toggleCategory(cat.id)}
                    className={`text-left p-2.5 rounded-lg border text-xs transition-colors ${
                      selected
                        ? 'border-primary/40 bg-primary/5 text-primary'
                        : 'border-border hover:bg-accent/30 text-muted-foreground'
                    }`}
                  >
                    <div className="font-medium">{cat.label}</div>
                    <div className="text-[10px] opacity-70 mt-0.5">{cat.desc}</div>
                  </button>
                )
              })}
            </div>
          </CardContent>
        </Card>

        {/* ── 4. Test Tech Stack ── */}
        <Card>
          <CardContent className="p-4">
            <h4 className="config-title"><Wrench size={16} /> 测试技术栈</h4>
            <div className="space-y-2 mt-2">
              {TEST_TECH_STACKS.map(ts => (
                <button
                  key={ts.id}
                  onClick={() => setTestTech(ts.id)}
                  className={`w-full text-left p-2.5 rounded-lg border text-xs transition-colors ${
                    testTech === ts.id
                      ? 'border-primary/40 bg-primary/5 text-primary'
                      : 'border-border hover:bg-accent/30 text-muted-foreground'
                  }`}
                >
                  <div className="font-medium">{ts.label}</div>
                  <div className="text-[10px] opacity-70 mt-0.5">{ts.desc}</div>
                </button>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* ── 5. Test Project Location ── */}
        <Card>
          <CardContent className="p-4">
            <h4 className="config-title"><MapPin size={16} /> 测试项目存放地址</h4>
            <div className="space-y-2 mt-2">
              <Input
                value={testPath}
                onChange={e => setTestPath(e.target.value)}
                placeholder="D:\Projects\my-app\tests"
                className="h-8 text-xs font-mono"
              />
              <p className="text-[10px] text-muted-foreground">
                默认存放在被测项目根目录下。测试脚本、Page Object、报告均在此生成。
              </p>
              {sourceType === 'local' && projectPath && (
                <Button variant="ghost" size="sm" className="text-[10px] h-6"
                  onClick={() => setTestPath(`${projectPath.replace(/\\/g, '/').replace(/\/$/, '')}/tests`)}>
                  重置为默认路径
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Error */}
      {saveError && (
        <div className="flex items-center gap-2 text-sm text-red-400 bg-red-500/5 border border-red-500/20 rounded-md p-3 mt-4">
          <AlertTriangle size={16} />
          <span>{saveError}</span>
        </div>
      )}

      {/* Actions */}
      <div className="actions-bar">
        <Button
          variant="gradient"
          size="lg"
          onClick={handleSave}
          disabled={!canSave || saving}
          className="gap-2"
        >
          {saving ? <Loader2 size={16} className="animate-spin" /> : <ArrowRight size={16} />}
          {saving ? '保存中...' : '保存并打开项目'}
        </Button>
        {!canSave && isUrlType && (
          <p className="text-xs text-amber-400 mt-2">请先确认网络地址</p>
        )}
      </div>

      <style>{`
        .step-results { padding: 8px 0; }
        .success-banner { text-align: center; margin-bottom: 24px; }
        .success-banner h3 { font-size: 1.2rem; font-weight: 700; margin: 8px 0 4px; }
        .success-banner p { color: var(--muted-foreground); font-size: 0.85rem; margin: 0; }
        .config-grid { display: flex; flex-direction: column; gap: 12px; margin-bottom: 20px; }
        .config-title { display: flex; align-items: center; gap: 8px; font-size: 0.85rem; font-weight: 600; margin: 0 0 8px; }
        .config-rows { display: flex; flex-direction: column; gap: 6px; }
        .config-row { display: flex; align-items: center; gap: 8px; font-size: 0.8rem; }
        .config-label { color: var(--muted-foreground); min-width: 70px; font-size: 0.75rem; }
        .actions-bar { text-align: center; padding: 8px 0; }
      `}</style>
    </div>
  )
}
