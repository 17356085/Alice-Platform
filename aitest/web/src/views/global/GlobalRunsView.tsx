import { useCallback, useEffect, useMemo, useState } from 'react'
import { Clock3, RefreshCw, Search, TerminalSquare } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { api } from '@/api/client'
import { ENDPOINTS } from '@/api/endpoints'
import { Badge, type BadgeVariant } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'

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

  return <div className="mx-auto w-full max-w-7xl p-6">
    <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div>
        <div className="mb-1 flex items-center gap-2 text-primary"><Clock3 size={18} /><span className="text-xs font-semibold">全局执行</span></div>
        <h1 className="m-0 text-xl font-semibold tracking-tight">运行记录</h1>
        <p className="mb-0 mt-1 text-sm text-muted-foreground">查看所有项目的执行状态、目标和资源消耗。</p>
      </div>
      <Button variant="outline" size="sm" onClick={load} disabled={loading}><RefreshCw size={14} className={loading ? 'animate-spin' : ''} />刷新</Button>
    </div>

    <Card className="mb-4">
      <CardContent className="flex flex-wrap gap-3 p-4">
        <div className="relative min-w-[220px] flex-1"><Search size={15} className="pointer-events-none absolute left-3 top-2.5 text-muted-foreground" /><Input value={query} onChange={e => setQuery(e.target.value)} className="pl-9" placeholder="搜索 Run、Agent、模块或项目" /></div>
        <select aria-label="按状态筛选" value={status} onChange={e => setStatus(e.target.value)} className="h-9 rounded-md border border-input bg-background px-3 text-sm">
          <option value="">全部状态</option><option value="running">运行中</option><option value="completed">已完成</option><option value="failed">失败</option><option value="pending">等待中</option>
        </select>
      </CardContent>
    </Card>

    {error ? <p role="alert" className="rounded-md bg-destructive-light p-4 text-sm text-destructive">{error}</p> : null}
    {loading ? <div className="space-y-2">{[1, 2, 3, 4].map(i => <div key={i} className="h-16 animate-pulse rounded-md bg-muted" />)}</div> : null}
    {!loading && !error && filtered.length === 0 ? <Card><CardContent className="py-14 text-center"><TerminalSquare size={32} className="mx-auto mb-3 text-muted-foreground/50" /><p className="m-0 font-medium">尚无匹配的运行记录</p><p className="mb-0 mt-1 text-sm text-muted-foreground">从项目执行页启动一个 Workflow 或 Agent 后，记录会出现在这里。</p></CardContent></Card> : null}
    {!loading && !error && filtered.length > 0 ? <Card><CardContent className="p-0"><div className="overflow-x-auto"><table className="w-full min-w-[760px] text-left text-sm"><thead className="border-b border-border bg-muted/40 text-xs text-muted-foreground"><tr><th className="px-5 py-3 font-medium">目标</th><th className="px-4 py-3 font-medium">状态</th><th className="px-4 py-3 font-medium">项目 / 模块</th><th className="px-4 py-3 font-medium">资源</th><th className="px-5 py-3 font-medium">创建时间</th></tr></thead><tbody>{filtered.map(run => <tr key={run.run_id} onClick={() => navigate(`/projects/${run.workspace_id || 'default'}/runs/${run.run_id}`)} className="cursor-pointer border-b border-border/70 transition-colors last:border-0 hover:bg-accent/60"><td className="px-5 py-3"><div className="font-medium">{run.target_id || run.agent || '未命名目标'}</div><div className="mt-0.5 font-mono text-xs text-muted-foreground">{run.run_id}</div></td><td className="px-4 py-3"><Badge variant={statusVariant(run.status)}>{run.status}</Badge></td><td className="px-4 py-3"><div>{run.workspace_id || '—'}</div><div className="mt-0.5 text-xs text-muted-foreground">{run.module || '—'}</div></td><td className="px-4 py-3 text-muted-foreground">{run.total_tokens?.toLocaleString() || '—'} tokens</td><td className="px-5 py-3 text-muted-foreground">{run.created_at ? new Date(run.created_at).toLocaleString() : '—'}</td></tr>)}</tbody></table></div></CardContent></Card> : null}
  </div>
}
