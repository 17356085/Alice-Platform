import { useCallback, useEffect, useMemo, useState } from 'react'
import { Blocks, Bot, Box, Cable, RefreshCw, Server, Workflow } from 'lucide-react'
import { api } from '@/api/client'
import { ENDPOINTS } from '@/api/endpoints'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { EmptyState, ErrorState, LoadingState, PageHeader } from '@/components/shared'

type Registry = { agents: Array<{ id: string; skills: string[] }>; skills: string[]; workflows: Array<{ workflow_id: string; name: string; status: string; version: string }>; providers: Array<{ provider_id: string; name: string; type: string; status: string }>; environments: Array<{ environment_id: string; name: string; base_url: string; is_default: boolean }>; plugins: Array<{ name: string; version: string; description: string; loaded: boolean; error?: string | null }> }
type Tab = 'agents' | 'workflows' | 'providers' | 'environments' | 'plugins'
export default function RegistryView() {
  const [data, setData] = useState<Registry | null>(null); const [tab, setTab] = useState<Tab>('agents'); const [loading, setLoading] = useState(true); const [error, setError] = useState('')
  const load = useCallback(async () => { setLoading(true); setError(''); try { setData(await api.get<Registry>(ENDPOINTS.REGISTRY)) } catch { setError('无法加载注册资源。请确认服务正在运行后重试。') } finally { setLoading(false) } }, [])
  useEffect(() => { load() }, [load])
  const tabs = useMemo(() => [{ id: 'agents', label: 'Agents', count: data?.agents.length || 0, icon: Bot }, { id: 'workflows', label: 'Workflows', count: data?.workflows.length || 0, icon: Workflow }, { id: 'providers', label: 'Providers', count: data?.providers.length || 0, icon: Server }, { id: 'environments', label: 'Environments', count: data?.environments.length || 0, icon: Box }, { id: 'plugins', label: 'Plugins', count: data?.plugins.length || 0, icon: Cable }] as const, [data])
  return <div className="mx-auto flex w-full max-w-7xl flex-col gap-5 p-4 sm:p-6"><PageHeader eyebrow="Discoverable resources" title="注册中心" description="统一浏览可在项目中组合、运行和评估的资源。" actions={<Button variant="outline" size="sm" onClick={() => void load()} disabled={loading}><RefreshCw data-icon="inline-start" className={loading ? 'animate-spin' : ''} />刷新</Button>} />
    {error ? <ErrorState message={error} action={<Button variant="outline" size="sm" onClick={() => void load()}>重试</Button>} /> : null}{loading ? <LoadingState rows={5} /> : null}
    {!loading && !error && data ? <><Tabs value={tab} onValueChange={value => setTab(value as Tab)}><TabsList className="mb-4 h-auto flex-wrap justify-start gap-1 bg-transparent p-0">{tabs.map(({ id, label, count, icon: Icon }) => <TabsTrigger key={id} value={id} className="gap-2 data-[state=active]:bg-secondary"><Icon size={14} />{label}<span className="text-muted-foreground">{count}</span></TabsTrigger>)}</TabsList></Tabs><Card><CardContent className="p-0"><RegistryList tab={tab} data={data} /></CardContent></Card></> : null}
  </div>
}
function RegistryList({ tab, data }: { tab: Tab; data: Registry }) {
  const rows = tab === 'agents' ? data.agents.map(item => ({ title: item.id, meta: `${item.skills.length} skills`, tags: item.skills })) : tab === 'workflows' ? data.workflows.map(item => ({ title: item.name, meta: `${item.workflow_id} · v${item.version}`, tags: [item.status] })) : tab === 'providers' ? data.providers.map(item => ({ title: item.name, meta: `${item.provider_id} · ${item.type}`, tags: [item.status] })) : tab === 'environments' ? data.environments.map(item => ({ title: item.name, meta: item.base_url || item.environment_id, tags: item.is_default ? ['default'] : [] })) : data.plugins.map(item => ({ title: item.name, meta: item.description || `v${item.version}`, tags: [item.loaded ? 'loaded' : 'unavailable'] }))
  if (!rows.length) return <EmptyState title="尚未发现资源" description="创建资源或配置 Plugin 后，它会出现在这个分类中。" />
  return <div className="divide-y divide-border">{rows.map(row => <div key={`${tab}-${row.title}`} className="flex flex-wrap items-center justify-between gap-3 px-6 py-4"><div className="min-w-0"><p className="m-0 font-medium">{row.title}</p><p className="mb-0 mt-1 truncate text-xs text-muted-foreground">{row.meta}</p></div><div className="flex flex-wrap justify-end gap-1">{row.tags.slice(0, 4).map(tag => <Badge key={tag} variant="secondary">{tag}</Badge>)}</div></div>)}</div>
}
