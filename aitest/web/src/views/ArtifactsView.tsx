/** Artifacts — browser + preview + download. Epic 2: Artifact Center.
 *
 * Merges file artifacts (SOP-generated docs) + Run artifacts (execution-produced).
 * Preview renders: Markdown, Image, Code, JSON tree.
 */
import { useState, useEffect, useMemo, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '@/api/client'
import { useSettingsStore } from '../stores/settings'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { Skeleton } from '@/components/ui/skeleton'
import { Input } from '@/components/ui/input'
import {
  Sheet, SheetContent, SheetHeader, SheetTitle,
} from '@/components/ui/sheet'
import {
  FolderOpen, FileText, Image, FileSpreadsheet, Code, Eye, Download, Copy,
  Search, ChevronRight, XCircle, Clock, CheckCircle2, Filter, X
} from 'lucide-react'
import { cn } from '@/lib/utils'
import Markdown from '@/components/Markdown'

// ── Types ─────────────────────────────────────────────────────────────

interface ArtifactItem {
  id: string; type: 'file' | 'run_artifact'; name: string
  path: string; module: string; page: string
  exists: boolean; size: number; mime_type: string
  run_id?: string; timestamp?: string; artifact_type?: string
}

interface ArtifactContent {
  name: string; mime_type: string; encoding: string
  content: string; size: number; error?: string
}

// ── Constants ─────────────────────────────────────────────────────────

const TYPE_ICON: Record<string, typeof FileText> = {
  'text/markdown': FileText,
  'text/x-python': Code,
  'application/json': Code,
  'text/html': Code,
  'image/png': Image,
  'image/jpeg': Image,
  'image/svg+xml': Image,
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': FileSpreadsheet,
}

const TYPE_COLOR: Record<string, string> = {
  'text/markdown': 'text-blue-400',
  'text/x-python': 'text-emerald-400',
  'application/json': 'text-amber-400',
  'text/html': 'text-orange-400',
  'image/png': 'text-purple-400',
  'image/jpeg': 'text-purple-400',
}

function fileIcon(mime: string) {
  const Icon = TYPE_ICON[mime] || FileText
  const color = TYPE_COLOR[mime] || 'text-muted-foreground'
  return <Icon size={16} className={color} />
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

// ── Component ─────────────────────────────────────────────────────────

export default function ArtifactsView() {
  const { id: pid } = useParams<{ id: string }>()
  const theme = useSettingsStore(s => s.app.theme)
  const projectId = pid || 'default'

  const [artifacts, setArtifacts] = useState<ArtifactItem[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [filterType, setFilterType] = useState<'all' | 'file' | 'run_artifact'>('all')
  const [selected, setSelected] = useState<ArtifactItem | null>(null)
  const [content, setContent] = useState<ArtifactContent | null>(null)
  const [contentLoading, setContentLoading] = useState(false)
  const [moduleFilter, setModuleFilter] = useState('')

  // Fetch artifact list
  const fetchArtifacts = useCallback(async () => {
    setLoading(true)
    try {
      const data = await api.get<{ artifacts: ArtifactItem[] }>(`/api/v1/kpi/artifacts/${projectId}/all`)
      setArtifacts(data.artifacts || [])
    } catch { setArtifacts([]) }
    finally { setLoading(false) }
  }, [projectId])

  useEffect(() => { fetchArtifacts() }, [fetchArtifacts])

  // Fetch content when selected
  useEffect(() => {
    if (!selected || selected.type !== 'file') { setContent(null); return }
    let cancelled = false
    setContentLoading(true)
    api.get<ArtifactContent>(
      `/api/v1/kpi/artifacts/${projectId}/content?module=${encodeURIComponent(selected.module)}&page=${encodeURIComponent(selected.page)}&name=${encodeURIComponent(selected.name)}`
    ).then(data => { if (!cancelled) setContent(data) })
    .catch(() => { if (!cancelled) setContent(null) })
    .finally(() => { if (!cancelled) setContentLoading(false) })
    return () => { cancelled = true }
  }, [selected, projectId])

  // Filters
  const modules = useMemo(() => [...new Set(artifacts.map(a => a.module))].sort(), [artifacts])

  const filtered = useMemo(() => artifacts.filter(a => {
    if (filterType !== 'all' && a.type !== filterType) return false
    if (moduleFilter && a.module !== moduleFilter) return false
    if (search) {
      const q = search.toLowerCase()
      return a.name.toLowerCase().includes(q) || a.path.toLowerCase().includes(q) || a.module.toLowerCase().includes(q)
    }
    return true
  }), [artifacts, filterType, moduleFilter, search])

  const hasFilters = filterType !== 'all' || !!moduleFilter || !!search

  // Download handler
  const handleDownload = (item: ArtifactItem) => {
    const url = `/api/v1/kpi/artifacts/${projectId}/download?module=${encodeURIComponent(item.module)}&page=${encodeURIComponent(item.page)}&name=${encodeURIComponent(item.name)}`
    window.open(url, '_blank')
  }

  const handleCopyPath = (item: ArtifactItem) => {
    navigator.clipboard.writeText(item.path).catch(() => {})
  }

  // ── Loading ──
  if (loading) {
    return (
      <div className="p-6 h-full flex flex-col">
        <div className="flex items-center gap-2 mb-6"><Skeleton className="h-7 w-32" /></div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {Array.from({ length: 9 }).map((_, i) => <Skeleton key={i} className="h-20" />)}
        </div>
      </div>
    )
  }

  // ── Empty ──
  if (artifacts.length === 0) {
    return (
      <div className="p-6 h-full flex flex-col">
        <h1 className="text-xl font-bold mb-6 flex items-center gap-2"><FolderOpen size={20} /> 产物</h1>
        <Card className="text-center py-16 flex-1">
          <CardContent>
            <FolderOpen size={48} className="mx-auto mb-4 opacity-20" />
            <p className="text-sm text-muted-foreground">No artifacts yet. Run SOP to generate.</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  // ── Main ──
  return (
    <div className="p-6 h-[calc(100vh-100px)] flex flex-col">
      {/* Header */}
      <div className="flex items-center gap-3 mb-4 shrink-0">
        <h1 className="text-xl font-bold flex items-center gap-2"><FolderOpen size={20} /> 产物</h1>
        <Badge variant="secondary" className="text-[10px]">{artifacts.length} items</Badge>
        <div className="flex-1" />
        <Button variant="ghost" size="icon" onClick={fetchArtifacts} title="Refresh"><Clock size={14} /></Button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 mb-4 shrink-0 flex-wrap">
        <div className="relative w-64">
          <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search artifacts..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="pl-8 h-8 text-xs"
          />
          {search && (
            <button onClick={() => setSearch('')} className="absolute right-2 top-1/2 -translate-y-1/2">
              <X size={12} className="text-muted-foreground" />
            </button>
          )}
        </div>

        <select value={moduleFilter} onChange={e => setModuleFilter(e.target.value)}
          className="h-8 text-xs border border-border rounded-md bg-background px-2">
          <option value="">All Modules</option>
          {modules.map(m => <option key={m} value={m}>{m}</option>)}
        </select>

        <div className="flex gap-1">
          {(['all', 'file', 'run_artifact'] as const).map(t => (
            <button key={t} onClick={() => setFilterType(t)}
              className={cn('px-2.5 py-1 text-[11px] rounded-md border transition-colors',
                filterType === t ? 'bg-primary/10 border-primary/30 text-primary' : 'border-border text-muted-foreground hover:bg-accent')}>
              {t === 'all' ? 'All' : t === 'file' ? 'SOP Docs' : 'Run Outputs'}
            </button>
          ))}
        </div>

        {hasFilters && (
          <button onClick={() => { setFilterType('all'); setModuleFilter(''); setSearch('') }}
            className="text-[11px] text-muted-foreground hover:text-foreground flex items-center gap-1">
            <X size={11} /> Clear
          </button>
        )}

        <span className="text-[11px] text-muted-foreground ml-auto">{filtered.length} results</span>
      </div>

      {/* Artifact grid */}
      <ScrollArea className="flex-1">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 pr-2">
          {filtered.map(item => (
            <Card
              key={item.id}
              className={cn(
                'hover:bg-accent/10 transition-colors cursor-pointer group',
                !item.exists && 'opacity-50'
              )}
              onClick={() => setSelected(item)}
            >
              <CardContent className="p-3.5">
                <div className="flex items-start gap-3">
                  <div className="p-2 rounded-md bg-muted shrink-0">
                    {fileIcon(item.mime_type)}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="text-sm font-medium truncate">{item.name}</div>
                    <div className="text-[11px] text-muted-foreground mt-0.5">
                      {item.module}{item.page ? ` / ${item.page}` : ''}
                    </div>
                    <div className="flex items-center gap-2 mt-1.5">
                      {item.type === 'run_artifact' ? (
                        <Badge variant="outline" className="text-[9px] px-1.5 py-0 bg-purple-500/10 text-purple-400 border-purple-500/20">Run</Badge>
                      ) : (
                        <Badge variant="outline" className="text-[9px] px-1.5 py-0">Doc</Badge>
                      )}
                      {item.size > 0 && <span className="text-[10px] text-muted-foreground">{formatSize(item.size)}</span>}
                      {!item.exists && <span className="text-[10px] text-amber-400">Not generated</span>}
                    </div>
                  </div>
                  <div className="flex flex-col gap-1 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
                    {item.exists && (
                      <>
                        <Button variant="ghost" size="icon" className="h-7 w-7" title="Preview"
                          onClick={e => { e.stopPropagation(); setSelected(item) }}>
                          <Eye size={13} />
                        </Button>
                        <Button variant="ghost" size="icon" className="h-7 w-7" title="Download"
                          onClick={e => { e.stopPropagation(); handleDownload(item) }}>
                          <Download size={13} />
                        </Button>
                        <Button variant="ghost" size="icon" className="h-7 w-7" title="Copy path"
                          onClick={e => { e.stopPropagation(); handleCopyPath(item) }}>
                          <Copy size={13} />
                        </Button>
                      </>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {filtered.length === 0 && (
          <div className="text-center py-16 text-muted-foreground text-sm">No artifacts match filters.</div>
        )}
      </ScrollArea>

      {/* Detail Sheet */}
      <Sheet open={!!selected} onOpenChange={() => { setSelected(null); setContent(null) }}>
        <SheetContent className="w-[520px] sm:max-w-[520px] flex flex-col p-0">
          {selected && (
            <>
              <SheetHeader className="px-5 py-4 border-b border-border shrink-0">
                <SheetTitle className="text-sm font-mono truncate">{selected.name}</SheetTitle>
                <div className="flex items-center gap-2 mt-1">
                  <p className="text-[11px] text-muted-foreground font-mono">
                    {selected.module}{selected.page ? ` / ${selected.page}` : ''}
                  </p>
                  {selected.run_id && (
                    <Badge variant="outline" className="text-[9px]">Run: {selected.run_id.slice(0, 8)}</Badge>
                  )}
                </div>
              </SheetHeader>

              <div className="flex-1 overflow-y-auto p-5">
                {/* Run artifact info */}
                {selected.type === 'run_artifact' && (
                  <div className="space-y-4">
                    <ArtifactMeta item={selected} />
                    <Separator />
                    <Card className="p-4 bg-muted/30 border-dashed">
                      <p className="text-xs text-muted-foreground text-center">
                        Run artifact — view in Run Inspector for timeline context.
                      </p>
                    </Card>
                  </div>
                )}

                {/* File artifact content */}
                {selected.type === 'file' && (
                  <div className="space-y-4">
                    <ArtifactMeta item={selected} />
                    <Separator />
                    {contentLoading ? (
                      <Skeleton className="h-64" />
                    ) : content?.error ? (
                      <Card className="p-4 bg-red-500/5 border-red-500/20">
                        <p className="text-xs text-red-400">{content.error}</p>
                      </Card>
                    ) : content ? (
                      <ArtifactContentRenderer content={content} />
                    ) : (
                      <Card className="p-4 bg-muted/30 border-dashed">
                        <p className="text-xs text-muted-foreground text-center">Failed to load content.</p>
                      </Card>
                    )}
                  </div>
                )}
              </div>

              {/* Actions */}
              {selected.exists && (
                <div className="flex gap-2 p-4 border-t border-border shrink-0">
                  <Button variant="outline" size="sm" className="gap-1.5 text-xs flex-1"
                    onClick={() => handleDownload(selected)}>
                    <Download size={13} /> Download
                  </Button>
                  <Button variant="outline" size="sm" className="gap-1.5 text-xs"
                    onClick={() => handleCopyPath(selected)}>
                    <Copy size={13} /> Copy Path
                  </Button>
                </div>
              )}
            </>
          )}
        </SheetContent>
      </Sheet>
    </div>
  )
}

// ── Sub-components ─────────────────────────────────────────────────────

function ArtifactMeta({ item }: { item: ArtifactItem }) {
  const IconComponent = TYPE_ICON[item.mime_type] || FileText
  return (
    <div className="space-y-2 text-sm">
      <div className="flex items-center gap-2">
        <IconComponent size={18} className={TYPE_COLOR[item.mime_type] || 'text-muted-foreground'} />
        <span className="font-semibold">{item.name}</span>
        {item.mime_type && <Badge variant="secondary" className="text-[9px]">{item.mime_type.split('/')[1]}</Badge>}
      </div>
      <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-muted-foreground">
        <div>Module: <span className="font-mono">{item.module}</span></div>
        {item.page && <div>Page: <span className="font-mono">{item.page}</span></div>}
        {item.size > 0 && <div>Size: {formatSize(item.size)}</div>}
        {item.timestamp && <div>Time: <span className="font-mono">{item.timestamp.slice(0, 19)}</span></div>}
        <div>Status: <span className={item.exists ? 'text-emerald-400' : 'text-amber-400'}>
          {item.exists ? 'Generated' : 'Not generated'}</span></div>
      </div>
    </div>
  )
}

function ArtifactContentRenderer({ content }: { content: ArtifactContent }) {
  // Image
  if (content.mime_type.startsWith('image/')) {
    return (
      <div className="space-y-2">
        <img src={content.content} alt={content.name}
          className="w-full rounded-lg border border-border" />
        <p className="text-[10px] text-muted-foreground text-center">
          {formatSize(content.size)} — {content.mime_type}
        </p>
      </div>
    )
  }

  // Markdown
  if (content.mime_type === 'text/markdown' || content.name.endsWith('.md')) {
    return (
      <div className="prose prose-sm prose-invert max-w-none">
        <Markdown content={content.content} />
      </div>
    )
  }

  // Code (JSON, Python, HTML, etc.)
  if (['application/json', 'text/x-python', 'text/html', 'text/css', 'text/javascript', 'text/yaml'].includes(content.mime_type)) {
    const lang = content.mime_type.split('/')[1] === 'json' ? 'json' :
      content.mime_type === 'text/x-python' ? 'python' :
      content.mime_type === 'text/html' ? 'html' : ''
    return (
      <div className="space-y-2">
        <pre className="text-xs font-mono bg-muted p-4 rounded-lg overflow-x-auto max-h-[500px] overflow-y-auto whitespace-pre-wrap">
          {content.content.slice(0, 50000)}
        </pre>
        {content.content.length > 50000 && (
          <p className="text-[10px] text-amber-400">Content truncated ({(content.content.length / 1024).toFixed(0)} KB total)</p>
        )}
      </div>
    )
  }

  // Fallback — plain text
  return (
    <pre className="text-xs font-mono bg-muted p-4 rounded-lg overflow-x-auto max-h-[500px] overflow-y-auto whitespace-pre-wrap">
      {content.content.slice(0, 10000)}
    </pre>
  )
}
