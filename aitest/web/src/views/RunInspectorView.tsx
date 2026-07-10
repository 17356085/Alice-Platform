/** Run Inspector — full-page DevTools-style execution detail.
 *
 * Routes: /projects/:id/runs/:runId
 * Data:  GET /api/runs/{run_id}/inspector
 *
 * Tabs: Timeline | Artifacts | Agent Calls | Metrics | Logs | Tree
 */
import { useState, useEffect, useCallback, type ReactNode } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '@/api/client'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { Skeleton } from '@/components/ui/skeleton'
import SwimlaneTimeline from '@/components/SwimlaneTimeline'
import type { SwimlaneEntry } from '@/components/SwimlaneTimeline'
import {
  ArrowLeft, Clock, Box, MessageSquare, BarChart3, FileText, GitBranch,
  CheckCircle2, XCircle, AlertTriangle, Circle, Timer, DollarSign, Zap,
  ChevronRight, ExternalLink, Download, Copy, Eye, Code, Image, FileSpreadsheet
} from 'lucide-react'

// ── Types ──────────────────────────────────────────────────────────────

interface InspectorHeader {
  run_id: string; request_id: string; workspace_id: string; org_id: string
  triggered_by: string; capability: string; agent: string; module: string
  pages: string[]; mode: string; status: string
  created_at: string; completed_at: string; duration_ms: number
  total_tokens: number; total_cost: number; agent_runs: number
  artifacts_count: number; error_message: string
}

interface TimelineEntry {
  ts: string; type: string; message: string; detail?: Record<string, unknown>
}

interface PhaseInfo {
  name: string; status: string; started_at: string | null
  completed_at: string | null; duration_ms: number
}

interface AgentCall {
  event_id: string; event_type: string; timestamp: string
  agent: string; prompt: string; response: string
  tokens: number; cost: number; tool_calls: Array<{ name: string; args: unknown; result: unknown }>
}

interface ArtifactInfo {
  event_id: string; timestamp: string; path: string; name?: string; type: string
  size: number; mime_type: string; source_phase: string
}

interface LogEntry {
  timestamp: string; level: string; event_type: string; message: string
}

interface TreeNode {
  type: string; name: string; timestamp: string; status: string
  children?: TreeNode[]
}

interface InspectorData {
  header: InspectorHeader
  timeline: TimelineEntry[]
  phases: PhaseInfo[]
  agent_calls: AgentCall[]
  artifacts: ArtifactInfo[]
  logs: LogEntry[]
  execution_tree: TreeNode[]
  summary: Record<string, unknown>
}

// ── Helpers ─────────────────────────────────────────────────────────────

const STATUS_COLOR: Record<string, string> = {
  completed: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  failed: 'bg-red-500/10 text-red-400 border-red-500/20',
  running: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  cancelled: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  timed_out: 'bg-orange-500/10 text-orange-400 border-orange-500/20',
  pending: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
}

const STATUS_ICON: Record<string, typeof CheckCircle2> = {
  completed: CheckCircle2,
  failed: XCircle,
  running: Circle,
  cancelled: AlertTriangle,
  timed_out: AlertTriangle,
}

