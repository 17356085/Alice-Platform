import { useCallback, useEffect, useState } from 'react'
import { BarChart3, Database, RefreshCw, Target } from 'lucide-react'
import { api } from '@/api/client'
import { ENDPOINTS } from '@/api/endpoints'
import { Badge, type BadgeVariant } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { EmptyState, ErrorState, LoadingState, PageHeader } from '@/components/shared'

type Evaluation = { evaluation_id: string; name: string; dataset_id: string; agent_id: string; status: string; created_at?: string; results?: { pass_rate?: number; total_examples?: number } }
type Dataset = { dataset_id: string; name: string; type: string; examples?: unknown[] }
const statusVariant = (status: string): BadgeVariant => ({ completed: 'success', running: 'info', pending: 'warning', failed: 'destructive' }[status] || 'outline') as BadgeVariant

export default function EvaluationsView() {
  const [evaluations, setEvaluations] = useState<Evaluation[]>([])
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const load = useCallback(async () => {
    setLoading(true); setError('')
    try {
      const [evaluationData, datasetData] = await Promise.all([
        api.get<{ evaluations: Evaluation[] }>(ENDPOINTS.EVALUATIONS_LIST), api.get<{ datasets: Dataset[] }>('/api/v1/datasets'),
      ])
      setEvaluations(evaluationData.evaluations || []); setDatasets(datasetData.datasets || [])
    } catch { setError('无法加载质量资源。请确认服务正在运行后重试。') } finally { setLoading(false) }
  }, [])
  useEffect(() => { load() }, [load])
  const completed = evaluations.filter(item => item.status === 'completed')
  const averagePassRate = completed.length ? completed.reduce((sum, item) => sum + (item.results?.pass_rate || 0), 0) / completed.length : 0
  return <div className="mx-auto flex w-full max-w-7xl flex-col gap-5 p-4 sm:p-6">
    <PageHeader eyebrow="Quality loop" title="质量评估" description="以 Dataset 驱动 Agent 与 Skill 的改进决策。" actions={<Button variant="outline" size="sm" onClick={() => void load()} disabled={loading}><RefreshCw data-icon="inline-start" className={loading ? 'animate-spin' : ''} />刷新</Button>} />
    <div className="mb-5 grid gap-3 sm:grid-cols-3"><Metric icon={Database} label="Datasets" value={datasets.length} /><Metric icon={Target} label="Evaluations" value={evaluations.length} /><Metric icon={BarChart3} label="平均通过率" value={completed.length ? `${Math.round(averagePassRate * 100)}%` : '—'} /></div>
    {error ? <ErrorState message={error} action={<Button variant="outline" size="sm" onClick={() => void load()}>重试</Button>} /> : null}
    {loading ? <LoadingState rows={3} /> : null}
    {!loading && !error ? <div className="grid gap-5 lg:grid-cols-[1.6fr_1fr]"><Card><CardHeader><CardTitle className="text-sm">评估任务</CardTitle></CardHeader><CardContent className="p-0">{evaluations.length === 0 ? <Empty label="尚未创建评估" hint="先从一次失败 Run 保存 Dataset Example，再创建评估任务。" /> : <div className="divide-y divide-border">{evaluations.map(item => <div key={item.evaluation_id} className="flex items-center justify-between gap-3 px-6 py-4"><div className="min-w-0"><p className="m-0 truncate font-medium">{item.name}</p><p className="mb-0 mt-1 truncate text-xs text-muted-foreground">{item.agent_id} · {item.dataset_id}</p></div><div className="flex shrink-0 items-center gap-3"><span className="text-xs text-muted-foreground">{item.results?.pass_rate != null ? `${Math.round(item.results.pass_rate * 100)}%` : '—'}</span><Badge variant={statusVariant(item.status)}>{item.status}</Badge></div></div>)}</div>}</CardContent></Card><Card><CardHeader><CardTitle className="text-sm">可用 Dataset</CardTitle></CardHeader><CardContent className="p-0">{datasets.length === 0 ? <Empty label="尚无 Dataset" hint="从 Run Inspector 保存失败样本即可建立质量基线。" /> : <div className="divide-y divide-border">{datasets.map(item => <div key={item.dataset_id} className="px-6 py-4"><p className="m-0 font-medium">{item.name}</p><p className="mb-0 mt-1 text-xs text-muted-foreground">{item.type} · {item.examples?.length || 0} examples</p></div>)}</div>}</CardContent></Card></div> : null}
  </div>
}
function Metric({ icon: Icon, label, value }: { icon: typeof BarChart3; label: string; value: string | number }) { return <Card><CardContent className="flex items-center gap-3 p-4"><div className="rounded-md bg-accent p-2 text-primary"><Icon size={17} /></div><div><div className="text-lg font-semibold leading-none">{value}</div><div className="mt-1 text-xs text-muted-foreground">{label}</div></div></CardContent></Card> }
function Empty({ label, hint }: { label: string; hint: string }) { return <EmptyState title={label} description={hint} /> }
