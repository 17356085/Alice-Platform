import { useCallback, useEffect, useMemo, useState } from 'react'
import { Clock3, RefreshCw, Search, TerminalSquare } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { api } from '@/api/client'
import { ENDPOINTS } from '@/api/endpoints'
import { Badge, type BadgeVariant } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { EmptyState, ErrorState, LoadingState, PageHeader } from '@/components/shared'

type Run = {
  run_id: string; workspace_id: string; target_type?: string; target_id?: string
  agent: string; module: string; status: string; created_at: string
  total_tokens?: number; total_cost?: number
}

const statusVariant = (status: string): BadgeVariant => ({
  completed: 'success', running: 'info', pending: 'warning', failed: 'destructive',
  cancelled: 'secondary', timed_out: 'warning',
}[status] || 'outline') as BadgeVariant

export default function GlobalRunsView() {
  const navigate = useNavigate()
  const [runs, setRuns] = useState<Run[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [query, setQuery] = useState('')
  const [status, setStatus] = useState('')

  const load = useCallback(async () => {
    setLoading(true); setError('')
    try {
      const data = await api.get<{ runs: Run[] }>(`${ENDPOINTS.RUNS_LIST}?limit=100`)
      setRuns(data.runs || [])
    } catch {
      setError('无法加载运行记录。请确认服务正在运行后重试。')
    } finally { setLoading(false) }
  }, [])

  useEffect(() => { load() }, [load])

  const filtered = useMemo(() => runs.filter(run => {
    const needle = query.trim().toLowerCase()
    const matchesQuery = !needle || [run.run_id, run.agent, run.module, run.target_id, run.workspace_id]
      .filter(Boolean).some(value => (value ?? '').toLowerCase().includes(needle))
    return matchesQuery && (!status || run.status === status)
  }), [runs, query, status])

  return <div className="mx-auto flex w-full max-w-7xl flex-col gap-5 p-4 sm:p-6">
    <PageHeader eyebrow="Global execution" title="运行记录" description="查看所有项目的执行状态、目标和资源消耗。" actions={<Button variant="outline" size="sm" onClick={() => void load()} disabled={loading}><RefreshCw data-icon="inline-start" className={loading ? 'animate-spin' : ''} />刷新</Button>} />

    <Card className="mb-4">
      <CardContent className="flex flex-wrap gap-3 p-4">
        <div className="relative min-w-[220px] flex-1"><Search size={15} className="pointer-events-none absolute left-3 top-2.5 text-muted-foreground" /><Input value={query} onChange={e => setQuery(e.target.value)} className="pl-9" placeholder="搜索 Run、Agent、模块或项目" /></div>
        <Select value={status || 'all'} onValueChange={value => setStatus(value === 'all' ? '' : value)}><SelectTrigger className="h-9 w-full sm:w-36"><SelectValue placeholder="全部状态" /></SelectTrigger><SelectContent><SelectItem value="all">全部状态</SelectItem><SelectItem value="running">运行中</SelectItem><SelectItem value="completed">已完成</SelectItem><SelectItem value="failed">失败</SelectItem><SelectItem value="pending">等待中</SelectItem></SelectContent></Select>
      </CardContent>
    </Card>

    {error ? <ErrorState message={error} action={<Button variant="outline" size="sm" onClick={() => void load()}>重试</Button>} /> : null}
    {loading ? <LoadingState rows={4} /> : null}
    {!loading && !error && filtered.length === 0 ? <EmptyState icon={TerminalSquare} title="尚无匹配的运行记录" description="从项目执行页启动一个 Workflow 或 Agent 后，记录会出现在这里。" /> : null}
    {!loading && !error && filtered.length > 0 ? <Card><CardContent className="p-0"><div className="overflow-x-auto"><table className="w-full min-w-[760px] text-left text-sm"><thead className="border-b border-border bg-muted/40 text-xs text-muted-foreground"><tr><th className="px-5 py-3 font-medium">目标</th><th className="px-4 py-3 font-medium">状态</th><th className="px-4 py-3 font-medium">项目 / 模块</th><th className="px-4 py-3 font-medium">资源</th><th className="px-5 py-3 font-medium">创建时间</th></tr></thead><tbody>{filtered.map(run => <tr key={run.run_id} onClick={() => navigate(`/projects/${run.workspace_id || 'default'}/runs/${run.run_id}`)} className="cursor-pointer border-b border-border/70 transition-colors last:border-0 hover:bg-accent/60"><td className="px-5 py-3"><div className="font-medium">{run.target_id || run.agent || '未命名目标'}</div><div className="mt-0.5 font-mono text-xs text-muted-foreground">{run.run_id}</div></td><td className="px-4 py-3"><Badge variant={statusVariant(run.status)}>{run.status}</Badge></td><td className="px-4 py-3"><div>{run.workspace_id || '—'}</div><div className="mt-0.5 text-xs text-muted-foreground">{run.module || '—'}</div></td><td className="px-4 py-3 text-muted-foreground">{run.total_tokens?.toLocaleString() || '—'} tokens</td><td className="px-5 py-3 text-muted-foreground">{run.created_at ? new Date(run.created_at).toLocaleString() : '—'}</td></tr>)}</tbody></table></div></CardContent></Card> : null}
  </div>
}