const LOG_COLOR: Record<string, string> = {
  error: 'text-red-400',
  warn: 'text-amber-400',
  info: 'text-slate-400',
}

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`
  if (ms < 60_000) return `${(ms / 1000).toFixed(1)}s`
  const m = Math.floor(ms / 60_000)
  const s = Math.round((ms % 60_000) / 1000)
  return `${m}m ${s}s`
}

function formatCost(cost: number): string {
  return `$${cost.toFixed(4)}`
}

function tsShort(iso: string): string {
  return iso ? iso.slice(11, 19) : '—'
}

function tsFull(iso: string): string {
  return iso ? iso.slice(0, 19).replace('T', ' ') : '—'
}

// ── Component ───────────────────────────────────────────────────────────

export default function RunInspectorView() {
  const { id: pid, runId } = useParams<{ id: string; runId: string }>()
  const navigate = useNavigate()
  const [data, setData] = useState<InspectorData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [expandedCall, setExpandedCall] = useState<string | null>(null)
  const [report, setReport] = useState<Record<string, unknown> | null>(null)
  const [reportLoading, setReportLoading] = useState(false)

  const fetchData = useCallback(async () => {
    if (!runId) return
    setLoading(true)
    setError('')
    try {
      const result = await api.get<InspectorData>(`/api/runs/${runId}/inspector`)
      setData(result)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load')
    } finally {
      setLoading(false)
    }
  }, [runId])

  const fetchReport = useCallback(async () => {
    if (!runId) return
    setReportLoading(true)
    try {
      const res = await api.get<{ report: Record<string, unknown> | null }>(`/api/runs/${runId}/report`)
      setReport(res.report)
    } catch { setReport(null) }
    finally { setReportLoading(false) }
  }, [runId])

  useEffect(() => { fetchData() }, [fetchData])

  // ── Loading ──
  if (loading) {
    return (
      <div className="p-6 max-w-7xl mx-auto space-y-4">
        <Skeleton className="h-12 w-64" />
        <div className="grid grid-cols-4 gap-4">
          {Array.from({ length: 8 }).map((_, i) => <Skeleton key={i} className="h-24" />)}
        </div>
        <Skeleton className="h-96" />
      </div>
    )
  }

  // ── Error ──
  if (error || !data) {
    return (
      <div className="p-6 max-w-7xl mx-auto text-center">
        <XCircle size={48} className="mx-auto text-red-400 mb-4" />
        <p className="text-lg text-red-400">{error || 'Run not found'}</p>
        <Button variant="outline" className="mt-4" onClick={() => navigate(-1)}>
          <ArrowLeft size={14} /> Back
        </Button>
      </div>
    )
  }

  const { header, timeline, phases, agent_calls, artifacts, logs, execution_tree } = data
  const StatusIcon = STATUS_ICON[header.status] || Circle

  // ── Render ──
  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Back + Title */}
      <div className="flex items-center gap-3 mb-6">
        <Button variant="ghost" size="sm" onClick={() => navigate(-1)}>
          <ArrowLeft size={16} />
        </Button>
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-bold">Run {header.run_id.slice(0, 12)}</h1>
            <Badge variant="outline" className={STATUS_COLOR[header.status]}>
              <StatusIcon size={12} className="mr-1" />
              {header.status}
            </Badge>
          </div>
        </div>
      </div>

      {/* ── Header KPI cards ── */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-3 mb-6">
        <KpiCard icon={Timer} label="Duration" value={formatDuration(header.duration_ms)} />
        <KpiCard icon={Zap} label="Module" value={header.module || '—'} />
        <KpiCard icon={Box} label="Agent" value={header.agent || '—'} />
        <KpiCard icon={MessageSquare} label="Agent Runs" value={String(header.agent_runs)} />
        <KpiCard icon={Code} label="Tokens" value={header.total_tokens.toLocaleString()} />
        <KpiCard icon={DollarSign} label="Cost" value={formatCost(header.total_cost)} />
        <KpiCard icon={FileText} label="Artifacts" value={String(header.artifacts_count)} />
        <KpiCard icon={GitBranch} label="Pages" value={String(header.pages?.length || 0)} />
      </div>

      {/* Error banner */}
      {header.error_message && (
        <div className="mb-6 p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm font-mono">
          {header.error_message}
        </div>
      )}

      {/* ── Meta row ── */}
      <div className="flex flex-wrap gap-x-6 gap-y-1 text-xs text-muted-foreground mb-6">
        <span>Request: <code>{header.request_id?.slice(0, 12)}</code></span>
        <span>Workspace: <code>{header.workspace_id}</code></span>
        <span>Triggered by: {header.triggered_by}</span>
        <span>Capability: {header.capability}</span>
        <span>Mode: {header.mode}</span>
        <span>Created: {tsFull(header.created_at)}</span>
        {header.completed_at && <span>Completed: {tsFull(header.completed_at)}</span>}
      </div>

      <Separator className="mb-6" />

      {/* ── Tabs ── */}
      <Tabs defaultValue="timeline" className="w-full">
        <TabsList className="mb-6">
          <TabsTrigger value="timeline"><Clock size={14} className="mr-1" /> Timeline</TabsTrigger>
          <TabsTrigger value="artifacts"><Box size={14} className="mr-1" /> Artifacts ({artifacts.length})</TabsTrigger>
          <TabsTrigger value="agent-calls"><MessageSquare size={14} className="mr-1" /> Agent Calls ({agent_calls.length})</TabsTrigger>
          <TabsTrigger value="metrics"><BarChart3 size={14} className="mr-1" /> Metrics</TabsTrigger>
          <TabsTrigger value="logs"><FileText size={14} className="mr-1" /> Logs ({logs.length})</TabsTrigger>
          <TabsTrigger value="tree"><GitBranch size={14} className="mr-1" /> Tree</TabsTrigger>
          <TabsTrigger value="report" onClick={fetchReport}><FileSpreadsheet size={14} className="mr-1" /> Report</TabsTrigger>
        </TabsList>

        {/* ── Timeline Tab ── */}
        <TabsContent value="timeline">
          <SwimlaneTimeline
            entries={timeline as SwimlaneEntry[]}
            className="mt-0"
          />
        </TabsContent>

        {/* ── Artifacts Tab ── */}
        <TabsContent value="artifacts">
          {artifacts.length === 0 ? (
            <EmptyState icon={Box} message="No artifacts in this run" />
          ) : (
            <div className="grid gap-3">
              {artifacts.map((a) => (
                <Card key={a.path || a.name} className="hover:bg-accent/5 transition-colors">
                  <CardContent className="p-4 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <ArtifactIcon type={a.type} />
                      <div>
                        <div className="text-sm font-medium font-mono">{a.path}</div>
                        <div className="text-xs text-muted-foreground flex gap-3 mt-0.5">
                          <span>{a.type}</span>
                          {a.size > 0 && <span>{(a.size / 1024).toFixed(1)} KB</span>}
                          <span>{tsShort(a.timestamp)}</span>
                          {a.source_phase && <span>Phase: {a.source_phase}</span>}
                        </div>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button variant="ghost" size="icon" title="Copy path"><Copy size={14} /></Button>
                      <Button variant="ghost" size="icon" title="Download"><Download size={14} /></Button>
                      <Button variant="ghost" size="icon" title="Preview"><Eye size={14} /></Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* ── Agent Calls Tab ── */}
        <TabsContent value="agent-calls">
          {agent_calls.length === 0 ? (
            <EmptyState icon={MessageSquare} message="No agent LLM calls recorded" />
          ) : (
            <div className="space-y-3">
              {agent_calls.map((call) => (
                <Card key={call.event_id || call.timestamp} className="hover:bg-accent/5 transition-colors">
                  <CardHeader className="py-3 px-4 cursor-pointer"
                    onClick={() => setExpandedCall(expandedCall === call.event_id ? null : call.event_id)}>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <ChevronRight size={14}
                          className={`transition-transform ${expandedCall === call.event_id ? 'rotate-90' : ''}`} />
                        <span className="text-sm font-medium">{call.agent || call.event_type}</span>
                        <span className="text-xs text-muted-foreground font-mono">{tsShort(call.timestamp)}</span>
                      </div>
                      <div className="flex gap-3 text-xs text-muted-foreground">
                        {call.tokens > 0 && <span>{call.tokens} tokens</span>}
                        {call.cost > 0 && <span>${call.cost.toFixed(4)}</span>}
                        {call.tool_calls?.length > 0 && <span>{call.tool_calls.length} tool calls</span>}
                      </div>
                    </div>
                  </CardHeader>
                  {expandedCall === call.event_id && (
                    <CardContent className="px-4 pb-4 space-y-3 border-t border-border pt-3">
                      {call.prompt && (
                        <div>
                          <div className="text-xs font-semibold text-muted-foreground mb-1">Prompt</div>
                          <pre className="text-xs font-mono bg-muted p-3 rounded-md max-h-[200px] overflow-y-auto whitespace-pre-wrap">
                            {call.prompt}
                          </pre>
                        </div>
                      )}
                      {call.response && (
                        <div>
                          <div className="text-xs font-semibold text-muted-foreground mb-1">Response</div>
                          <pre className="text-xs font-mono bg-muted p-3 rounded-md max-h-[200px] overflow-y-auto whitespace-pre-wrap">
                            {call.response}
                          </pre>
                        </div>
                      )}
                      {call.tool_calls?.length > 0 && (
                        <div>
                          <div className="text-xs font-semibold text-muted-foreground mb-1">Tool Calls</div>
                          {call.tool_calls.map((tc: Record<string, unknown>, j: number) => (
                            <div key={tc.name ? `${String(tc.name)}-${j}` : j} className="bg-muted p-2 rounded-md mb-2 text-xs font-mono">
                              <span className="font-semibold text-primary">{String(tc.name ?? '')}</span>
                              {tc.args !== undefined && tc.args !== null ? <pre className="mt-1 text-[11px] opacity-70">{JSON.stringify(tc.args, null, 2)}</pre> : null}
                              {tc.result !== undefined && (
                                <pre className="mt-1 text-[11px] text-emerald-400">{JSON.stringify(tc.result, null, 2)}</pre>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </CardContent>
                  )}
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* ── Metrics Tab ── */}
        <TabsContent value="metrics">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader className="py-3"><CardTitle className="text-sm">Phase Breakdown</CardTitle></CardHeader>
              <CardContent>
                {phases.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No phase data</p>
                ) : (
                  <div className="space-y-2">
                    {phases.map((p, i) => (
                      <div key={i} className="flex items-center justify-between text-sm">
                        <div className="flex items-center gap-2">
                          <div className={`w-2 h-2 rounded-full ${
                            p.status === 'completed' ? 'bg-emerald-500' :
                            p.status === 'running' ? 'bg-blue-500 animate-pulse' : 'bg-slate-600'
                          }`} />
                          <span>{p.name}</span>
                        </div>
                        <span className="text-muted-foreground font-mono text-xs">
                          {formatDuration(p.duration_ms)}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="py-3"><CardTitle className="text-sm">Token Distribution</CardTitle></CardHeader>
              <CardContent>
                <div className="text-3xl font-bold">{header.total_tokens.toLocaleString()}</div>
                <div className="text-sm text-muted-foreground">Total tokens</div>
                {agent_calls.length > 0 && (
                  <div className="mt-3 text-xs text-muted-foreground">
                    {agent_calls.length} LLM call{agent_calls.length !== 1 ? 's' : ''} |
                    Avg {Math.round(header.total_tokens / Math.max(agent_calls.length, 1)).toLocaleString()} tokens/call
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="py-3"><CardTitle className="text-sm">Cost Analysis</CardTitle></CardHeader>
              <CardContent>
                <div className="text-3xl font-bold">{formatCost(header.total_cost)}</div>
                <div className="text-sm text-muted-foreground">Total cost</div>
                {header.total_tokens > 0 && (
                  <div className="mt-3 text-xs text-muted-foreground">
                    ${((header.total_cost / header.total_tokens) * 1_000_000).toFixed(2)} / 1M tokens
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="py-3"><CardTitle className="text-sm">Run Summary</CardTitle></CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div className="text-muted-foreground">Events:</div><div>{logs.length}</div>
                  <div className="text-muted-foreground">Phases:</div><div>{phases.length}</div>
                  <div className="text-muted-foreground">Artifacts:</div><div>{artifacts.length}</div>
                  <div className="text-muted-foreground">Pages:</div><div>{header.pages?.join(', ') || '—'}</div>
                  <div className="text-muted-foreground">Mode:</div><div>{header.mode}</div>
                  <div className="text-muted-foreground">Capability:</div><div>{header.capability}</div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* ── Logs Tab ── */}
        <TabsContent value="logs">
          <Card>
            <CardHeader className="py-3">
              <CardTitle className="text-sm">Structured Log ({logs.length} entries)</CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[500px]">
                <div className="font-mono text-xs space-y-0.5">
                  {logs.map((log, i) => (
                    <div key={i} className={`flex gap-3 py-0.5 hover:bg-muted/50 px-1 rounded ${LOG_COLOR[log.level]}`}>
                      <span className="text-muted-foreground shrink-0 w-[75px]">{tsShort(log.timestamp)}</span>
                      <span className={`shrink-0 w-[40px] font-semibold uppercase`}>{log.level}</span>
                      <span className="text-muted-foreground shrink-0 w-[140px] truncate">{log.event_type}</span>
                      <span className="truncate">{log.message}</span>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        {/* ── Execution Tree Tab ── */}
        <TabsContent value="tree">
          <Card>
            <CardHeader className="py-3"><CardTitle className="text-sm">Execution Tree</CardTitle></CardHeader>
            <CardContent>
              {execution_tree.length === 0 ? (
                <EmptyState icon={GitBranch} message="No tree data available" />
              ) : (
                <div className="font-mono text-sm">
                  {execution_tree.map((node, i) => (
                    <TreeNodeRow key={i} node={node} depth={0} />
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* ── AI Report Tab ── */}
        <TabsContent value="report">
          {reportLoading ? (
            <Card><CardContent className="py-8"><Skeleton className="h-64" /></CardContent></Card>
          ) : report ? (
            <ReportCard report={report} />
          ) : (
            <Card>
              <CardContent className="py-12 text-center">
                <FileSpreadsheet size={32} className="mx-auto mb-3 text-muted-foreground/30" />
                <p className="text-sm text-muted-foreground mb-2">AI Report not yet available</p>
                <p className="text-xs text-muted-foreground/60">
                  Reports are auto-generated when a run completes. The ReportConsumer must be active.
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
}

// ── Sub-components ───────────────────────────────────────────────────────

function KpiCard({ icon: Icon, label, value }: { icon: typeof Clock; label: string; value: string }) {
  return (
    <Card className="hover:bg-accent/5 transition-colors">
      <CardContent className="p-3 flex items-center gap-3">
        <div className="p-2 rounded-md bg-muted">
          <Icon size={14} className="text-muted-foreground" />
        </div>
        <div className="min-w-0">
          <div className="text-[11px] text-muted-foreground uppercase tracking-wider">{label}</div>
          <div className="text-sm font-semibold truncate">{value}</div>
        </div>
      </CardContent>
    </Card>
  )
}

function EmptyState({ icon: Icon, message }: { icon: typeof Box; message: string }) {
  return (
    <Card>
      <CardContent className="py-12 text-center">
        <Icon size={32} className="mx-auto text-muted-foreground/30 mb-3" />
        <p className="text-sm text-muted-foreground">{message}</p>
      </CardContent>
    </Card>
  )
}

function ArtifactIcon({ type }: { type: string }) {
  if (type === 'screenshot' || type === 'image') return <Image size={18} className="text-purple-400" />
  if (type === 'html' || type === 'trace') return <Code size={18} className="text-blue-400" />
  if (type === 'report') return <FileText size={18} className="text-emerald-400" />
  return <FileText size={18} className="text-muted-foreground" />
}

function TreeNodeRow({ node, depth }: { node: TreeNode; depth: number }) {
  const [expanded, setExpanded] = useState(depth < 2)
  const hasChildren = node.children && node.children.length > 0
  const statusColor = node.status === 'completed' ? 'text-emerald-400' :
    node.status === 'running' ? 'text-blue-400' :
    node.status === 'failed' ? 'text-red-400' : 'text-muted-foreground'

  return (
    <div>
      <div
        className={`flex items-center gap-2 py-1 hover:bg-muted/30 px-1 rounded cursor-pointer ${hasChildren ? '' : ''}`}
        style={{ paddingLeft: `${depth * 20 + 8}px` }}
        onClick={() => hasChildren && setExpanded(!expanded)}
      >
        {hasChildren ? (
          <ChevronRight size={12} className={`transition-transform ${expanded ? 'rotate-90' : ''}`} />
        ) : (
          <span className="w-3" />
        )}
        <span className={statusColor}>{node.type === 'phase' ? '●' : '○'}</span>
        <span className="font-medium">{node.name}</span>
        <span className={`text-xs ml-auto ${statusColor}`}>{node.status}</span>
      </div>
      {hasChildren && expanded && node.children!.map((child, i) => (
        <TreeNodeRow key={i} node={child} depth={depth + 1} />
      ))}
    </div>
  )
}

// ── AI Report Card ───────────────────────────────────────────────────────

function ReportCard({ report }: { report: Record<string, unknown> }) {
  const header = report.header as Record<string, unknown> | undefined
  const summary = report.summary as Record<string, unknown> | undefined
  const issues = (report.issues as Array<Record<string, string>>) || []
  const suggestions = (report.suggestions as Array<Record<string, string>>) || []

  const severityColor = (s: string) =>
    s === 'error' ? 'text-red-400 bg-red-500/10 border-red-500/20' :
    s === 'warning' ? 'text-amber-400 bg-amber-500/10 border-amber-500/20' :
    'text-blue-400 bg-blue-500/10 border-blue-500/20'

  const issuesBlock = issues.length > 0 ? (
    <Card>
      <CardHeader className="py-3"><CardTitle className="text-sm flex items-center gap-2">
        <AlertTriangle size={14} className="text-amber-400" /> Issues ({issues.length})
      </CardTitle></CardHeader>
      <CardContent className="space-y-2">
        {issues.map((issue, i) => (
          <div key={i} className={`p-3 rounded-lg border text-sm ${severityColor(issue.severity || 'info')}`}>
            <div className="font-medium">{String(issue.message || '')}</div>
            {issue.suggestion && <div className="text-xs mt-1 opacity-70">{String(issue.suggestion)}</div>}
          </div>
        ))}
      </CardContent>
    </Card>
  ) : null

  const suggestionsBlock = suggestions.length > 0 ? (
    <Card>
      <CardHeader className="py-3"><CardTitle className="text-sm flex items-center gap-2">
        <Zap size={14} className="text-blue-400" /> Suggestions ({suggestions.length})
      </CardTitle></CardHeader>
      <CardContent className="space-y-2">
        {suggestions.map((s, i) => (
          <div key={i} className="flex items-start gap-2 text-sm p-2">
            <ChevronRight size={14} className="text-blue-400 mt-0.5 shrink-0" />
            <span>{String(s.message || '')}</span>
          </div>
        ))}
      </CardContent>
    </Card>
  ) : null

  const timelineSummaryBlock = report.timeline_summary && Array.isArray(report.timeline_summary) ? (
    <Card>
      <CardHeader className="py-3"><CardTitle className="text-sm">Recent Events</CardTitle></CardHeader>
      <CardContent>
        <div className="space-y-1 font-mono text-xs text-muted-foreground">
          {(report.timeline_summary as string[]).map((msg, i) => (
            <div key={i} className="flex gap-2">
              <span className="text-muted-foreground/40">{i + 1}.</span>
              <span>{msg}</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  ) : null

  return (
    <div className="space-y-4">
      {/* Summary banner */}
      <Card className={summary?.success ? 'border-emerald-500/20 bg-emerald-500/5' : 'border-red-500/20 bg-red-500/5'}>
        <CardContent className="p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className={`p-2 rounded-full ${summary?.success ? 'bg-emerald-500/20' : 'bg-red-500/20'}`}>
              {summary?.success
                ? <CheckCircle2 size={20} className="text-emerald-400" />
                : <XCircle size={20} className="text-red-400" />}
            </div>
            <div>
              <h2 className="text-lg font-bold">
                {summary?.success ? 'Execution Completed' : 'Execution Failed'}
              </h2>
              <p className="text-xs text-muted-foreground">
                Generated {report.generated_at ? String(report.generated_at).slice(0, 19) : ''}
              </p>
            </div>
          </div>

          {/* KPI grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <MiniStat label="Duration" value={String(summary?.duration_display || '—')} />
            <MiniStat label="Tokens" value={Number(summary?.total_tokens || 0).toLocaleString()} />
            <MiniStat label="Cost" value={`$${Number(summary?.total_cost || 0).toFixed(4)}`} />
            <MiniStat label="Agent Runs" value={String(summary?.agent_runs || 0)} />
            <MiniStat label="Phases" value={String(summary?.phase_count || 0)} />
            <MiniStat label="Artifacts" value={String(summary?.artifact_count || 0)} />
            <MiniStat label="LLM Calls" value={String(summary?.llm_call_count || 0)} />
            <MiniStat label="Events" value={String(summary?.event_count || 0)} />
          </div>

          <div className="mt-3 text-xs text-muted-foreground flex flex-wrap gap-x-4 gap-y-1">
            <span>Module: <code>{String(header?.module || '—')}</code></span>
            <span>Agent: {String(header?.agent || '—')}</span>
            <span>Pages: {Array.isArray(header?.pages) ? (header.pages as string[]).join(', ') || '—' : '—'}</span>
          </div>
        </CardContent>
      </Card>

      {/* Issues */}
      {issuesBlock}

      {/* Suggestions */}
      {suggestionsBlock}

      {/* Timeline summary */}
      {timelineSummaryBlock}
    </div>
  )
}

function MiniStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="p-2 rounded-md bg-muted/30 text-center">
      <div className="text-[10px] text-muted-foreground uppercase">{label}</div>
      <div className="text-sm font-semibold font-mono">{value}</div>
    </div>
  )
}
