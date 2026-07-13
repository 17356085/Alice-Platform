import { useState, useRef, useEffect } from "react";
import {
  LayoutDashboard, GitBranch, Activity, Brain, Wrench,
  History, Settings, Search, Bell, CheckCircle2, XCircle,
  Clock, Cpu, Zap, Network, Plus, MoreHorizontal,
  AlertTriangle, ChevronDown, Circle, Server, Tag,
  Terminal, Eye, Bot, Filter, Play, RotateCcw, Copy,
  ChevronLeft, Database, Hash, Layers, ArrowRight,
  ChevronRight, MessageSquare, FileText, BarChart2,
  Gauge, Box, Send, Download, File, Image, Code2,
  FileJson, X, RefreshCw, ZoomIn, ZoomOut, Pencil, Trash2,
} from "lucide-react";
import { cancelExecution, createModule, createModulePage, createWorkflow, deleteModule, deleteModulePage, deleteWorkflow, listModulePages, listNotifications, loadRunInspector, loadRunsPage, loadStudioSnapshot, markNotificationRead, normalizeRunStatus, publishWorkflow, replayWorkflow, runAgent, searchMemory, type StudioModulePage, type StudioNotification, type StudioRun, type StudioSnapshot, updateBug, updateModule, updateModulePage, updateWorkflow, validateWorkflow } from "./api/studio";
import { useChatStore } from "./stores/chat";
import { useSettingsStore } from "./stores/settings";
import { useProjectStore } from "./stores/project";
import ProjectSelector from "./components/ProjectSelector";
import OnboardingWizardView from "./views/cross-cutting/OnboardingWizardView";
import { useTranslation } from "react-i18next";

// ─── Types ───────────────────────────────────────────────────────────────────
type View =
  | "dashboard" | "workflow" | "execution" | "kanban" | "inspector"
  | "reports"   | "gaps"     | "memory"    | "knowledge" | "graph"
  | "artifacts" | "chat"     | "observability" | "history"
  | "settings"  | "agent" | "onboarding";

type AgentStatus = "idle" | "running" | "success" | "failed" | "warning";

interface AgentData {
  id: string; name: string; type: string; status: AgentStatus;
  lastRun: string; successRate: number; totalRuns: number;
  model: string; tools: string[]; description: string; memoryNodes: number;
}

interface LogEntry { ts: string; level: string; msg: string; ctx: string }

// ─── Data ─────────────────────────────────────────────────────────────────────
const KANBAN_PHASES = ["Project Init","Requirements","Planning","Design","Development","Testing","Integration","Review","Knowledge"];
const PHASE_KEYS: Record<string, string> = {
  "Project Init": "projectInit", Requirements: "requirements", Planning: "planning", Design: "design",
  Development: "development", Testing: "testing", Integration: "integration", Review: "review", Knowledge: "knowledge",
};

const KANBAN_MODULES = [
  { id: 1,  name: "Authentication",  pages: 12, artifacts: 8,  phase: "Testing",      status: "running" },
  { id: 2,  name: "User Management", pages: 8,  artifacts: 3,  phase: "Requirements", status: "idle" },
  { id: 3,  name: "Dashboard UI",    pages: 6,  artifacts: 5,  phase: "Development",  status: "success" },
  { id: 4,  name: "API Gateway",     pages: 24, artifacts: 14, phase: "Testing",      status: "running" },
  { id: 5,  name: "Payment Flow",    pages: 5,  artifacts: 2,  phase: "Planning",     status: "idle" },
  { id: 6,  name: "Settings",        pages: 4,  artifacts: 1,  phase: "Design",       status: "idle" },
  { id: 7,  name: "Notifications",   pages: 3,  artifacts: 0,  phase: "Project Init", status: "idle" },
  { id: 8,  name: "Reporting",       pages: 15, artifacts: 6,  phase: "Integration",  status: "success" },
  { id: 9,  name: "File Manager",    pages: 7,  artifacts: 4,  phase: "Review",       status: "idle" },
  { id: 10, name: "Search",          pages: 5,  artifacts: 2,  phase: "Requirements", status: "idle" },
];

const GAPS = [
  { id: 1, severity: "high",   type: "Missing Tests",           title: "Payment Flow",       module: "payment",    desc: "No test cases defined for payment processing workflow. 5 pages uncovered." },
  { id: 2, severity: "medium", type: "Missing Types",           title: "Session Expiry",     module: "auth",       desc: "Edge cases for token expiry not covered. Only happy path tested." },
  { id: 3, severity: "medium", type: "Insufficient Coverage",   title: "API Rate Limiting",  module: "api-gateway",desc: "Rate limiting logic has only 40% coverage. Error paths untested." },
  { id: 4, severity: "low",    type: "Untested Components",     title: "File Upload",        module: "file-manager",desc: "File upload component has 0% test coverage across all test types." },
  { id: 5, severity: "low",    type: "Flaky",                   title: "Search Debounce",    module: "search",     desc: "Test result varies based on timing. Intermittent failures observed." },
  { id: 6, severity: "medium", type: "Missing Types",           title: "Error Boundaries",   module: "dashboard",  desc: "React error boundary components not tested under failure conditions." },
];

const ARTIFACTS_DATA = [
  { name: "test-report.md",        type: "markdown", size: "12 KB",  module: "authentication",  age: "2m" },
  { name: "dashboard-baseline.png",type: "image",    size: "847 KB", module: "dashboard-ui",    age: "14m" },
  { name: "coverage.json",         type: "json",     size: "34 KB",  module: "authentication",  age: "14m" },
  { name: "auth-spec.ts",          type: "code",     size: "8.2 KB", module: "authentication",  age: "1h" },
  { name: "api-contracts.yaml",    type: "yaml",     size: "22 KB",  module: "api-gateway",     age: "1h" },
  { name: "ui-components.test.ts", type: "code",     size: "15 KB",  module: "dashboard-ui",    age: "2h" },

  { name: "payment-flow.md",       type: "markdown", size: "6 KB",   module: "payment",         age: "3h" },
  { name: "perf-metrics.json",     type: "json",     size: "18 KB",  module: "api-gateway",     age: "1d" },
  { name: "error-report.pdf",      type: "pdf",      size: "2.1 MB", module: "api-gateway",     age: "1d" },
];

const CHAT_MESSAGES = [
  { id: 1, role: "user", content: "What is the current test coverage for the auth module?" },
  { id: 2, role: "assistant", content: "The auth module has **87.3% test coverage** with 12 passing tests and 1 warning (slow API response on user creation).\n\nKey metrics:\n- Login flow: 100% covered\n- Token management: 94% covered\n- Session handling: 78% covered\n\nI recommend adding tests for session expiry edge cases.", tools: ["knowledge_search", "metrics_query"] },
  { id: 3, role: "user", content: "What are the highest risk areas right now?" },
  { id: 4, role: "assistant", content: "Top 3 risk areas identified:\n\n1. **Payment Flow** — No tests defined, 5 pages uncovered (HIGH)\n2. **Session Expiry** — Partial coverage, edge cases missing (MEDIUM)\n3. **API Rate Limiting** — Only happy path tested (MEDIUM)\n\nWould you like me to generate test cases for any of these?", tools: ["gap_analysis", "risk_scoring"] },
];

// ─── Config Maps ─────────────────────────────────────────────────────────────
const STATUS_CFG: Record<string, { dot: string; label: string; text: string; bg: string; border: string }> = {
  idle:    { dot: "bg-slate-500",   label: "Idle",    text: "text-slate-400",   bg: "bg-slate-500/10",   border: "border-slate-500/20" },
  running: { dot: "bg-cyan-400",    label: "Running", text: "text-cyan-400",    bg: "bg-cyan-400/10",    border: "border-cyan-400/25" },
  success: { dot: "bg-emerald-400", label: "Success", text: "text-emerald-400", bg: "bg-emerald-400/10", border: "border-emerald-400/25" },
  published: { dot: "bg-emerald-400", label: "Published", text: "text-emerald-400", bg: "bg-emerald-400/10", border: "border-emerald-400/25" },
  failed:  { dot: "bg-red-400",     label: "Failed",  text: "text-red-400",     bg: "bg-red-400/10",     border: "border-red-400/25" },
  warning: { dot: "bg-amber-400",   label: "Warning", text: "text-amber-400",   bg: "bg-amber-400/10",   border: "border-amber-400/25" },
};

const LOG_CFG: Record<string, { color: string; label: string }> = {
  info:    { color: "text-blue-400",    label: "INFO " },
  debug:   { color: "text-slate-500",   label: "DEBUG" },
  success: { color: "text-emerald-400", label: " OK  " },
  warning: { color: "text-amber-400",   label: "WARN " },
  error:   { color: "text-red-400",     label: "ERROR" },
};

const MEM_CFG: Record<string, { color: string; bg: string; border: string; label: string }> = {
  episodic:   { color: "text-violet-400", bg: "bg-violet-400/8",  border: "border-violet-400/20", label: "Episodic" },
  semantic:   { color: "text-sky-400",    bg: "bg-sky-400/8",     border: "border-sky-400/20",    label: "Semantic" },
  procedural: { color: "text-amber-400",  bg: "bg-amber-400/8",   border: "border-amber-400/20",  label: "Procedural" },
};

const SEV_CFG: Record<string, { text: string; bg: string; border: string; label: string }> = {
  high:   { text: "text-red-400",   bg: "bg-red-400/10",   border: "border-red-400/20",   label: "HIGH" },
  medium: { text: "text-amber-400", bg: "bg-amber-400/10", border: "border-amber-400/20", label: "MED" },
  low:    { text: "text-slate-400", bg: "bg-slate-500/10", border: "border-slate-500/20", label: "LOW" },
};

// ─── Workflow SVG Graph ───────────────────────────────────────────────────────
function WorkflowGraph({ workflow, selectedNode, onSelectNode }: { workflow?: Record<string, any>; selectedNode: string|null; onSelectNode: (id: string) => void }) {
  const { t } = useTranslation();
  const rawNodes = Array.isArray(workflow?.graph?.nodes) ? workflow.graph.nodes : [];
  const rawEdges = Array.isArray(workflow?.graph?.edges) ? workflow.graph.edges : [];
  if (!rawNodes.length) {
    return <div className="flex h-full w-full items-center justify-center rounded-lg border border-dashed border-border text-xs text-muted-foreground">{t("studio.common.noData")}</div>;
  }
  type GraphNode = { id: string; cx: number; cy: number; label: string; sub: string; status: "completed" | "running" | "pending" | "failed" };
  const nodes: GraphNode[] = rawNodes.map((raw: any, index: number) => ({
    id: String(raw.id ?? raw.key ?? index),
    cx: 100 + (index % 5) * 180,
    cy: 100 + Math.floor(index / 5) * 110,
    label: String(raw.label ?? raw.name ?? raw.type ?? raw.id ?? `node-${index + 1}`),
    sub: String(raw.type ?? raw.agent ?? "workflow node"),
    status: (normalizeRunStatus(raw.status) === "success" ? "completed" : normalizeRunStatus(raw.status) === "running" ? "running" : normalizeRunStatus(raw.status) === "failed" ? "failed" : "pending") as GraphNode["status"],
  }));
  const nodeById = new Map(nodes.map(node => [node.id, node]));
  const edges = rawEdges.map((raw: any, index: number) => {
    const source = nodeById.get(String(raw.source ?? raw.from ?? ""));
    const target = nodeById.get(String(raw.target ?? raw.to ?? ""));
    if (!source || !target) return null;
    return { d: `M ${source.cx + 75},${source.cy} L ${target.cx - 75},${target.cy}`, status: "pending" as const, key: index };
  }).filter(Boolean) as Array<{ d: string; status: "pending"; key: number }>;
  const W = 150, H = 40;
  const nodeColors = {
    completed: { fill: "rgba(52,211,153,0.07)", stroke: "#34d399", text: "#d8e6f7", dot: "#34d399", sub: "#34d399" },
    running:   { fill: "rgba(34,211,238,0.09)", stroke: "#22d3ee", text: "#d8e6f7", dot: "#22d3ee", sub: "#22d3ee" },
    pending:   { fill: "rgba(7,16,31,0.7)",     stroke: "rgba(50,90,180,0.22)", text: "#4e6a92", dot: "#253a5e", sub: "#2d4370" },
    failed:    { fill: "rgba(239,68,68,0.08)",  stroke: "#ef4444", text: "#d8e6f7", dot: "#ef4444", sub: "#ef4444" },
  };
  const edgeColors = {
    completed: { stroke: "#34d399", marker: "url(#arr-comp)" },
    active:    { stroke: "#22d3ee", marker: "url(#arr-act)" },
    pending:   { stroke: "rgba(50,90,180,0.25)", marker: "url(#arr-pend)" },
  };
  return (
    <svg viewBox="0 0 920 320" className="w-full h-full" style={{ fontFamily: "Inter, sans-serif" }}>
      <defs>
        <style>{`.ef{stroke-dasharray:8 4;animation:df .9s linear infinite}.np{animation:np 2s ease-in-out infinite}@keyframes df{to{stroke-dashoffset:-12}}@keyframes np{0%,100%{opacity:.2}50%{opacity:.55}}`}</style>
        {(["comp","act","pend"] as const).map((t) => {
          const c = { comp:"#34d399", act:"#22d3ee", pend:"rgba(50,90,180,0.3)" }[t];
          return <marker key={t} id={`arr-${t}`} markerWidth="7" markerHeight="7" refX="5" refY="3.5" orient="auto"><path d="M0,1 L5,3.5 L0,6 Z" fill={c}/></marker>;
        })}
      </defs>
      {edges.map((e) => {
        const ec = edgeColors[e.status];
        return <path key={e.key} d={e.d} fill="none" stroke={ec.stroke} strokeWidth="1.5" markerEnd={ec.marker}/>;
      })}
      {nodes.map((n) => {
        const nc = nodeColors[n.status];
        const x = n.cx - W/2, y = n.cy - H/2;
        const isSel = selectedNode === n.id;
        return (
          <g key={n.id} onClick={() => onSelectNode(n.id)} style={{ cursor:"pointer" }}>
            {isSel && <rect x={x-3} y={y-3} width={W+6} height={H+6} rx={9} fill="none" stroke="#4a7cf7" strokeWidth="1.5" opacity=".7"/>}
            {n.status==="running" && <rect x={x-2} y={y-2} width={W+4} height={H+4} rx={8} fill="none" stroke={nc.stroke} strokeWidth="1" className="np"/>}
            <rect x={x} y={y} width={W} height={H} rx={6} fill={nc.fill} stroke={nc.stroke} strokeWidth={isSel?"1.5":"1"}/>
            <text x={n.cx} y={n.cy-4} textAnchor="middle" fontSize="11.5" fill={nc.text} fontWeight="500">{n.label}</text>
            <text x={n.cx} y={n.cy+10} textAnchor="middle" fontSize="9.5" fill={nc.sub} opacity=".85">{n.sub}</text>
            <circle cx={x+W-9} cy={y+8} r="3.5" fill={nc.dot}/>
          </g>
        );
      })}
    </svg>
  );
}

// ─── Shared Components ────────────────────────────────────────────────────────
function StatusBadge({ status }: { status: string }) {
  const cfg = STATUS_CFG[status] ?? STATUS_CFG.idle;
  const { t } = useTranslation();
  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-medium ${cfg.bg} ${cfg.text} border ${cfg.border}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot} ${status==="running"?"animate-pulse":""}`}/>
      {t(`studio.status.${status}`, cfg.label)}
    </span>
  );
}

function StatCard({ icon: Icon, label, value, sub, accent }: { icon: React.ElementType; label: string; value: string; sub?: string; accent?: string }) {
  return (
    <div className="bg-card border border-border rounded-lg p-4 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <span className="text-xs text-muted-foreground font-medium uppercase tracking-wider">{label}</span>
        <Icon size={14} className={accent ?? "text-muted-foreground"}/>
      </div>
      <div>
        <div className={`text-2xl font-semibold tracking-tight ${accent ?? "text-foreground"}`}>{value}</div>
        {sub && <div className="text-xs text-muted-foreground mt-0.5">{sub}</div>}
      </div>
    </div>
  );
}

function AgentCard({ agent, onClick }: { agent: AgentData; onClick: () => void }) {
  const { t } = useTranslation();
  const description = agent.description === 'Registered by the backend agent registry.'
    ? t('studio.dashboard.registeredByBackend')
    : agent.description;
  return (
    <button onClick={onClick} className="bg-card border border-border rounded-lg p-4 text-left hover:border-primary/30 transition-all group w-full">
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="flex items-center gap-1.5 mb-1">

            <Bot size={11} className="text-muted-foreground"/><span className="text-xs text-muted-foreground">{t('studio.dashboard.registeredAgent')}</span>
          </div>
          <div className="text-sm font-semibold text-foreground">{agent.name}</div>
        </div>
        <StatusBadge status={agent.status}/>
      </div>
      <p className="text-xs text-muted-foreground leading-relaxed line-clamp-2 mb-3">{description || t('studio.dashboard.registeredByBackend')}</p>
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1"><CheckCircle2 size={11} className="text-emerald-500"/>{agent.successRate}%</span>
          <span className="flex items-center gap-1"><Activity size={11}/>{agent.totalRuns.toLocaleString()} {t('studio.dashboard.runs')}</span>
        </div>
        <span className="text-muted-foreground/60">{agent.lastRun}</span>
      </div>
      <div className="mt-3 pt-3 border-t border-border flex items-center gap-1 flex-wrap">
        {agent.tools.slice(0,3).map((t) => <span key={t} className="px-1.5 py-0.5 bg-muted rounded text-xs text-muted-foreground font-mono">{t}</span>)}
        {agent.tools.length>3 && <span className="text-xs text-muted-foreground">+{agent.tools.length-3}</span>}
      </div>
    </button>
  );
}

function LogStream({ entries, filter }: { entries: LogEntry[]; filter: string }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => { if (ref.current) ref.current.scrollTop = ref.current.scrollHeight; }, []);
  const filtered = filter==="all" ? entries : entries.filter((l) => l.level===filter);
  return (
    <div ref={ref} className="flex-1 overflow-y-auto p-3 space-y-0" style={{ scrollbarWidth:"none" }}>
      {filtered.map((e, i) => {
        const lc = LOG_CFG[e.level] ?? LOG_CFG.info;
        return (
          <div key={i} className="flex gap-2 py-0.5 hover:bg-white/2 rounded px-1 transition-colors">
            <span className="text-xs font-mono text-muted-foreground/50 flex-shrink-0 w-[88px]">{e.ts}</span>
            <span className={`text-xs font-mono flex-shrink-0 w-11 ${lc.color}`}>{lc.label}</span>
            <span className="text-xs font-mono text-sky-400/70 flex-shrink-0 w-[100px] truncate">{e.ctx}</span>
            <span className="text-xs font-mono text-foreground/75 flex-1">{e.msg}</span>
          </div>
        );
      })}
    </div>
  );
}

// ─── SOP Phase Stepper ───────────────────────────────────────────────────────
const SOP_PHASES = [
  { id:"init",   label:"Project Init",  status:"success" },
  { id:"req",    label:"Requirements",  status:"success" },
  { id:"plan",   label:"Planning",      status:"success" },
  { id:"design", label:"Design",        status:"success" },
  { id:"dev",    label:"Development",   status:"success" },
  { id:"test",   label:"Testing",       status:"running" },
  { id:"integ",  label:"Integration",   status:"idle" },
  { id:"review", label:"Review",        status:"idle" },
  { id:"know",   label:"Knowledge",     status:"idle" },
];

function SOPStepper({ snapshot }: { snapshot: StudioSnapshot | null }) {
  const { t } = useTranslation();
  const modules = snapshot?.sopStatus?.modules && typeof snapshot.sopStatus.modules === "object" ? Object.values(snapshot.sopStatus.modules) as Array<Record<string, any>> : [];
  const phaseStatus = modules[0]?.phase_status ?? {};
  const phases = SOP_PHASES.map((phase) => ({
    ...phase,
    status: phaseStatus[phase.label] === true || phaseStatus[phase.label] === "completed" ? "success" : phaseStatus[phase.label] === "running" ? "running" : "idle",
  }));
  return (
    <div className="flex items-center gap-0 overflow-x-auto" style={{ scrollbarWidth:"none" }}>
      {phases.map((p, i) => {
        const isComplete = p.status==="success";
        const isRunning = p.status==="running";
        const isPending = p.status==="idle";
        return (
          <div key={p.id} className="flex items-center flex-shrink-0">
            <div className="flex flex-col items-center gap-1.5 px-2">
              <div className={`w-7 h-7 rounded-full flex items-center justify-center border ${
                isComplete ? "bg-emerald-400/15 border-emerald-400/40" :
                isRunning  ? "bg-cyan-400/15 border-cyan-400/40 animate-pulse" :
                             "bg-muted border-border"}`}>
                {isComplete ? <CheckCircle2 size={13} className="text-emerald-400"/> :
                 isRunning  ? <Circle size={9} className="text-cyan-400 fill-cyan-400"/> :
                              <Circle size={9} className="text-muted-foreground/30"/>}
              </div>
              <span className={`text-[9px] font-medium whitespace-nowrap ${
                isComplete ? "text-emerald-400/80" : isRunning ? "text-cyan-400" : "text-muted-foreground/40"}`}>
                 {t(`sop.phase.${p.label}`, p.label)}
              </span>
            </div>
            {i < phases.length-1 && (
              <div className={`h-px w-6 flex-shrink-0 mb-4 ${isComplete ? "bg-emerald-400/40" : "bg-border"}`}/>
            )}
          </div>
        );
      })}
    </div>
  );
}

function useStudioSnapshot(activeProjectId: string, refreshToken = 0) {
  const [snapshot, setSnapshot] = useState<StudioSnapshot | null>(null);

  useEffect(() => {
    let mounted = true;
    const refresh = () => loadStudioSnapshot(activeProjectId).then(next => { if (mounted) setSnapshot(next); });
    refresh();
    const timer = window.setInterval(refresh, 30_000);
    return () => { mounted = false; window.clearInterval(timer); };
  }, [activeProjectId, refreshToken]);

  return snapshot;
}

// ─── Dashboard View ───────────────────────────────────────────────────────────
function DashboardView({ onSelectAgent, onViewHistory, snapshot }: { onSelectAgent: (a: AgentData) => void; onViewHistory: () => void; snapshot: StudioSnapshot | null }) {
  const { t } = useTranslation();
  const liveAgents: AgentData[] = snapshot?.agents ? Object.entries(snapshot.agents).map(([id, skills]) => ({
    id,
    name: id,
    type: "Registered Agent",
    status: "idle",
    lastRun: "—",
    successRate: 0,
    totalRuns: 0,
    model: "configured by backend",
    tools: skills,
    description: "Registered by the backend agent registry.",
    memoryNodes: 0,
  })) : [];
  const liveRuns = snapshot?.runs?.length ? snapshot.runs.slice(0, 5).map(run => ({
    id: run.run_id,
    status: normalizeRunStatus(run.status),
    workflow: String(run.workflow || run.module || 'workflow'),
    started: run.created_at ? new Date(run.created_at).toLocaleString() : 'recently',
    duration: run.completed_at && run.created_at ? `${Math.max(0, (new Date(run.completed_at).getTime() - new Date(run.created_at).getTime()) / 1000).toFixed(1)}s` : 'running',
    passed: Number((run as any).passed ?? (run as any).tests_passed ?? 0),
    total: Number((run as any).total ?? (run as any).tests_total ?? 0),
  })) : [];
  const kpi = snapshot?.productKpi?.this_week;
  const liveAgentCount = liveAgents.length;
  const successRate = typeof kpi?.success_rate === 'number' && Number(kpi.runs ?? 0) > 0 ? `${(kpi.success_rate * 100).toFixed(1)}%` : '—';
  const workflowsToday = typeof kpi?.runs === 'number' ? String(kpi.runs) : '—';
  return (
    <div className="p-6 space-y-5 max-w-[1400px] overflow-y-auto h-full" style={{ scrollbarWidth:"none" }}>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={Bot}          label={t("studio.dashboard.registeredAgents")} value={String(liveAgentCount)} sub={t("studio.dashboard.agentRegistrySub")} accent="text-cyan-400"/>
        <StatCard icon={GitBranch}    label={t("studio.dashboard.workflowsToday")} value={workflowsToday}    sub={t("studio.dashboard.kpiSub")}  accent="text-primary"/>
        <StatCard icon={CheckCircle2} label={t("studio.dashboard.successRate")}    value={successRate} sub={t("studio.dashboard.last7Days")}         accent="text-emerald-400"/>
        <StatCard icon={Brain}        label={t("studio.dashboard.memoryCollections")} value={String(Object.keys(snapshot?.memory?.collections ?? {}).length)} sub={t("studio.dashboard.memoryStore")} accent="text-violet-400"/>
      </div>
      {liveRuns.some((run) => run.status === "running") && <div className="bg-cyan-400/5 border border-cyan-400/20 rounded-lg px-5 py-3 flex items-center gap-4">
        <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"/><span className="text-sm font-medium text-cyan-400">{t("studio.dashboard.executionInProgress")}</span>
        <span className="text-xs text-muted-foreground font-mono">{liveRuns.find((run) => run.status === "running")?.id}</span>
      </div>}
      <div className="grid grid-cols-1 xl:grid-cols-[1fr_300px] gap-5">
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-foreground">{t("studio.dashboard.agentRegistry")}</h2>
             <span className="text-xs text-muted-foreground">{liveAgents.length} {t("studio.dashboard.agents")}</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {liveAgents.map((a) => <AgentCard key={a.id} agent={a} onClick={() => onSelectAgent(a)}/>)}
          </div>
        </div>
        <div className="space-y-4">
          <div>
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-semibold text-foreground">{t("studio.dashboard.recentRuns")}</h2>
              <button onClick={onViewHistory} className="text-xs text-muted-foreground hover:text-foreground transition-colors">{t("studio.common.viewAll")}</button>
            </div>
             <div className="bg-card border border-border rounded-lg overflow-hidden">
               {liveRuns.map((r, i) => {
                const cfg = STATUS_CFG[r.status] ?? STATUS_CFG.idle;
                return (
                   <div key={r.id} className={`flex items-center gap-3 px-4 py-3 hover:bg-white/4 transition-colors ${i<liveRuns.length-1?"border-b border-border":""}`}>
                    <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${cfg.dot}`}/>
                    <div className="flex-1 min-w-0">
                      <div className="text-xs font-mono text-foreground/70">{r.id}</div>
                      <div className="text-xs text-muted-foreground mt-0.5">{r.started} · {r.duration}</div>
                    </div>
                    <div className={`text-xs font-medium ${cfg.text}`}>{r.passed}/{r.total}</div>
                   </div>
                 );
               })}
               {liveRuns.length === 0 && <div className="px-4 py-6 text-xs text-muted-foreground">{t("studio.common.noData")}</div>}
             </div>
          </div>
          <div>

            <h3 className="text-sm font-semibold text-foreground mb-3">{t("studio.dashboard.systemHealth")}</h3>
            <div className="bg-card border border-border rounded-lg divide-y divide-border">
               {[{label:"API Gateway",status:snapshot?.health?.status ?? "unknown",dot:snapshot?.health?.status === "healthy" ? "bg-emerald-400" : "bg-amber-400"},{label:t("studio.dashboard.memory"),status:snapshot?.memory?.available ? "available" : "unavailable",dot:snapshot?.memory?.available ? "bg-cyan-400" : "bg-slate-500"},{label:t("studio.dashboard.taskQueue"),status:`${snapshot?.observability?.queue?.queued ?? 0} ${t("studio.observability.queued")}`,dot:"bg-amber-400"},{label:t("studio.dashboard.modelProviders"),status:`${snapshot?.providers?.length ?? 0} ${t("studio.dashboard.configured")}`,dot:"bg-emerald-400"}].map((r) => (
                <div key={r.label} className="flex items-center justify-between px-4 py-2.5">
                  <div className="flex items-center gap-2"><span className={`w-1.5 h-1.5 rounded-full ${r.dot}`}/><span className="text-xs text-muted-foreground">{r.label}</span></div>
                  <span className="text-xs font-mono text-foreground/70">{String(r.status)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Workflow Builder View ────────────────────────────────────────────────────
function WorkflowBuilderView({ snapshot, onSaved }: { snapshot: StudioSnapshot | null; onSaved?: () => void }) {
  const { t } = useTranslation();
  const [selNode, setSelNode] = useState<string|null>("browser");
  const [selectedWorkflowId, setSelectedWorkflowId] = useState<string|null>(null);
  const [wfName, setWfName] = useState("");
  const [wfDesc, setWfDesc] = useState("");
  const [saveState, setSaveState] = useState("");
  const existingWFs = snapshot?.workflows?.map(workflow => ({
    id: String(workflow.workflow_id ?? workflow.id ?? ""),
    name: String(workflow.name || workflow.workflow_id || 'workflow'),
    description: String(workflow.description ?? ""),
    status: String(workflow.status || 'idle'),
    updated: workflow.updated_at ? new Date(String(workflow.updated_at)).toLocaleString() : 'recently',
    nodes: Array.isArray((workflow as any).graph?.nodes) ? (workflow as any).graph.nodes.length : 0,
  })) ?? [];
  const activeWorkflow = snapshot?.workflows?.find((workflow) => String(workflow.workflow_id ?? workflow.id ?? "") === selectedWorkflowId) ?? snapshot?.workflows?.[0];
  const activeWorkflowId = activeWorkflow ? String(activeWorkflow.workflow_id ?? activeWorkflow.id ?? "") : "";

  function selectWorkflow(workflow: (typeof existingWFs)[number]) {
    setSelectedWorkflowId(workflow.id);
    setWfName(workflow.name);
    setWfDesc(workflow.description);
    setSaveState("");
  }

  async function handleSaveWorkflow(publish = false) {
    if (!wfName.trim()) return;
    setSaveState("saving");
    try {
      let workflowId = selectedWorkflowId;
      if (workflowId) {
        await updateWorkflow(workflowId, { name: wfName.trim(), description: wfDesc.trim(), status: publish ? "published" : "draft" });
      } else {
        const created = await createWorkflow(wfName.trim(), wfDesc.trim());
        workflowId = created.workflow_id ? String(created.workflow_id) : null;
      }
      if (publish && workflowId) await publishWorkflow(workflowId);
      setSaveState("saved");
      if (workflowId) setSelectedWorkflowId(workflowId);
      onSaved?.();
    }
    catch { setSaveState("failed"); }
  }

  async function handleDeleteWorkflow() {
    if (!selectedWorkflowId) return;
    setSaveState("saving");
    try {
      await deleteWorkflow(selectedWorkflowId);
      setSelectedWorkflowId(null); setWfName(""); setWfDesc(""); setSaveState("saved"); onSaved?.();
    } catch { setSaveState("failed"); }
  }

  async function handleInspectWorkflow() {
    if (!activeWorkflowId) return;
    setSaveState("saving");
    try {
      const result = await validateWorkflow(activeWorkflowId);
       setSaveState(result.valid === false ? "invalid" : "saved");
    } catch { setSaveState("failed"); }
  }

  async function handleReplayWorkflow() {
    if (!activeWorkflowId) return;
    setSaveState("saving");
    try {
      await replayWorkflow(activeWorkflowId);
      setSaveState("saved"); onSaved?.();
    } catch { setSaveState("failed"); }
  }
  return (
    <div className="flex h-full overflow-hidden">
      <div className="w-72 border-r border-border flex flex-col flex-shrink-0">
        <div className="p-4 border-b border-border">
          <div className="text-sm font-semibold text-foreground mb-3">{t("studio.workflow.newWorkflow")}</div>
          <div className="space-y-3">
            <div>
              <label className="text-xs text-muted-foreground mb-1 block">{t("studio.workflow.name")}</label>
              <input value={wfName} onChange={(e) => setWfName(e.target.value)} placeholder={t("studio.workflow.workflowName")} className="w-full px-3 py-2 bg-muted border border-border rounded text-xs text-foreground placeholder:text-muted-foreground/50 outline-none focus:border-primary/50 font-mono"/>
            </div>
            <div>
              <label className="text-xs text-muted-foreground mb-1 block">{t("studio.workflow.description")}</label>
              <textarea value={wfDesc} onChange={(e) => setWfDesc(e.target.value)} placeholder={t("studio.workflow.describe")} rows={3} className="w-full px-3 py-2 bg-muted border border-border rounded text-xs text-foreground placeholder:text-muted-foreground/50 outline-none focus:border-primary/50 resize-none"/>
            </div>
            <div>
              <label className="text-xs text-muted-foreground mb-2 block">{t("studio.workflow.agents")}</label>
              <div className="flex flex-wrap gap-1.5">
                 {Object.keys(snapshot?.agents ?? {}).slice(0,4).map((agentId) => (
                   <span key={agentId} className="px-2 py-0.5 bg-primary/10 border border-primary/25 rounded text-xs text-primary font-mono cursor-pointer hover:bg-primary/20 transition-colors">{agentId}</span>
                ))}
              </div>
            </div>
            <div className="flex gap-2 pt-1">
              <button onClick={() => void handleSaveWorkflow(false)} className="flex-1 py-2 bg-muted border border-border rounded text-xs text-muted-foreground hover:text-foreground transition-colors">{saveState === "saving" ? t("studio.common.loading") : t("studio.common.saveDraft")}</button>
              <button onClick={() => void handleSaveWorkflow(true)} className="flex-1 py-2 bg-primary/10 border border-primary/30 rounded text-xs text-primary hover:bg-primary/20 transition-colors">{t("studio.common.publish")}</button>
              {selectedWorkflowId && <button onClick={() => void handleDeleteWorkflow()} className="w-full py-2 bg-red-400/10 border border-red-400/25 rounded text-xs text-red-400 hover:bg-red-400/15 transition-colors">{t("common.delete")}</button>}
               {saveState && <span role="status" className="text-xs text-muted-foreground">{saveState === "saved" ? t("studio.dashboard.saved") : saveState === "invalid" ? t("studio.dashboard.validationFailed", "Validation failed") : saveState === "failed" ? t("studio.dashboard.saveFailed") : ""}</span>}
            </div>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto p-4" style={{ scrollbarWidth:"none" }}>
          <div className="text-xs text-muted-foreground mb-3 font-medium uppercase tracking-wider">{t("studio.workflow.existingWorkflows")}</div>
          <div className="space-y-2">
            {existingWFs.map((w) => {
              const cfg = STATUS_CFG[w.status] ?? STATUS_CFG.idle;
              return (
                <button type="button" key={w.id || w.name} onClick={() => selectWorkflow(w)} className={`w-full text-left bg-card border rounded-lg p-3 hover:border-border/80 transition-colors ${selectedWorkflowId === w.id ? "border-primary/50" : "border-border"}`}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-mono text-foreground/80 truncate">{w.name}</span>
                    <span className={`text-xs font-medium ${cfg.text}`}>{cfg.label}</span>
                  </div>
                  <div className="flex items-center gap-3 text-xs text-muted-foreground">
                    <span>{w.nodes} {t("studio.workflow.nodes")}</span><span>{w.updated}</span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      </div>
      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="flex items-center gap-3 px-5 py-3 border-b border-border flex-shrink-0">
           <span className="text-xs font-mono text-muted-foreground">{String(activeWorkflow?.workflow_id ?? activeWorkflow?.id ?? t("studio.common.noData"))}</span>
           <StatusBadge status={String(activeWorkflow?.status ?? "idle")}/>
          <div className="ml-auto flex gap-2">
            <button onClick={() => void handleReplayWorkflow()} disabled={!activeWorkflowId || saveState === "saving"} className="flex items-center gap-1.5 px-3 py-1.5 bg-muted rounded text-xs text-muted-foreground hover:text-foreground transition-colors disabled:opacity-40"><RotateCcw size={11}/> {t("studio.common.replay")}</button>
            <button onClick={() => void handleInspectWorkflow()} disabled={!activeWorkflowId || saveState === "saving"} className="flex items-center gap-1.5 px-3 py-1.5 bg-primary/10 border border-primary/25 rounded text-xs text-primary hover:bg-primary/15 transition-colors disabled:opacity-40"><Eye size={11}/> {t("studio.common.inspect")}</button>
          </div>
        </div>
        <div className="flex-1 flex items-center justify-center p-6">
           <WorkflowGraph workflow={activeWorkflow} selectedNode={selNode} onSelectNode={setSelNode}/>
        </div>
      </div>
    </div>
  );
}

// ─── Execution Center View ────────────────────────────────────────────────────
function ExecutionView({ snapshot }: { snapshot: StudioSnapshot | null }) {
  const { t } = useTranslation();
  const [logFilter, setLogFilter] = useState("all");
  const [selNode, setSelNode] = useState<string|null>(null);
  const runId = snapshot?.runs?.[0]?.run_id;
  const [inspector, setInspector] = useState<Record<string, any> | null>(null);
  useEffect(() => {
    if (!runId) { setInspector(null); return; }
    let mounted = true;
    loadRunInspector(runId).then((data) => { if (mounted) setInspector(data); }).catch(() => { if (mounted) setInspector(null); });
    return () => { mounted = false; };
  }, [runId]);
  const header = inspector?.header ?? {};
  const executionLogs = (inspector?.logs ?? []).map((entry: any) => ({
    ts: String(entry.timestamp ?? entry.ts ?? "—"),
    level: String(entry.level ?? entry.severity ?? "info"),
    msg: String(entry.message ?? entry.msg ?? entry.data ?? ""),
    ctx: String(entry.agent ?? entry.ctx ?? "backend"),
  })) as LogEntry[];
  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Control bar */}
      <div className="flex items-center gap-4 px-5 py-3 border-b border-border flex-shrink-0">
        <div className="flex items-center gap-2 bg-muted rounded px-3 py-1.5">
           <span className="text-xs text-muted-foreground">{t("studio.workflow.module")}:</span>
           <span className="text-xs font-medium text-foreground font-mono">{String(header.module ?? snapshot?.runs?.[0]?.module ?? t("studio.common.noData"))}</span>
          <ChevronDown size={11} className="text-muted-foreground"/>
        </div>
        <div className="flex items-center gap-2 bg-muted rounded px-3 py-1.5">
           <span className="text-xs text-muted-foreground">{t("studio.workflow.mode")}:</span>
           <span className="text-xs font-medium text-foreground">{t("studio.workflow.fullSop")}</span>
          <ChevronDown size={11} className="text-muted-foreground"/>
        </div>
        <div className="flex items-center gap-2 ml-auto">
           <StatusBadge status={normalizeRunStatus(header.status ?? snapshot?.runs?.[0]?.status)}/>
            {header.request_id && <button onClick={() => void cancelExecution(String(header.request_id))} className="flex items-center gap-1.5 px-3 py-1.5 bg-red-400/10 border border-red-400/25 rounded text-xs text-red-400 hover:bg-red-400/15 transition-colors"><X size={11}/> {t("studio.workflow.cancel")}</button>}
        </div>
      </div>
      {/* SOP Stepper */}
      <div className="px-5 py-4 border-b border-border flex-shrink-0 bg-card/50">
        <div className="flex items-center justify-between mb-2">
           <span className="text-xs text-muted-foreground font-medium">{t("studio.workflow.sopProgress")}</span>
              <span className="text-xs font-mono text-cyan-400">{header.module ?? t("studio.workflow.noActiveRun")}</span>
        </div>
         <SOPStepper snapshot={snapshot}/>
      </div>
      {/* Main content: graph + logs */}
      <div className="flex-1 flex overflow-hidden">
        <div className="flex-1 flex flex-col overflow-hidden border-r border-border">
          <div className="px-4 py-2.5 border-b border-border flex-shrink-0">
             <span className="text-xs font-semibold text-foreground">{t("studio.workflow.liveGraph")}</span>
          </div>
          <div className="flex-1 flex items-center justify-center p-4">
             <WorkflowGraph workflow={snapshot?.workflows?.[0]} selectedNode={selNode} onSelectNode={setSelNode}/>
          </div>
        </div>
        <div className="w-[420px] flex flex-col flex-shrink-0">
          <div className="flex items-center gap-3 px-4 py-2.5 border-b border-border flex-shrink-0">
            <Terminal size={12} className="text-muted-foreground"/>
             <span className="text-xs font-semibold text-foreground">{t("studio.workflow.agentTerminal")}</span>
            <div className="ml-auto flex gap-1">
              {["all","info","warning","debug"].map((f) => (
                <button key={f} onClick={() => setLogFilter(f)} className={`px-2 py-0.5 rounded text-xs transition-colors ${logFilter===f?"bg-primary/15 text-primary":"text-muted-foreground hover:text-foreground"}`}>{f}</button>

              ))}
            </div>
          </div>
          <div className="flex-1 overflow-hidden bg-muted/30">
             <LogStream entries={executionLogs} filter={logFilter}/>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Kanban Board View ────────────────────────────────────────────────────────
function KanbanView({ snapshot, projectId, onRefresh }: { snapshot: StudioSnapshot | null; projectId: string; onRefresh?: () => void }) {
  const { t } = useTranslation();
  const [showAddModule, setShowAddModule] = useState(false);
  const [editingModule, setEditingModule] = useState<string | null>(null);
  const [moduleName, setModuleName] = useState("");
  const [actionState, setActionState] = useState("");
  const [pageManagerModule, setPageManagerModule] = useState<string | null>(null);
  const [modulePages, setModulePages] = useState<StudioModulePage[]>([]);
  const [pageEditing, setPageEditing] = useState<string | null>(null);
  const [pageName, setPageName] = useState("");
  const [pageDescription, setPageDescription] = useState("");
  const [pageUrl, setPageUrl] = useState("");
  const [pageLocators, setPageLocators] = useState("{}");
  const [pageConfig, setPageConfig] = useState("{}");
  const [pageExecution, setPageExecution] = useState("{}");
  const [pageEnabled, setPageEnabled] = useState(true);
  const [pageAction, setPageAction] = useState("");
  const kanbanModules = (snapshot?.kanban ?? []).map((item, index) => {
    const phases = Array.isArray(item.phases) ? item.phases : [];
    const current = phases.find((phase: any) => phase.status === "running") ?? phases[phases.length - 1];
    return { id:String(item.module ?? index), name:String(item.module ?? "module"), pages:Number(item.page_count ?? (Array.isArray(item.pages) ? item.pages.length : 0)), artifacts:Number(item.artifact_count ?? 0), phase:String(current?.name ?? "Project Init"), status:normalizeRunStatus(item.overall_status ?? item.status) };
  });

  useEffect(() => {
    if (!pageManagerModule) return;
    let mounted = true;
    setPageAction(t('studio.common.loading', 'Loading…'));
    void listModulePages(pageManagerModule, projectId).then((data) => {
      if (mounted) {
        setModulePages(data.pages);
        setPageAction("");
      }
    }).catch((error: unknown) => {
      if (mounted) setPageAction(error instanceof Error ? error.message : t('studio.common.requestFailed', 'Request failed'));
    });
    return () => { mounted = false; };
  }, [pageManagerModule, projectId, t]);

  const openPageManager = (module: string) => {
    setPageManagerModule(module);
    setPageEditing(null);
    setPageName("");
    setPageDescription("");
    setPageUrl("");
    setPageLocators("{}");
    setPageConfig("{}");
    setPageExecution("{}");
    setPageEnabled(true);
    setPageAction("");
  };

  const submitPage = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!pageManagerModule || !pageName.trim()) {
      setPageAction(t('studio.common.required', 'Page name is required'));
      return;
    }
    let locators: Record<string, unknown>;
    let config: Record<string, unknown>;
    let execution: Record<string, unknown>;
    try {
      const parseObject = (value: string, label: string) => {
        let parsed: unknown = {};
        if (value.trim()) {
          try {
            parsed = JSON.parse(value);
          } catch {
            throw new Error(`${label} must be valid JSON object`);
          }
        }
        if (!parsed || Array.isArray(parsed) || typeof parsed !== 'object') {
          throw new Error(`${label} must be a JSON object`);
        }
        return parsed as Record<string, unknown>;
      };
      locators = parseObject(pageLocators, 'Locators');
      config = parseObject(pageConfig, 'Page config');
      execution = parseObject(pageExecution, 'Execution plan');
    } catch (error: unknown) {
      setPageAction(error instanceof Error ? error.message : t('studio.common.invalid', 'Invalid configuration'));
      return;
    }
    setPageAction(t('studio.common.loading', pageEditing ? 'Updating…' : 'Creating…'));
    const pageConfigPayload = { url: pageUrl.trim(), locators, config, execution, enabled: pageEnabled };
    const request = pageEditing
      ? updateModulePage(pageManagerModule, pageEditing, { name: pageName.trim(), description: pageDescription, ...pageConfigPayload }, projectId)
      : createModulePage(pageManagerModule, pageName.trim(), pageDescription, projectId, pageConfigPayload);
    void request.then(() => listModulePages(pageManagerModule, projectId)).then((data) => {
      setModulePages(data.pages);
      setPageAction(t('studio.common.saved', pageEditing ? 'Updated' : 'Created'));
      setPageEditing(null);
      setPageName("");
      setPageDescription("");
      setPageUrl("");
      setPageLocators("{}");
      setPageConfig("{}");
      setPageExecution("{}");
      setPageEnabled(true);
      onRefresh?.();
    }).catch((error: unknown) => {
      setPageAction(error instanceof Error ? error.message : t('studio.common.requestFailed', 'Request failed'));
    });
  };
  return (
    <div className="h-full flex flex-col overflow-hidden">
      <div className="flex items-center gap-3 px-5 py-3 border-b border-border flex-shrink-0">
        <span className="text-sm font-semibold text-foreground">{t('studio.common.kanbanBoard')}</span>
        <span className="text-xs text-muted-foreground">— {t('studio.common.sopPhaseOverview')}</span>
        <div className="ml-auto flex items-center gap-2">
          <span className="text-xs text-muted-foreground">{kanbanModules.length} {t('studio.common.modules')}</span>
           <button data-testid="kanban-add-module" onClick={() => { setActionState(""); setEditingModule(null); setModuleName(""); setShowAddModule(true); }} className="flex items-center gap-1.5 px-3 py-1.5 bg-primary/10 border border-primary/25 rounded text-xs text-primary hover:bg-primary/15 transition-colors"><Plus size={11}/> {t('studio.common.addModule')}</button>
        </div>
      </div>
      <div className="flex-1 overflow-x-auto overflow-y-hidden" style={{ scrollbarWidth:"thin" }}>
        <div className="flex gap-3 p-4 h-full min-w-max">
           {KANBAN_PHASES.map((phase) => {
             const cards = kanbanModules.filter((m) => m.phase===phase);
            const isActive = phase==="Testing";
            return (
              <div key={phase} className={`w-48 flex flex-col rounded-lg border flex-shrink-0 ${isActive?"border-cyan-400/25 bg-cyan-400/5":"border-border bg-card/50"}`}>
                <div className="px-3 py-2.5 border-b border-border flex items-center justify-between">
                   <span className={`text-xs font-semibold ${isActive?"text-cyan-400":"text-foreground/70"}`}>{t(`studio.common.phases.${PHASE_KEYS[phase]}`, phase)}</span>
                  <span className={`text-xs px-1.5 py-0.5 rounded font-mono ${isActive?"bg-cyan-400/15 text-cyan-400":"bg-muted text-muted-foreground"}`}>{cards.length}</span>
                </div>
                <div className="flex-1 overflow-y-auto p-2 space-y-2" style={{ scrollbarWidth:"none" }}>
                  {cards.map((m) => {
                    const cfg = STATUS_CFG[m.status] ?? STATUS_CFG.idle;
                    return (
                       <div key={m.id} data-testid={`kanban-module-${m.id}`} role="button" tabIndex={0} aria-label={`Manage pages for ${m.name}`} onClick={() => openPageManager(m.name)} onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); openPageManager(m.name); } }} className={`bg-card border rounded-md p-3 cursor-pointer hover:border-primary/30 transition-colors ${cfg.border}`}>
                         <div className="flex items-center justify-between mb-2">
                           <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${cfg.dot} ${m.status==="running"?"animate-pulse":""}`}/>
                           <div className="flex items-center gap-1"><span className={`text-xs ${cfg.text}`}>{t(`studio.status.${m.status}`, cfg.label)}</span><button type="button" aria-label={`Edit ${m.name}`} onClick={(event) => { event.stopPropagation(); setEditingModule(m.name); setModuleName(m.name); setActionState(""); setShowAddModule(true); }} className="p-1 text-muted-foreground hover:text-foreground"><Pencil size={10}/></button><button type="button" aria-label={`Delete ${m.name}`} onClick={(event) => { event.stopPropagation(); if (!window.confirm(`Delete module ${m.name}?`)) return; setActionState(t('studio.common.loading', 'Deleting…')); void deleteModule(m.name, projectId).then(() => { setActionState(t('studio.common.saved', 'Deleted')); onRefresh?.(); }).catch((error: unknown) => setActionState(error instanceof Error ? error.message : t('studio.common.requestFailed', 'Request failed'))); }} className="p-1 text-muted-foreground hover:text-destructive"><Trash2 size={10}/></button></div>
                         </div>
                        <div className="text-xs font-semibold text-foreground mb-2 leading-tight">{m.name}</div>
                        <div className="flex items-center gap-2 text-xs text-muted-foreground">
                           <span>{m.pages} {t('studio.common.pages')} · {t('studio.common.manage', 'Manage')}</span>
                           <span>{m.artifacts} {t('studio.common.tabsArtifacts')}</span>
                        </div>
                      </div>
                    );
                  })}
                  {cards.length===0 && <div className="text-xs text-muted-foreground/40 text-center py-4">{t('studio.common.empty')}</div>}
                </div>
              </div>
            );
          })}
        </div>
      </div>
      {showAddModule && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/50 p-4" role="dialog" aria-modal="true" aria-label={t('studio.common.addModule')}>
          <form className="w-full max-w-sm rounded-lg border border-border bg-card p-5 shadow-xl" onSubmit={(event) => {
            event.preventDefault();
            const name = moduleName.trim();
            if (!name) { setActionState(t('studio.common.required', 'Module name is required')); return; }
            setActionState(t('studio.common.loading', editingModule ? 'Updating…' : 'Creating…'));
            const request = editingModule ? updateModule(editingModule, { name }, projectId) : createModule(name, projectId);
            void request.then(() => {
              setActionState(t('studio.common.saved', editingModule ? 'Updated' : 'Created'));
              setModuleName("");
              setEditingModule(null);
              onRefresh?.();
            }).catch((error: unknown) => {
              setActionState(error instanceof Error ? error.message : t('studio.common.requestFailed', 'Request failed'));
            });
          }}>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-foreground">{editingModule ? t('studio.common.editModule', 'Edit module') : t('studio.common.addModule')}</h2>
              <button type="button" aria-label={t('studio.common.close', 'Close')} onClick={() => setShowAddModule(false)} className="p-1 text-muted-foreground hover:text-foreground"><X size={14}/></button>
            </div>
            <label className="block text-xs text-muted-foreground mb-1.5" htmlFor="kanban-module-name">{t('studio.common.moduleName', 'Module name')}</label>
            <input id="kanban-module-name" autoFocus value={moduleName} onChange={(event) => setModuleName(event.target.value)} className="w-full rounded border border-border bg-muted px-3 py-2 text-sm text-foreground outline-none focus:border-primary" placeholder="authentication" />
            {actionState && <div role="status" className="mt-3 text-xs text-muted-foreground">{actionState}</div>}
            <div className="mt-5 flex justify-end gap-2">
              <button type="button" onClick={() => setShowAddModule(false)} className="rounded bg-muted px-3 py-1.5 text-xs text-muted-foreground hover:text-foreground">{t('studio.common.cancel', 'Cancel')}</button>
              <button type="submit" disabled={actionState.endsWith('…')} className="rounded bg-primary/15 px-3 py-1.5 text-xs text-primary hover:bg-primary/25 disabled:opacity-50">{editingModule ? t('studio.common.save', 'Save') : t('studio.common.create', 'Create')}</button>
            </div>
          </form>
        </div>
      )}
      {pageManagerModule && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/50 p-4" role="dialog" aria-modal="true" aria-label={`Manage pages for ${pageManagerModule}`}>
          <div className="w-full max-w-2xl rounded-lg border border-border bg-card p-5 shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-foreground">{t('studio.common.managePages', 'Manage pages')} · {pageManagerModule}</h2>
              <button type="button" aria-label={t('studio.common.close', 'Close')} onClick={() => setPageManagerModule(null)} className="p-1 text-muted-foreground hover:text-foreground"><X size={14}/></button>
            </div>
            <div className="max-h-48 overflow-y-auto space-y-2" data-testid="module-pages-list">
              {modulePages.length === 0 && !pageAction && <div className="text-xs text-muted-foreground">{t('studio.common.emptyPages', 'No pages configured')}</div>}
              {modulePages.map((page) => (
                <div key={page.id} data-testid={`module-page-${page.id}`} className="flex items-center gap-2 rounded border border-border/70 bg-muted/30 px-3 py-2">
                  <div className="min-w-0 flex-1"><div className="text-xs font-medium text-foreground">{page.name}</div>{page.description && <div className="text-[11px] text-muted-foreground truncate">{page.description}</div>}<div className="text-[11px] text-muted-foreground truncate">{page.url || 'No URL'} · {page.enabled === false ? 'Disabled' : 'Enabled'}</div></div>
                   <button type="button" aria-label={`Edit page ${page.name}`} onClick={() => { setPageEditing(page.id); setPageName(page.name); setPageDescription(page.description ?? ''); setPageUrl(page.url ?? ''); setPageLocators(JSON.stringify(page.locators ?? {}, null, 2)); setPageConfig(JSON.stringify(page.config ?? {}, null, 2)); setPageExecution(JSON.stringify(page.execution ?? {}, null, 2)); setPageEnabled(page.enabled !== false); setPageAction(''); }} className="p-1 text-muted-foreground hover:text-foreground"><Pencil size={11}/></button>
                  <button type="button" aria-label={`Delete page ${page.name}`} onClick={() => { if (!window.confirm(`Delete page ${page.name}?`)) return; setPageAction(t('studio.common.loading', 'Deleting…')); void deleteModulePage(pageManagerModule, page.id, projectId).then(() => listModulePages(pageManagerModule, projectId)).then((data) => { setModulePages(data.pages); setPageAction(t('studio.common.saved', 'Deleted')); onRefresh?.(); }).catch((error: unknown) => setPageAction(error instanceof Error ? error.message : t('studio.common.requestFailed', 'Request failed'))); }} className="p-1 text-muted-foreground hover:text-destructive"><Trash2 size={11}/></button>
                </div>
              ))}
            </div>
            <form className="mt-4 border-t border-border pt-4" onSubmit={submitPage}>
              <div className="text-xs font-semibold text-foreground mb-3">{pageEditing ? t('studio.common.editPage', 'Edit page') : t('studio.common.addPage', 'Add page')}</div>
              <label className="block text-xs text-muted-foreground mb-1.5" htmlFor="module-page-name">{t('studio.common.pageName', 'Page name')}</label>
              <input id="module-page-name" data-testid="module-page-name" autoFocus value={pageName} onChange={(event) => setPageName(event.target.value)} className="w-full rounded border border-border bg-muted px-3 py-2 text-sm text-foreground outline-none focus:border-primary" placeholder="product-list" />
               <label className="block text-xs text-muted-foreground mb-1.5 mt-3" htmlFor="module-page-description">{t('studio.common.pageDescription', 'Description')}</label>
               <textarea id="module-page-description" data-testid="module-page-description" value={pageDescription} onChange={(event) => setPageDescription(event.target.value)} className="w-full min-h-16 rounded border border-border bg-muted px-3 py-2 text-sm text-foreground outline-none focus:border-primary" placeholder={t('studio.common.optional', 'Optional')} />
               <label className="block text-xs text-muted-foreground mb-1.5 mt-3" htmlFor="module-page-url">Page URL</label>
               <input id="module-page-url" data-testid="module-page-url" value={pageUrl} onChange={(event) => setPageUrl(event.target.value)} className="w-full rounded border border-border bg-muted px-3 py-2 text-sm text-foreground outline-none focus:border-primary" placeholder="https://example.test/login" />
               <label className="block text-xs text-muted-foreground mb-1.5 mt-3" htmlFor="module-page-locators">Locators (JSON)</label>
               <textarea id="module-page-locators" data-testid="module-page-locators" value={pageLocators} onChange={(event) => setPageLocators(event.target.value)} className="w-full min-h-20 rounded border border-border bg-muted px-3 py-2 text-xs font-mono text-foreground outline-none focus:border-primary" placeholder={'{"username":"#username"}'} />
                <label className="block text-xs text-muted-foreground mb-1.5 mt-3" htmlFor="module-page-config">Page config (JSON)</label>
                <textarea id="module-page-config" data-testid="module-page-config" value={pageConfig} onChange={(event) => setPageConfig(event.target.value)} className="w-full min-h-20 rounded border border-border bg-muted px-3 py-2 text-xs font-mono text-foreground outline-none focus:border-primary" placeholder={'{"requires_auth":true}'} />
                <label className="block text-xs text-muted-foreground mb-1.5 mt-3" htmlFor="module-page-execution">Execution plan (JSON)</label>
                <textarea id="module-page-execution" data-testid="module-page-execution" value={pageExecution} onChange={(event) => setPageExecution(event.target.value)} className="w-full min-h-24 rounded border border-border bg-muted px-3 py-2 text-xs font-mono text-foreground outline-none focus:border-primary" placeholder={'{"wait_for":["username"],"actions":[{"action":"click","target":"submit"}]}' } />
                <label className="mt-3 flex items-center gap-2 text-xs text-muted-foreground" htmlFor="module-page-enabled"><input id="module-page-enabled" data-testid="module-page-enabled" type="checkbox" checked={pageEnabled} onChange={(event) => setPageEnabled(event.target.checked)} /> Enabled</label>
               {pageAction && <div role="status" className="mt-3 text-xs text-muted-foreground">{pageAction}</div>}
               <div className="mt-4 flex justify-end gap-2">
                  {pageEditing && <button type="button" onClick={() => { setPageEditing(null); setPageName(''); setPageDescription(''); setPageUrl(''); setPageLocators('{}'); setPageConfig('{}'); setPageExecution('{}'); setPageEnabled(true); setPageAction(''); }} className="rounded bg-muted px-3 py-1.5 text-xs text-muted-foreground hover:text-foreground">{t('studio.common.cancel', 'Cancel')}</button>}
                <button type="submit" data-testid="module-page-submit" disabled={pageAction.endsWith('…')} className="rounded bg-primary/15 px-3 py-1.5 text-xs text-primary hover:bg-primary/25 disabled:opacity-50">{pageEditing ? t('studio.common.savePage', 'Save page') : t('studio.common.createPage', 'Create page')}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Run Inspector View ───────────────────────────────────────────────────────
function RunInspectorView({ runId }: { runId: string }) {
  const { t } = useTranslation();
  const [tab, setTab] = useState("timeline");
  const [inspector, setInspector] = useState<Record<string, any> | null>(null);
  useEffect(() => {
    let mounted = true;
    setInspector(null);
    loadRunInspector(runId).then((data) => { if (mounted) setInspector(data); }).catch(() => { /* mock fallback below */ });
    return () => { mounted = false; };
  }, [runId]);
  const TABS = [
    { key:'timeline', label:t('studio.common.tabsTimeline') }, { key:'artifacts', label:t('studio.common.tabsArtifacts') },
    { key:'agent-calls', label:t('studio.common.tabsAgentCalls') }, { key:'metrics', label:t('studio.common.tabsMetrics') },
    { key:'logs', label:t('studio.common.tabsLogs') }, { key:'report', label:t('studio.common.tabsReport') },
  ];
  const header = inspector?.header ?? {};
  const summary = inspector?.summary ?? {};
  const kpis = [
    { label:t('studio.common.duration'), value:header.duration_ms ? `${(Number(header.duration_ms) / 1000).toFixed(1)}s` : "—", icon:Clock },
    { label:t('studio.common.module'), value:String(header.module ?? "—"), icon:Box },
    { label:t('studio.common.agent'), value:String(header.agent ?? "—"), icon:Bot },
    { label:t('studio.common.tokens'), value:Number(header.total_tokens ?? 0).toLocaleString(), icon:Zap },
    { label:t('studio.common.cost'), value:`$${Number(header.total_cost ?? 0).toFixed(3)}`, icon:Tag },
    { label:t('studio.common.tabsArtifacts'), value:String(header.artifacts_count ?? inspector?.artifacts?.length ?? 0), icon:FileText },
    { label:t('studio.common.pages'), value:String(header.pages?.length ?? 0), icon:Layers },
    { label:t('studio.common.tests'), value:String(summary.tests ?? "—"), icon:CheckCircle2 },
  ];
  const artifactsList: Array<{ id: string; name: string; path: string; size: string; age: string; module: string; downloadUrl: string }> = inspector?.artifacts?.length ? inspector.artifacts.map((a: any) => {
    const path = String(a.path ?? a.artifact_path ?? "");
    return {
      id: String(a.event_id ?? path),
      name: String(a.name ?? path.split(/[\\/]/).pop() ?? "artifact"),
      path,
      size: String(a.size ?? "—"),
      age: String(a.age ?? "recently"),
      module: String(a.module ?? header.module ?? "run"),
      downloadUrl: String(a.download_url ?? ""),
    };
  }) : [];
  const agentCalls: Array<{ agent: string; prompt: string; tokens: number; status: string }> = inspector?.agent_calls?.length ? inspector.agent_calls.map((c: any) => ({
    agent: String(c.agent ?? c.name ?? "Agent"), prompt: String(c.prompt ?? c.input ?? c.message ?? "Agent call"), tokens: Number(c.tokens ?? c.total_tokens ?? 0), status: normalizeRunStatus(c.status)
  })) : [];
  const timelineRows = Array.isArray(inspector?.timeline) ? inspector.timeline : [];
  function copyRunId() {
    void navigator.clipboard?.writeText(String(header.run_id ?? runId));
  }
  function exportInspector() {
    const blob = new Blob([JSON.stringify(inspector ?? { run_id: runId }, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${String(header.run_id ?? runId)}-inspector.json`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 0);
  }
  function copyArtifactPath(path: string) {
    if (path) void navigator.clipboard?.writeText(path);
  }
  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-4 px-5 py-3 border-b border-border flex-shrink-0">
        <div>
          <div className="flex items-center gap-2">
             <span className="text-sm font-semibold text-foreground font-mono">{String(header.run_id ?? runId)}</span>
             <StatusBadge status={normalizeRunStatus(header.status)}/>
          </div>
            <div className="text-xs text-muted-foreground mt-0.5 font-mono">{t('studio.common.started')} {header.created_at ? new Date(header.created_at).toLocaleTimeString() : "—"} · {String(header.module ?? "—")} · {String(header.agent ?? "—")}</div>
        </div>
        <div className="ml-auto flex gap-2">
          <button onClick={copyRunId} className="flex items-center gap-1.5 px-3 py-1.5 bg-muted rounded text-xs text-muted-foreground hover:text-foreground transition-colors"><Copy size={11}/> {t('studio.common.copyId')}</button>
          <button onClick={exportInspector} className="flex items-center gap-1.5 px-3 py-1.5 bg-muted rounded text-xs text-muted-foreground hover:text-foreground transition-colors"><Download size={11}/> {t('studio.common.export')}</button>
        </div>
      </div>
      {/* KPI row */}
      <div className="flex gap-3 px-5 py-3 border-b border-border flex-shrink-0 overflow-x-auto" style={{ scrollbarWidth:"none" }}>
        {kpis.map(({ label, value, icon: Icon }) => (
          <div key={label} className="flex-shrink-0 bg-card border border-border rounded-md px-3 py-2 flex flex-col gap-1 min-w-[90px]">
            <div className="flex items-center justify-between gap-2">
              <span className="text-xs text-muted-foreground">{label}</span>
              <Icon size={11} className="text-muted-foreground/60"/>
            </div>
            <span className="text-sm font-semibold text-foreground font-mono">{value}</span>
          </div>
        ))}
      </div>
      {/* Tabs */}
      <div className="flex gap-0 border-b border-border px-5 flex-shrink-0">
        {TABS.map((item) => (
          <button key={item.key} onClick={() => setTab(item.key)} className={`px-4 py-2.5 text-xs font-medium border-b-2 -mb-px transition-colors ${tab===item.key?"border-primary text-primary":"border-transparent text-muted-foreground hover:text-foreground"}`}>{item.label}</button>
        ))}
      </div>
      {/* Tab content */}
      <div className="flex-1 overflow-hidden">
        <div className="h-full overflow-y-auto p-5" style={{ scrollbarWidth:"none" }}>
            {tab==="timeline" && (
              <div className="space-y-2">
                {timelineRows.length === 0 && <div className="rounded-lg border border-dashed border-border p-8 text-center text-xs text-muted-foreground">{t('studio.common.noTimeline')}</div>}
                {timelineRows.map((row: any, index: number) => (
                  <div key={String(row.id ?? index)} className="flex items-center gap-3 rounded-lg border border-border bg-card px-4 py-3">
                    <span className="w-32 truncate text-xs font-mono text-foreground/80">{String(row.agent ?? row.name ?? row.label ?? "agent")}</span>
                    <div className="h-2 flex-1 overflow-hidden rounded-full bg-muted"><div className="h-full rounded-full bg-primary" style={{ width: `${Math.max(0, Math.min(100, Number(row.progress ?? 0)))}%` }} /></div>
                    <span className="w-14 text-right text-xs font-mono text-muted-foreground">{Number(row.progress ?? 0)}%</span>
                  </div>
                ))}
              </div>
            )}
            {tab==="artifacts" && (
              <div className="space-y-2">
                {artifactsList.map((a) => (
                   <div key={a.id} data-testid={`inspector-artifact-${a.id}`} className="flex items-center gap-3 bg-card border border-border rounded-lg px-4 py-3 hover:border-border/80 transition-colors group">
                    <FileText size={14} className="text-muted-foreground flex-shrink-0"/>
                    <div className="flex-1 min-w-0">
                      <div className="text-xs font-mono text-foreground">{a.name}</div>
                      <div className="text-xs text-muted-foreground mt-0.5">{a.size} · {a.age}</div>
                    </div>
                    <span className="px-1.5 py-0.5 bg-muted rounded text-xs text-muted-foreground font-mono">{a.module}</span>
                    <div className="flex gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
                       <a aria-label={`Download ${a.name}`} href={a.downloadUrl || undefined} download={a.name} className={`p-1.5 bg-muted rounded hover:bg-card transition-colors ${a.downloadUrl ? "" : "pointer-events-none opacity-40"}`}><Download size={11} className="text-muted-foreground"/></a>
                       <button aria-label={`Copy ${a.name} path`} onClick={() => copyArtifactPath(a.path)} disabled={!a.path} className="p-1.5 bg-muted rounded hover:bg-card transition-colors disabled:opacity-40"><Copy size={11} className="text-muted-foreground"/></button>
                    </div>
                  </div>
                ))}
              </div>
            )}
            {tab==="agent-calls" && (
              <div className="space-y-3">
                {agentCalls.map((c, i) => {
                  const cfg = STATUS_CFG[c.status] ?? STATUS_CFG.idle;
                  return (
                    <div key={i} className="bg-card border border-border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2"><Bot size={13} className="text-primary"/><span className="text-sm font-medium text-foreground">{c.agent}</span></div>
                        <div className="flex items-center gap-2"><span className="text-xs font-mono text-muted-foreground">{c.tokens.toLocaleString()} tokens</span><StatusBadge status={c.status}/></div>
                      </div>
                      <div className="bg-muted rounded p-3 text-xs font-mono text-muted-foreground leading-relaxed">{c.prompt.substring(0,120)}…</div>
                    </div>
                  );
                })}
              </div>
            )}
            {tab==="metrics" && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <StatCard icon={CheckCircle2} label={t('studio.common.passRate')} value={typeof summary.pass_rate === "number" ? `${(summary.pass_rate * 100).toFixed(1)}%` : "—"} accent="text-emerald-400"/>
                  <StatCard icon={Zap}          label={t('studio.common.avgDuration')} value={summary.avg_duration_ms != null ? `${(Number(summary.avg_duration_ms) / 1000).toFixed(2)}s` : "—"} accent="text-cyan-400"/>
                </div>
                <div className="bg-card border border-border rounded-lg p-4">
                  <div className="text-xs text-muted-foreground mb-3 font-medium uppercase tracking-wider">{t('studio.common.phaseBreakdown')}</div>
                  <div className="space-y-3">
                    {SOP_PHASES.slice(0,6).map((p) => {
                      const phase = Array.isArray(inspector?.phases) ? inspector.phases.find((item: any) => String(item.name) === p.label) : null;
                      const pct = phase?.progress != null ? Number(phase.progress) : phase?.status === "completed" ? 100 : phase?.status === "running" ? 50 : 0;
                      return (
                        <div key={p.id}>
                          <div className="flex justify-between text-xs mb-1">
                            <span className="text-muted-foreground">{p.label}</span>
                            <span className="font-mono text-foreground/70">{pct}%</span>
                          </div>
                          <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                            <div className={`h-full rounded-full ${phase?.status==="completed"?"bg-emerald-400":phase?.status==="running"?"bg-cyan-400 animate-pulse":"bg-muted"}`} style={{ width:`${pct}%` }}/>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            )}
             {tab==="logs" && <div className="h-80 flex flex-col bg-card border border-border rounded-lg overflow-hidden"><LogStream entries={(inspector?.logs ?? []).map((entry: any) => ({ ts:String(entry.timestamp ?? "—"), level:String(entry.level ?? "info"), msg:String(entry.message ?? entry.msg ?? ""), ctx:String(entry.agent ?? "backend") })) as LogEntry[]} filter="all"/></div>}
            {tab==="report" && (
              <div className="bg-card border border-border rounded-lg p-5 space-y-4">
                  <div className="flex items-center gap-2 text-xs text-muted-foreground mb-2"><Cpu size={11}/><span>AI {t('studio.common.tabsReport')} · {String(header.run_id ?? runId)}</span></div>
                <h3 className="text-sm font-semibold text-foreground">{t('studio.common.executionSummary')}</h3>
                 <p className="text-sm text-foreground/80 leading-relaxed">{String(inspector?.report?.summary ?? inspector?.report ?? t('studio.common.noReport'))}</p>
                <h4 className="text-sm font-semibold text-foreground">{t('studio.common.keyFindings')}</h4>
                <ul className="space-y-2 text-sm text-foreground/80">
                   {(Array.isArray(inspector?.report?.findings) ? inspector.report.findings : []).map((f: unknown,i: number) => (
                    <li key={i} className="flex items-start gap-2"><ArrowRight size={12} className="text-muted-foreground flex-shrink-0 mt-0.5"/>{String(f)}</li>
                  ))}
                </ul>
              </div>
            )}
        </div>
      </div>
    </div>
  );
}

// ─── Reports View ─────────────────────────────────────────────────────────────
function ReportsView({ snapshot }: { snapshot: StudioSnapshot | null }) {
  const { t } = useTranslation();
  const kpi = snapshot?.productKpi?.this_week ?? {};
  const reportRuns = snapshot?.runs ?? [];
  const failingBugs = snapshot?.bugs?.filter((bug) => String(bug.status ?? "open") === "open") ?? [];
  function exportReport() {
    const blob = new Blob([JSON.stringify({ kpi, runs: reportRuns, bugs: failingBugs }, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "alice-report.json";
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 0);
  }
  return (
    <div className="p-6 space-y-5 overflow-y-auto h-full" style={{ scrollbarWidth:"none" }}>
      <div className="grid grid-cols-3 gap-4">
        <StatCard icon={CheckCircle2} label={t('studio.common.passRate')} value={typeof kpi.success_rate === "number" && Number(kpi.runs ?? 0) > 0 ? `${(kpi.success_rate * 100).toFixed(1)}%` : "—"} sub={t('studio.common.fromProductKpi')} accent="text-emerald-400"/>
        <StatCard icon={BarChart2} label={t('studio.settings.totalRuns')} value={kpi.runs != null ? String(kpi.runs) : "—"} sub={t('studio.common.thisWeek')} accent="text-[#f0c040]"/>
        <StatCard icon={AlertTriangle} label={t('studio.common.openDefects')} value={String(failingBugs.length)} sub={t('studio.common.fromBugHistory')} accent="text-amber-400"/>
      </div>
      <div className="bg-card border border-border rounded-lg overflow-hidden">
        <div className="px-4 py-3 border-b border-border flex items-center justify-between">
          <span className="text-sm font-semibold text-foreground">{t('studio.common.recentTestRuns')}</span>
           <button onClick={exportReport} className="flex items-center gap-1.5 px-3 py-1.5 bg-muted rounded text-xs text-muted-foreground hover:text-foreground transition-colors"><Download size={11}/> {t('studio.common.export')}</button>
        </div>
        <div>
          <div className="grid grid-cols-5 px-4 py-2 border-b border-border">
            {[t('studio.common.module'),t('studio.common.status'),t('studio.common.tests'),t('studio.common.coverage'),t('studio.common.date')].map((h) => <span key={h} className="text-xs text-muted-foreground font-medium">{h}</span>)}
          </div>
          {reportRuns.map((run, i, arr) => {
            const status = normalizeRunStatus(run.status);
            const cfg = STATUS_CFG[status] ?? STATUS_CFG.idle;
            return (
              <div key={run.run_id} className={`grid grid-cols-5 px-4 py-3 hover:bg-white/3 transition-colors ${i<arr.length-1?"border-b border-border":""}`}>
                <span className="text-xs text-foreground/80">{run.module ?? run.workflow ?? run.run_id}</span>
                <span className={`text-xs font-medium ${cfg.text}`}>{cfg.label}</span>
                <span className="text-xs font-mono text-foreground/70">{String((run as any).tests_passed ?? "—")}/{String((run as any).tests_total ?? "—")}</span>
                <span className="text-xs font-mono text-foreground/70">{String((run as any).coverage ?? "—")}</span>
                <span className="text-xs text-muted-foreground">{run.created_at ? new Date(run.created_at).toLocaleString() : "—"}</span>
              </div>
            );
          })}
        </div>
      </div>
      <div className="bg-card border border-border rounded-lg p-4">
        <div className="text-xs text-muted-foreground mb-3 font-medium uppercase tracking-wider">{t('studio.common.topFailingTests')}</div>
        {failingBugs.map((bug, index) => (
          <div key={String(bug.bug_id ?? index)} className="flex items-start gap-3 py-2.5 border-b last:border-0 border-border">
            <XCircle size={13} className="text-red-400 flex-shrink-0 mt-0.5"/>
            <div>
              <div className="text-xs font-mono text-foreground/80">{String(bug.error_type ?? bug.bug_id ?? "Bug")}</div>

              <div className="text-xs text-muted-foreground mt-0.5">{String(bug.root_cause ?? bug.page ?? "Open defect")}</div>
            </div>
            <span className="ml-auto text-xs px-1.5 py-0.5 bg-muted rounded font-mono text-muted-foreground">{String(bug.module ?? "unknown")}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Gap Discovery View ───────────────────────────────────────────────────────
function GapsView({ snapshot, onRefresh }: { snapshot: StudioSnapshot | null; onRefresh?: () => void }) {
  const { t, i18n } = useTranslation();
  const [filter, setFilter] = useState("all");
  const [actionState, setActionState] = useState<Record<string, string>>({});
  const types = ["all","Missing Tests","Missing Types","Insufficient Coverage","Flaky","Untested Components"];
  const typeLabels: Record<string, string> = i18n.language.startsWith('zh')
    ? { all:t('studio.common.all'), "Missing Tests":"缺失测试", "Missing Types":"缺失类型", "Insufficient Coverage":"覆盖率不足", Flaky:"不稳定", "Untested Components":"未测试组件" }
    : { all:t('studio.common.all'), "Missing Tests":"Missing Tests", "Missing Types":"Missing Types", "Insufficient Coverage":"Insufficient Coverage", Flaky:"Flaky", "Untested Components":"Untested Components" };
  const liveGaps = snapshot?.bugs?.length ? snapshot.bugs.map((bug, index) => ({
    id:String(bug.bug_id ?? bug.id ?? index),
    type:String(bug.error_type ?? "Missing Tests"),
    severity:String(bug.severity ?? "medium"),
    module:String(bug.module ?? "unknown"),
    title:String(bug.root_cause ?? bug.error_type ?? "Known issue"),
    desc:String(bug.page ?? bug.matched_issue ?? "Reported by Bug History"),
  })) : [];
  const filtered = filter==="all" ? liveGaps : liveGaps.filter((g) => g.type===filter);
  async function handleBugAction(id: string, status: string) {
    setActionState((current) => ({ ...current, [id]: "saving" }));
    try { await updateBug(id, status); setActionState((current) => ({ ...current, [id]: status })); }
    catch { setActionState((current) => ({ ...current, [id]: "failed" })); }
  }
  return (
    <div className="p-6 space-y-5 overflow-y-auto h-full" style={{ scrollbarWidth:"none" }}>
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold text-foreground">{t('studio.common.gapDiscovery')}</h2>
          <p className="text-xs text-muted-foreground mt-0.5">{liveGaps.length} {t('studio.common.gapsIdentified')} — {t('studio.common.fromBugHistory')}</p>
        </div>
        <button onClick={onRefresh} className="flex items-center gap-1.5 px-3 py-1.5 bg-primary/10 border border-primary/25 rounded text-xs text-primary hover:bg-primary/15 transition-colors"><RefreshCw size={11}/> {t('studio.common.rescan')}</button>
      </div>
      <div className="flex gap-2 flex-wrap">
        {types.map((t) => (
          <button key={t} onClick={() => setFilter(t)} className={`px-3 py-1.5 rounded text-xs transition-colors ${filter===t?"bg-primary/15 border border-primary/30 text-primary":"bg-muted border border-border text-muted-foreground hover:text-foreground"}`}>{typeLabels[t] ?? t}</button>
        ))}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        {filtered.map((g) => {
          const sv = SEV_CFG[g.severity];
          return (
            <div key={g.id} data-testid={`gap-card-${g.id}`} className="bg-card border border-border rounded-lg p-4 hover:border-border/80 transition-colors">
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className={`text-xs px-1.5 py-0.5 rounded border font-medium ${sv.bg} ${sv.text} ${sv.border}`}>{sv.label}</span>
                  <span className="text-xs text-muted-foreground">{g.type}</span>
                </div>
                <span className="text-xs font-mono text-muted-foreground">{g.module}</span>
              </div>
              <div className="text-sm font-semibold text-foreground mb-2">{g.title}</div>
              <p className="text-xs text-muted-foreground leading-relaxed mb-3">{g.desc}</p>
              <div className="flex items-center gap-2">
                 <button onClick={() => void handleBugAction(g.id, "fixed")} className="px-2.5 py-1 bg-primary/10 border border-primary/25 rounded text-xs text-primary hover:bg-primary/15 transition-colors">{actionState[g.id] === "saving" ? t('studio.common.saving') : t('studio.common.resolve')}</button>
                 <button onClick={() => void handleBugAction(g.id, "wont_fix")} className="px-2.5 py-1 bg-muted border border-border rounded text-xs text-muted-foreground hover:text-foreground transition-colors">{t('studio.common.ignore')}</button>
                 <button onClick={() => void handleBugAction(g.id, "closed")} className="px-2.5 py-1 bg-muted border border-border rounded text-xs text-muted-foreground hover:text-foreground transition-colors">{t('studio.common.archive')}</button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ─── Memory Explorer View ─────────────────────────────────────────────────────
function MemoryView({ snapshot }: { snapshot: StudioSnapshot | null }) {
  const { t } = useTranslation();
  const [selected, setSelected] = useState<number|null>(null);
  const [search, setSearch] = useState("");
  const [results, setResults] = useState<Record<string, any>[]>([]);
  useEffect(() => {
    if (!search.trim()) { setResults([]); return; }
    let mounted = true;
    searchMemory(search).then((items) => { if (mounted) setResults(items); }).catch(() => { if (mounted) setResults([]); });
    return () => { mounted = false; };
  }, [search]);
  const backendBlocks = results.map((item, index) => {
    const meta = item.metadata ?? {};
    const type = String(meta.memory_type ?? meta.type ?? "semantic").toLowerCase().includes("histor") ? "episodic" : String(meta.memory_type ?? meta.type ?? "semantic").toLowerCase().includes("workflow") ? "procedural" : "semantic";
    return { id:index + 1, type, title:String(item.content ?? "Memory result").slice(0, 100), age:String(meta.updated_at ?? "recently"), tags:[String(meta.module ?? "memory")], tokens:String(item.content ?? "").length };
  });
  const memoryBlocks = backendBlocks;
  const total = memoryBlocks.reduce((a, m) => a+m.tokens, 0);
  const filtered = memoryBlocks.filter((m) => m.title.toLowerCase().includes(search.toLowerCase()) || m.tags.some((t) => t.includes(search.toLowerCase())));
  const sel = memoryBlocks.find((m) => m.id===selected);
  return (
    <div className="flex h-full overflow-hidden">
      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="px-5 py-3.5 border-b border-border flex items-center gap-4 flex-shrink-0">
          <div className="flex items-center gap-2 bg-muted rounded px-3 py-1.5 flex-1 max-w-xs">
            <Search size={11} className="text-muted-foreground/60 flex-shrink-0"/>
            <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder={t('studio.common.searchMemory')} className="bg-transparent text-xs text-foreground placeholder:text-muted-foreground/50 outline-none w-full"/>
          </div>
          <div className="flex items-center gap-3 text-xs text-muted-foreground ml-auto">
            {(["episodic","semantic","procedural"] as const).map((type) => {
              const count = memoryBlocks.filter((m) => m.type===type).length;
              const mc = MEM_CFG[type];
              return <div key={type} className="flex items-center gap-1.5"><span className={`w-2 h-2 rounded-sm ${mc.bg} border ${mc.border}`}/><span className={mc.color}>{t(`studio.common.memoryTypes.${type}`, mc.label)}</span><span className="text-muted-foreground">{count}</span></div>;
            })}
            <span className="font-mono">{total.toLocaleString()} tokens</span>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto p-5" style={{ scrollbarWidth:"none" }}>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {filtered.map((block) => {
              const mc = MEM_CFG[block.type as keyof typeof MEM_CFG];
              const isSel = selected===block.id;
              return (
                <button key={block.id} onClick={() => setSelected(block.id)} className={`text-left p-4 rounded-lg border transition-all ${isSel?"border-primary/40 bg-primary/5":"border-border bg-card hover:border-border/70"}`}>
                  <div className="flex items-start justify-between mb-2">
                    <span className={`text-xs px-1.5 py-0.5 rounded ${mc.bg} ${mc.color} border ${mc.border} font-medium`}>{t(`studio.common.memoryTypes.${block.type}`, mc.label)}</span>
                    <span className="text-xs text-muted-foreground/60 font-mono">{block.age}</span>
                  </div>
                  <div className="text-sm font-medium text-foreground leading-snug mb-2">{block.title}</div>
                  <div className="flex items-center justify-between">
                    <div className="flex gap-1 flex-wrap">{block.tags.map((t) => <span key={t} className="px-1.5 py-0.5 bg-muted rounded text-xs text-muted-foreground">#{t}</span>)}</div>
                    <span className="text-xs font-mono text-muted-foreground/60 ml-2 flex-shrink-0">{block.tokens}t</span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      </div>
      {sel && (
        <div className="w-64 border-l border-border bg-card flex flex-col flex-shrink-0">
          <div className="p-4 border-b border-border">
            <span className={`text-xs px-1.5 py-0.5 rounded ${MEM_CFG[sel.type as keyof typeof MEM_CFG].bg} ${MEM_CFG[sel.type as keyof typeof MEM_CFG].color} border ${MEM_CFG[sel.type as keyof typeof MEM_CFG].border} font-medium`}>{t(`studio.common.memoryTypes.${sel.type}`, MEM_CFG[sel.type as keyof typeof MEM_CFG].label)}</span>
            <div className="text-sm font-semibold text-foreground mt-2">{sel.title}</div>
          </div>
          <div className="p-4 space-y-2.5 border-b border-border text-xs">
            {[["Tokens",sel.tokens.toString()],["Age",sel.age+" ago"],["ID",`mem-${String(sel.id).padStart(4,"0")}`],["Associations","3 nodes"]].map(([l,v]) => (
              <div key={l} className="flex justify-between"><span className="text-muted-foreground">{l}</span><span className="text-foreground/70 font-mono">{v}</span></div>
            ))}
          </div>
          <div className="p-4">
            <div className="text-xs text-muted-foreground mb-2 font-medium uppercase tracking-wider">{t('studio.common.tags')}</div>
            <div className="flex flex-wrap gap-1.5">{sel.tags.map((t) => <span key={t} className="px-1.5 py-0.5 bg-muted rounded text-xs text-muted-foreground font-mono">#{t}</span>)}</div>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Knowledge Base View ──────────────────────────────────────────────────────
function KnowledgeView({ snapshot }: { snapshot: StudioSnapshot | null }) {
  const { t } = useTranslation();
  const knowledgeCollections = snapshot?.knowledge?.collections ?? {};
  const collections = Object.entries(knowledgeCollections).map(([name, docs]) => ({ name, docs:Number(docs), updated:"from store", status:"ready" }));
  return (
    <div className="p-6 space-y-5 overflow-y-auto h-full" style={{ scrollbarWidth:"none" }}>
      <div className="grid grid-cols-3 gap-4">
        <StatCard icon={Database}     label={t("studio.knowledgeBase.collections")}  value={String(collections.length)} accent="text-primary"/>
        <StatCard icon={FileText}     label={t("studio.knowledgeBase.documents")}    value={collections.reduce((sum, c) => sum + c.docs, 0).toLocaleString()} sub={t("studio.knowledgeBase.totalIndexed")} accent="text-sky-400"/>
        <StatCard icon={CheckCircle2} label={t("studio.knowledgeBase.chroma")}     value={snapshot?.knowledge?.available ? `● ${t('studio.common.online')}` : t("studio.common.unavailable")} sub={t("studio.knowledgeBase.fromKnowledgeStore")} accent="text-emerald-400"/>
      </div>
      <div className="bg-card border border-border rounded-lg overflow-hidden">
        <div className="px-4 py-3 border-b border-border"><span className="text-sm font-semibold text-foreground">{t("studio.knowledgeBase.collections")}</span></div>
        <div>

          <div className="grid grid-cols-4 px-4 py-2.5 border-b border-border">
            {[t("studio.knowledgeBase.name"),t("studio.knowledgeBase.documents"),t("studio.knowledgeBase.lastUpdated"),t("studio.knowledgeBase.status")].map((h) => <span key={h} className="text-xs text-muted-foreground font-medium">{h}</span>)}
          </div>
          {collections.map((c, i) => (
            <div key={c.name} className={`grid grid-cols-4 px-4 py-3 hover:bg-white/3 transition-colors items-center ${i<collections.length-1?"border-b border-border":""}`}>
              <span className="text-xs font-mono text-foreground/80">{c.name}</span>
              <span className="text-xs font-mono text-foreground/70">{c.docs.toLocaleString()}</span>
              <span className="text-xs text-muted-foreground">{c.updated === 'from store' ? t('studio.common.fromBackend') : c.updated}</span>
              <StatusBadge status={c.status}/>
            </div>
          ))}
        </div>
      </div>
      <div className="bg-card border border-border rounded-lg p-4">
         <div className="text-xs text-muted-foreground mb-3 font-medium uppercase tracking-wider">{t("studio.knowledgeBase.recentAdditions")}</div>
         {collections.length === 0 && <div className="text-xs text-muted-foreground">{t("studio.knowledgeBase.noIndexed")}</div>}
        {false && ["auth-token-patterns.json","api-rate-limit-cases.yaml","dashboard-component-specs.md","payment-edge-cases.md","session-management.json"].map((doc) => (
          <div key={doc} className="flex items-center gap-3 py-2.5 border-b last:border-0 border-border">
            <FileJson size={12} className="text-sky-400 flex-shrink-0"/>
            <span className="text-xs font-mono text-foreground/80">{doc}</span>
            <span className="text-xs text-muted-foreground ml-auto">just now</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Knowledge Graph View ─────────────────────────────────────────────────────
function KnowledgeGraphView({ snapshot }: { snapshot: StudioSnapshot | null }) {
  const { t } = useTranslation();
  const [zoom, setZoom] = useState(1);
  const lineageNodes = snapshot?.lineage?.nodes ?? [];
  const nodes: Array<{ id: string; x: number; y: number; r: number; type: string; label: string }> = lineageNodes.map((node: any, index: number) => ({
    id:String(node.id ?? index), x:80 + (index % 6) * 125, y:70 + Math.floor(index / 6) * 110, r:node.status === "generated" ? 16 : 12,
    type:node.status === "generated" ? "module" : node.status === "pending" ? "issue" : "pattern", label:String(node.label ?? node.id ?? "artifact"),
  }));
  const edges: Array<[string, string]> = (snapshot?.lineage?.edges ?? []).map((edge: any) => [String(edge.source), String(edge.target)] as [string, string]);
  /*
  const nodes = [
    { id:"auth",    x:300, y:140, r:18, type:"module",  label:"Authentication" },
    { id:"dash",    x:500, y:100, r:18, type:"module",  label:"Dashboard" },
    { id:"api",     x:480, y:240, r:18, type:"module",  label:"API Gateway" },
    { id:"pay",     x:180, y:240, r:18, type:"module",  label:"Payment" },
    { id:"sett",    x:650, y:180, r:18, type:"module",  label:"Settings" },
    { id:"notif",   x:160, y:140, r:18, type:"module",  label:"Notifications" },
    { id:"tok-exp", x:290, y:60,  r:12, type:"issue",   label:"Token Expiry" },
    { id:"rate-lim",x:560, y:60,  r:12, type:"issue",   label:"Rate Limit" },
    { id:"slow-res",x:390, y:220, r:12, type:"issue",   label:"Slow Response" },
    { id:"404err",  x:570, y:300, r:12, type:"issue",   label:"404 Errors" },
    { id:"form-val",x:200, y:310, r:12, type:"issue",   label:"Form Valid." },
    { id:"auth-pat",x:380, y:160, r:10, type:"pattern", label:"Auth Pattern" },
    { id:"rest-pat",x:480, y:170, r:10, type:"pattern", label:"REST Pattern" },
    { id:"form-pat",x:260, y:200, r:10, type:"pattern", label:"Form Pattern" },
    { id:"cache-pat",x:600, y:130,r:10, type:"pattern", label:"Cache Pattern" },
  ];
  const edges = [
    ["auth","tok-exp"],["auth","auth-pat"],["auth","slow-res"],["dash","rate-lim"],["dash","cache-pat"],
    ["api","rate-lim"],["api","404err"],["api","rest-pat"],["pay","form-val"],["pay","slow-res"],
    ["sett","cache-pat"],["notif","form-val"],["auth-pat","rest-pat"],["form-pat","form-val"],["auth","api"],
  ]; */
  const nodeColors = { module:"#4a7cf7", issue:"#f0c040", pattern:"#a78bfa" };
  return (
    <div className="p-6 space-y-4 overflow-y-auto h-full" style={{ scrollbarWidth:"none" }}>
      <div className="flex items-center justify-between">
         <div><h2 className="text-sm font-semibold text-foreground">{t('studio.common.knowledgeGraph')}</h2><p className="text-xs text-muted-foreground mt-0.5">{nodes.length} {t('studio.common.nodes')} · {edges.length} {t('studio.common.relationships')}</p></div>
        <div className="flex gap-2">
           <button onClick={() => setZoom((value) => Math.min(2, value + 0.2))} className="flex items-center gap-1 px-2.5 py-1.5 bg-muted border border-border rounded text-xs text-muted-foreground hover:text-foreground transition-colors"><ZoomIn size={11}/></button>
           <button onClick={() => setZoom((value) => Math.max(0.6, value - 0.2))} className="flex items-center gap-1 px-2.5 py-1.5 bg-muted border border-border rounded text-xs text-muted-foreground hover:text-foreground transition-colors"><ZoomOut size={11}/></button>
           <button onClick={() => setZoom(1)} className="px-2.5 py-1.5 bg-muted border border-border rounded text-xs text-muted-foreground hover:text-foreground transition-colors">{t('studio.common.reset')}</button>
        </div>
      </div>
      <div className="bg-card border border-border rounded-lg overflow-hidden">
         <svg viewBox={`0 0 ${800 / zoom} ${380 / zoom}`} className="w-full" style={{ fontFamily:"Inter, sans-serif" }}>
          <defs>
            <radialGradient id="bg-grad" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="rgba(74,124,247,0.03)"/>
              <stop offset="100%" stopColor="transparent"/>
            </radialGradient>
          </defs>
          <rect width="800" height="380" fill="url(#bg-grad)"/>
          {edges.map(([a,b]: [string, string]) => {
            const na = nodes.find((n: typeof nodes[number]) => n.id===a)!;
            const nb = nodes.find((n: typeof nodes[number]) => n.id===b)!;
            return <line key={`${a}-${b}`} x1={na.x} y1={na.y} x2={nb.x} y2={nb.y} stroke="rgba(50,90,180,0.2)" strokeWidth="1"/>;
          })}
          {nodes.map((n: typeof nodes[number]) => {
            const c = nodeColors[n.type as keyof typeof nodeColors];
            return (
              <g key={n.id} style={{ cursor:"pointer" }}>
                <circle cx={n.x} cy={n.y} r={n.r+3} fill={c} opacity=".08"/>
                <circle cx={n.x} cy={n.y} r={n.r} fill={c} opacity=".2" stroke={c} strokeWidth="1.5"/>
                <text x={n.x} y={n.y+n.r+12} textAnchor="middle" fontSize="9" fill="#4e6a92">{n.label}</text>
              </g>
            );
          })}
        </svg>
      </div>
      <div className="flex items-center gap-6">
         {[{color:"#4a7cf7",label:t('studio.common.moduleCount', { count: 6 })},{color:"#f0c040",label:t('studio.common.issueCount', { count: 5 })},{color:"#a78bfa",label:t('studio.common.patternCount', { count: 4 })}].map(({ color,label }) => (
          <div key={label} className="flex items-center gap-2 text-xs text-muted-foreground">
            <span className="w-3 h-3 rounded-full" style={{ background:color, opacity:0.6 }}/>
            {label}
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Artifacts View ───────────────────────────────────────────────────────────
function ArtifactsView({ snapshot }: { snapshot: StudioSnapshot | null }) {
  const { t } = useTranslation();
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");
  const typeIcons: Record<string,React.ElementType> = { markdown:FileText, image:Image, json:FileJson, code:Code2, yaml:FileText, pdf:File };
  const typeColors: Record<string,string> = { markdown:"text-sky-400", image:"text-violet-400", json:"text-amber-400", code:"text-emerald-400", yaml:"text-orange-400", pdf:"text-red-400" };
  const types = ["all","markdown","json","image","code","yaml","pdf"];
  const liveArtifacts = snapshot?.artifacts?.length ? snapshot.artifacts.map((a, index) => {
    const name = String(a.name ?? a.path ?? `artifact-${index}`);
    const ext = name.split(".").pop()?.toLowerCase() ?? "";
    const type = ext === "md" ? "markdown" : ext === "json" ? "json" : ["png","jpg","jpeg","gif","svg"].includes(ext) ? "image" : ["py","ts","tsx","js","css"].includes(ext) ? "code" : ["yaml","yml"].includes(ext) ? "yaml" : ext === "pdf" ? "pdf" : "markdown";
     return { name, type, size: `${Number(a.size ?? 0).toLocaleString()} B`, age: a.timestamp ? new Date(a.timestamp).toLocaleString() : t('studio.common.fromBackend'), module: String(a.module ?? "run"), page: String(a.page ?? ""), path: String(a.path ?? name) };
   }) : [];
  const filtered = liveArtifacts.filter((a) => {
    const matchSearch = a.name.toLowerCase().includes(search.toLowerCase()) || a.module.toLowerCase().includes(search.toLowerCase());
    const matchType = typeFilter==="all" || a.type===typeFilter;
    return matchSearch && matchType;
  });
  return (
    <div className="p-5 space-y-4 overflow-y-auto h-full" style={{ scrollbarWidth:"none" }}>
      <div className="flex items-center gap-3 flex-wrap">
        <div className="flex items-center gap-2 bg-muted rounded px-3 py-1.5 flex-1 min-w-[180px] max-w-xs">
          <Search size={11} className="text-muted-foreground/60 flex-shrink-0"/>
           <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder={t('studio.common.searchArtifacts')} className="bg-transparent text-xs text-foreground placeholder:text-muted-foreground/50 outline-none w-full"/>
        </div>
        <div className="flex gap-1.5 flex-wrap">
           {types.map((type) => <button key={type} onClick={() => setTypeFilter(type)} className={`px-2.5 py-1.5 rounded text-xs transition-colors ${typeFilter===type?"bg-primary/15 border border-primary/30 text-primary":"bg-muted border border-border text-muted-foreground hover:text-foreground"}`}>{type === 'all' ? t('studio.common.all') : type}</button>)}
        </div>
           <span className="text-xs text-muted-foreground ml-auto">{filtered.length} {t('studio.common.artifactsCount')}</span>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
         {filtered.map((a, index) => {
          const Icon = typeIcons[a.type] ?? File;
          const iconColor = typeColors[a.type] ?? "text-muted-foreground";
          return (
             <div key={`${a.module}:${a.name}:${index}`} className="bg-card border border-border rounded-lg p-4 hover:border-border/70 transition-colors group cursor-pointer">
              <div className="flex items-start gap-3">
                <div className={`w-8 h-8 rounded bg-muted flex items-center justify-center flex-shrink-0 ${iconColor}`}>
                  <Icon size={14}/>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-mono text-foreground leading-tight truncate">{a.name}</div>
                  <div className="text-xs text-muted-foreground mt-0.5">{a.size}</div>
                </div>
              </div>
              <div className="flex items-center justify-between mt-3">

                <span className="px-1.5 py-0.5 bg-muted rounded text-xs font-mono text-muted-foreground truncate max-w-[120px]">{a.module}</span>
                 <div className="flex gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button onClick={() => {
                      const url = `/api/v1/kpi/artifacts/${encodeURIComponent(snapshot?.projectId ?? '')}/download?module=${encodeURIComponent(a.module)}&page=${encodeURIComponent(a.page)}&name=${encodeURIComponent(a.name)}`;
                      const anchor = document.createElement('a');
                      anchor.href = url;
                      anchor.download = a.name;
                      document.body.appendChild(anchor);
                      anchor.click();
                      anchor.remove();
                    }} className="p-1 bg-muted rounded hover:bg-secondary transition-colors" title={t('studio.common.download')} aria-label={`${t('studio.common.download')} ${a.name}`}><Download size={10} className="text-muted-foreground"/></button>
                    <button onClick={() => void navigator.clipboard?.writeText(a.path)} className="p-1 bg-muted rounded hover:bg-secondary transition-colors" title={t('studio.common.copyPath')} aria-label={`${t('studio.common.copyPath')} ${a.name}`}><Copy size={10} className="text-muted-foreground"/></button>
                 </div>
                <span className="text-xs text-muted-foreground/60 ml-auto group-hover:hidden">{a.age}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ─── Intelligence Chat View ───────────────────────────────────────────────────
function ChatView() {
  const { t } = useTranslation();
  const [input, setInput] = useState("");
  const chatSessions = useChatStore((state) => state.sessions);
  const activeId = useChatStore((state) => state.activeId);
  const sendMessage = useChatStore((state) => state.sendMessage);
  const newSession = useChatStore((state) => state.newSession);
  const selectSession = useChatStore((state) => state.selectSession);
  const activeSession = chatSessions.find((session) => session.id === activeId) ?? chatSessions[0];
  const msgs = activeSession?.messages ?? [];
  const sessions = chatSessions.map((session, index) => ({ id:session.id, title:session.name, active:session.id === activeSession?.id, time:index === 0 ? "recent" : "—" }));
  const suggestions = [t("studio.chat.showFailing"),t("studio.chat.summarizeRun"),t("studio.chat.coverageGaps"),t("studio.chat.explainError")];

  function handleSend() {
    if (!input.trim()) return;
    void sendMessage(input);
    setInput("");
  }

  return (
    <div className="flex h-full overflow-hidden">
      <div className="w-44 border-r border-border flex flex-col flex-shrink-0 bg-sidebar">
        <div className="px-3 py-3 border-b border-border">
           <button onClick={newSession} className="flex items-center gap-1.5 w-full px-2.5 py-1.5 bg-primary/10 border border-primary/25 rounded text-xs text-primary hover:bg-primary/15 transition-colors"><Plus size={11}/> {t("studio.chat.newChat")}</button>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-1" style={{ scrollbarWidth:"none" }}>
          {sessions.map((s) => (
            <button key={s.id} onClick={() => selectSession(s.id)} className={`w-full text-left px-3 py-2 rounded text-xs transition-colors ${s.active?"bg-primary/10 text-primary":"text-muted-foreground hover:text-foreground hover:bg-white/4"}`}>
              <div className="truncate font-medium">{s.title}</div>
               <div className="text-muted-foreground/60 mt-0.5">{s.time === "recent" ? t("studio.chat.recent") : s.time} {s.time === "recent" ? "" : "ago"}</div>
            </button>
          ))}
        </div>
      </div>
      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="flex-1 overflow-y-auto p-5 space-y-4" style={{ scrollbarWidth:"none" }}>
          {msgs.map((m) => (
            <div key={m.id} className={`flex gap-3 ${m.role==="user"?"flex-row-reverse":""}`}>
              <div className={`w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 ${m.role==="user"?"bg-primary/20 border border-primary/30":"bg-muted border border-border"}`}>
                {m.role==="user" ? <span className="text-xs font-semibold text-primary">U</span> : <Bot size={13} className="text-muted-foreground"/>}
              </div>
              <div className={`flex-1 max-w-[520px] ${m.role==="user"?"items-end flex flex-col":""}`}>
                <div className={`rounded-lg px-4 py-3 text-sm leading-relaxed ${m.role==="user"?"bg-primary/10 border border-primary/20 text-foreground":"bg-card border border-border text-foreground/85"}`}>
                  {m.content.split("\n").map((line, i) => (
                    <p key={i} className={line==="\n"?"mt-2":""} dangerouslySetInnerHTML={{ __html: line.replace(/\*\*(.+?)\*\*/g,"<strong>$1</strong>") }}/>
                  ))}
                </div>
                {"tools" in m && m.tools && (
                  <div className="flex gap-1.5 mt-1.5 flex-wrap">
                    {(Array.isArray(m.tools) ? m.tools : []).map((t: any, index: number) => <span key={index} className="px-2 py-0.5 bg-muted border border-border rounded text-xs text-muted-foreground font-mono">⚙ {String(typeof t === "string" ? t : t?.name ?? t?.type ?? "tool")}</span>)}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
        {msgs.length<=1 && (
          <div className="px-5 pb-3 grid grid-cols-2 gap-2">
            {suggestions.map((s) => (
              <button key={s} onClick={() => setInput(s)} className="text-left px-3 py-2 bg-card border border-border rounded-lg text-xs text-muted-foreground hover:text-foreground hover:border-primary/30 transition-colors">{s}</button>
            ))}
          </div>
        )}
        <div className="px-5 py-4 border-t border-border flex items-end gap-3 flex-shrink-0">
          <textarea value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => { if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();handleSend();}}} placeholder={t("studio.chat.placeholder")} rows={2} className="flex-1 bg-muted border border-border rounded-lg px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground/50 outline-none focus:border-primary/50 resize-none"/>
          <button onClick={handleSend} className="flex items-center gap-1.5 px-4 py-3 bg-primary/10 border border-primary/30 rounded-lg text-sm text-primary hover:bg-primary/20 transition-colors flex-shrink-0"><Send size={14}/></button>
        </div>
      </div>
    </div>
  );
}

// ─── Observability View ───────────────────────────────────────────────────────
function ObservabilityView({ snapshot, onRefresh }: { snapshot: StudioSnapshot | null; onRefresh?: () => void }) {
  const { t } = useTranslation();
  const [tab, setTab] = useState("overview");
  const telemetry = snapshot?.observability ?? {};
  const memory = telemetry.memory ?? {};
  const threads = telemetry.threads ?? {};
  const tasks = telemetry.tasks ?? {};
  const queue = telemetry.queue ?? {};
  const websocket = telemetry.websocket ?? {};
  const gc = telemetry.gc ?? {};
  return (
    <div className="h-full flex flex-col overflow-hidden">
      <div className="flex items-center gap-4 px-5 py-3 border-b border-border flex-shrink-0">
        <div className="flex gap-0 flex-1">
          {["overview","memory","threads","queue"].map((tabId) => (
              <button key={tabId} onClick={() => setTab(tabId)} className={`px-4 py-2 text-xs font-medium capitalize border-b-2 -mb-px transition-colors ${tab===tabId?"border-primary text-primary":"border-transparent text-muted-foreground hover:text-foreground"}`}>{tabId === "queue" ? t("studio.observability.queue") : tabId === "threads" ? t("studio.observability.threads") : tabId === "memory" ? t("studio.observability.memory") : t("studio.observability.overview")}</button>
          ))}
        </div>
        <div className="flex items-center gap-2 text-xs text-muted-foreground ml-auto">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"/>
           <span>{t("studio.observability.autoRefresh")}</span>
           <button onClick={onRefresh} className="p-1.5 bg-muted rounded hover:bg-secondary transition-colors" aria-label={t('common.refresh')}><RefreshCw size={11}/></button>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto p-5" style={{ scrollbarWidth:"none" }}>
        {tab==="overview" && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
               <StatCard icon={Cpu}     label={t("studio.observability.rss")} value={memory.rss_mb != null && Number(memory.rss_mb) >= 0 ? `${memory.rss_mb} MB` : "—"} sub={t("studio.observability.processResident")} accent="text-cyan-400"/>
               <StatCard icon={Network} label={t("studio.observability.threadsCount")}    value={threads.count != null ? String(threads.count) : "—"} sub={`${threads.daemon_count ?? "—"} ${t("studio.observability.daemon")}`} accent="text-primary"/>
               <StatCard icon={Zap}     label={t("studio.observability.activeTasks")}value={tasks.pending != null ? String(tasks.pending) : "—"} sub={`${queue.queued ?? "—"} ${t("studio.observability.queued")}`} accent="text-emerald-400"/>
               <StatCard icon={Server}  label={t("studio.observability.wsConns")}   value={String(websocket.total ?? 0)} sub={t("studio.observability.activeConnections")} accent="text-violet-400"/>
            </div>
            <div className="bg-card border border-border rounded-lg divide-y divide-border">
               {[
                 {label:"API Gateway", status:String(snapshot?.health?.status ?? "unknown")},
                 {label:"ChromaDB", status:snapshot?.knowledge?.available ? t("studio.common.healthy") : t("studio.common.unavailable")},
                 {label:"Redis Queue", status:String(queue.backend ?? "unknown")},
                 {label:"WebSocket Server", status:websocket.total != null ? `${websocket.total} ${t("studio.observability.activeConnections")}` : "—"},
                 {label:"Model Providers", status:snapshot?.providers?.length ? `${snapshot.providers.length} ${t("studio.dashboard.configured")}` : t("studio.common.unavailable")},
               ].map((r) => (
                  <div key={r.label} className="flex items-center justify-between px-4 py-3">
                   <div className="flex items-center gap-2"><span className={`w-1.5 h-1.5 rounded-full ${r.status === t("studio.common.unavailable") || r.status === "unknown" ? "bg-amber-400" : "bg-emerald-400"}`}/><span className="text-xs text-muted-foreground">{r.label}</span></div>
                    <span className="text-xs font-medium text-foreground/70">{r.status}</span>
                 </div>
              ))}
            </div>
          </div>
        )}
        {tab==="memory" && (
          <div className="space-y-4">
              {[{label:"RSS Memory",value:memory.rss_mb},{label:"VMS Memory",value:memory.vms_mb}].map((m) => (
               <div key={m.label} className="bg-card border border-border rounded-lg p-4">
                 <div className="flex justify-between text-xs"><span className="text-muted-foreground">{m.label}</span><span className="font-mono text-foreground/70">{m.value != null ? `${m.value} MB` : "—"}</span></div>
               </div>
            ))}
            <div className="bg-card border border-border rounded-lg p-4">
              <div className="text-xs text-muted-foreground mb-3 font-medium uppercase tracking-wider">{t('studio.common.gcGenerations')}</div>
               {[{gen:"Gen 0",count:gc.gen0},{gen:"Gen 1",count:gc.gen1},{gen:"Gen 2",count:gc.gen2}].map((g) => (
                <div key={g.gen} className="flex items-center justify-between py-2 border-b last:border-0 border-border">
                  <span className="text-xs text-muted-foreground">{g.gen}</span>
                   <span className="text-xs font-mono text-foreground/70">{g.count != null ? `${Number(g.count).toLocaleString()} ${t("studio.observability.collections")}` : "—"}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {tab==="threads" && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
                <StatCard icon={Cpu}   label={t('studio.common.totalThreads')} value={threads.count != null ? String(threads.count) : "—"} accent="text-primary"/>
                <StatCard icon={Zap}   label={t('studio.common.pendingTasks')} value={tasks.pending != null ? String(tasks.pending) : "—"} accent="text-cyan-400"/>
            </div>
            <div className="bg-card border border-border rounded-lg overflow-hidden">
              <div className="grid grid-cols-3 px-4 py-2.5 border-b border-border">{[t('studio.common.thread'),t('studio.common.status'),t('studio.common.task')].map((h) => <span key={h} className="text-xs text-muted-foreground font-medium">{h}</span>)}</div>
               {Array.isArray(threads.items) ? threads.items.map((t: any,i: number,arr: any[]) => {
                const cfg = STATUS_CFG[t.status] ?? STATUS_CFG.idle;
                return <div key={t.id} className={`grid grid-cols-3 px-4 py-2.5 hover:bg-white/3 transition-colors ${i<arr.length-1?"border-b border-border":""}`}><span className="text-xs font-mono text-foreground/70">{t.id}</span><span className={`text-xs font-medium ${cfg.text}`}>{cfg.label}</span><span className="text-xs font-mono text-muted-foreground truncate">{t.task}</span></div>;
               }) : <div className="px-4 py-6 text-xs text-muted-foreground">{t('studio.common.noThread')}</div>}
            </div>
          </div>
        )}
        {tab==="queue" && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <StatCard icon={Server}  label={t('studio.common.queueDepth')} value={String(queue.queued ?? 0)} accent="text-amber-400"/>
                <StatCard icon={Network} label={t('studio.common.wsActive')} value={String(websocket.total ?? 0)} accent="text-cyan-400"/>
                <StatCard icon={Zap}     label={t('studio.common.running')} value={String(queue.running ?? 0)} accent="text-primary"/>
                <StatCard icon={Zap}     label={t('studio.common.completed')} value={String(queue.completed ?? 0)} accent="text-violet-400"/>
            </div>
            <div className="bg-card border border-border rounded-lg p-4">
               <div className="text-xs text-muted-foreground mb-3 font-medium uppercase tracking-wider">{t('studio.common.queueItems')}</div>
               {(Array.isArray(queue.items) ? queue.items : []).map((q: any) => (
                <div key={q.id} className="flex items-center justify-between py-2.5 border-b last:border-0 border-border">
                  <span className="text-xs font-mono text-foreground/70">{q.id}</span>
                  <span className="text-xs text-muted-foreground">{q.type}</span>
                  <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${q.priority==="high"?"bg-amber-400/10 text-amber-400 border border-amber-400/20":"bg-muted text-muted-foreground border border-border"}`}>{q.priority}</span>
                </div>
               ))}
                {!Array.isArray(queue.items) || queue.items.length === 0 ? <div className="py-6 text-center text-xs text-muted-foreground">{t('studio.common.noQueue')}</div> : null}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Global Runs View ─────────────────────────────────────────────────────────
function HistoryView({ snapshot }: { snapshot: StudioSnapshot | null }) {
  const { t } = useTranslation();
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [page, setPage] = useState(0);
  const [pageRuns, setPageRuns] = useState<StudioRun[]>(snapshot?.runs ?? []);
  const [total, setTotal] = useState(snapshot?.runs?.length ?? 0);
  const [loading, setLoading] = useState(false);
  const pageSize = 10;
  useEffect(() => {
    let mounted = true;
    setLoading(true);
    void loadRunsPage(pageSize, page * pageSize).then((result) => {
      if (!mounted) return;
      setPageRuns(result.runs);
      setTotal(result.total);
    }).catch(() => {
      if (!mounted || page !== 0) return;
      setPageRuns(snapshot?.runs ?? []);
      setTotal(snapshot?.runs?.length ?? 0);
    }).finally(() => { if (mounted) setLoading(false); });
    return () => { mounted = false; };
  }, [page, snapshot?.projectId]);
  const runs = pageRuns.length ? pageRuns.map(run => ({
    id: run.run_id,
    status: normalizeRunStatus(run.status),
    workflow: String(run.workflow || run.module || 'workflow'),
    started: run.created_at ? new Date(run.created_at).toLocaleString() : 'recently',
    duration: run.completed_at && run.created_at ? `${Math.max(0, (new Date(run.completed_at).getTime() - new Date(run.created_at).getTime()) / 1000).toFixed(1)}s` : 'running',
    passed: Number((run as any).passed ?? (run as any).tests_passed ?? 0),
    total: Number((run as any).total ?? (run as any).tests_total ?? 0),
  })) : [];
  const filtered = runs.filter((r) => {
    const matchSearch = r.id.includes(search) || r.workflow.includes(search);
    const matchStatus = statusFilter==="all" || r.status===statusFilter;
    return matchSearch && matchStatus;
  });
  return (
    <div className="p-5 space-y-4 overflow-y-auto h-full" style={{ scrollbarWidth:"none" }}>
      <div className="flex items-center gap-3 flex-wrap">
        <div className="flex items-center gap-2 bg-muted rounded px-3 py-1.5 flex-1 min-w-[180px] max-w-xs">
          <Search size={11} className="text-muted-foreground/60 flex-shrink-0"/>
          <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder={t('studio.common.searchRuns')} className="bg-transparent text-xs text-foreground placeholder:text-muted-foreground/50 outline-none w-full"/>
        </div>
        <div className="flex gap-1.5">
          {["all","success","warning","failed","running"].map((s) => {
            const cfg = s==="all" ? null : STATUS_CFG[s];
             return <button key={s} onClick={() => setStatusFilter(s)} className={`px-2.5 py-1.5 rounded text-xs capitalize transition-colors ${statusFilter===s?"bg-primary/15 border border-primary/30 text-primary":"bg-muted border border-border text-muted-foreground hover:text-foreground"}`}>{s === "all" ? t('studio.common.all') : t(`studio.status.${s}`, s)}</button>;
          })}
        </div>
          <span className="text-xs text-muted-foreground ml-auto">{filtered.length} / {total} {t('studio.dashboard.runs')}</span>
      </div>
      <div className="bg-card border border-border rounded-lg overflow-hidden">
        <div className="grid grid-cols-6 px-4 py-2.5 border-b border-border">
           {[t('studio.common.copyId'),t('studio.common.status'),t('studio.workflow.module'),t('studio.common.started'),t('studio.common.duration'),t('studio.common.tests')].map((h) => <span key={h} className="text-xs text-muted-foreground font-medium">{h}</span>)}
        </div>
        {filtered.map((r, i) => {
          const cfg = STATUS_CFG[r.status] ?? STATUS_CFG.idle;
          return (
            <div key={r.id} className={`grid grid-cols-6 px-4 py-3 hover:bg-white/3 transition-colors items-center cursor-pointer ${i<filtered.length-1?"border-b border-border":""}`}>
              <span className="text-xs font-mono text-foreground/75">{r.id}</span>
              <div><StatusBadge status={r.status}/></div>
              <span className="text-xs font-mono text-muted-foreground">{r.workflow}</span>
              <span className="text-xs text-muted-foreground">{r.started}</span>
              <span className="text-xs font-mono text-muted-foreground">{r.duration}</span>
              <span className={`text-xs font-medium ${cfg.text}`}>{r.passed}/{r.total}</span>
            </div>
          );
        })}
      </div>
      <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>{loading ? t('studio.common.loading', 'Loading…') : `${t('studio.common.showing')} ${filtered.length} / ${total} ${t('studio.common.totalRuns')}`}</span>
         <div className="flex items-center gap-2">
            <button onClick={() => setPage((value) => Math.max(0, value - 1))} disabled={loading || page === 0} className="px-2.5 py-1 bg-muted border border-border rounded hover:text-foreground transition-colors disabled:opacity-40">← {t('studio.common.prev')}</button>
           <span className="px-3 py-1 bg-primary/10 border border-primary/30 rounded text-primary">{page + 1}</span>
            <button onClick={() => setPage((value) => value + 1)} disabled={loading || (page + 1) * pageSize >= total} className="px-2.5 py-1 bg-muted border border-border rounded hover:text-foreground transition-colors disabled:opacity-40">{t('studio.common.next')} →</button>
        </div>
      </div>
    </div>
  );
}

// ─── Agent Detail View ────────────────────────────────────────────────────────
function AgentDetailView({ agent, onBack, snapshot }: { agent: AgentData; onBack: () => void; snapshot: StudioSnapshot | null }) {
  const [tab, setTab] = useState<"overview"|"tools"|"runs">("overview");
  const [actionState, setActionState] = useState("");
  const { t } = useTranslation();
  const description = agent.description === 'Registered by the backend agent registry.'
    ? t('studio.dashboard.registeredByBackend')
    : agent.description;
  function triggerAgent(mode: "full" | "resume") {
    setActionState(t('studio.common.loading', 'Queuing…'));
    const configured = snapshot?.providers?.[0];
    const provider = String(configured?.provider_id ?? configured?.id ?? configured?.type ?? 'mock');
    void runAgent(agent.id, 'studio', provider, mode).then((result) => {
      setActionState(`${t('studio.common.queued', 'Queued')} ${String(result.task_id ?? '')}`.trim());
    }).catch((error: unknown) => {
      setActionState(error instanceof Error ? error.message : t('studio.common.requestFailed', 'Request failed'));
    });
  }
  return (
    <div className="h-full overflow-y-auto" style={{ scrollbarWidth:"none" }}>
      <div className="sticky top-0 z-10 bg-background border-b border-border px-6 py-4">
        <button onClick={onBack} className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors mb-3"><ChevronLeft size={13}/> {t('studio.common.backDashboard')}</button>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center"><Bot size={16} className="text-primary"/></div>
            <div>
              <div className="flex items-center gap-2"><h1 className="text-lg font-semibold text-foreground">{agent.name}</h1><StatusBadge status={agent.status}/></div>
              <div className="text-xs text-muted-foreground">{agent.type} · {agent.model}</div>
            </div>
          </div>
          <div className="flex gap-2">
             <button data-testid="agent-restart" onClick={() => triggerAgent('resume')} disabled={actionState === t('studio.common.loading', 'Queuing…')} className="flex items-center gap-1.5 px-3 py-1.5 bg-muted rounded text-xs text-muted-foreground hover:text-foreground transition-colors disabled:opacity-40"><RotateCcw size={11}/> {t('studio.common.restart')}</button>
             <button data-testid="agent-run" onClick={() => triggerAgent('full')} disabled={actionState === t('studio.common.loading', 'Queuing…')} className="flex items-center gap-1.5 px-3 py-1.5 bg-primary/10 border border-primary/25 rounded text-xs text-primary hover:bg-primary/15 transition-colors disabled:opacity-40"><Play size={11}/> {t('studio.common.run')}</button>
           </div>
         </div>
         {actionState && <div role="status" className="mt-3 text-xs text-muted-foreground">{actionState}</div>}
       </div>
      <div className="p-6 space-y-5">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard icon={CheckCircle2} label={t('studio.settings.successRate')} value={`${agent.successRate}%`} accent="text-emerald-400"/>
          <StatCard icon={Activity}     label={t('studio.settings.totalRuns')}   value={agent.totalRuns.toLocaleString()}/>
          <StatCard icon={Brain}        label={t('studio.settings.memoryNodes')} value={agent.memoryNodes.toString()} accent="text-violet-400"/>
          <StatCard icon={Wrench}       label={t('studio.settings.tools')}        value={agent.tools.length.toString()}/>
        </div>
        <div className="bg-card border border-border rounded-lg p-5">
          <div className="text-xs text-muted-foreground mb-2 font-medium uppercase tracking-wider">{t('studio.settings.description')}</div>
           <p className="text-sm text-foreground/80 leading-relaxed">{description}</p>
        </div>
        <div>
          <div className="flex gap-0 border-b border-border mb-4">
             {(["overview","tools","runs"] as const).map((tabId) => (
               <button key={tabId} onClick={() => setTab(tabId)} className={`px-4 py-2 text-xs font-medium capitalize border-b-2 -mb-px transition-colors ${tab===tabId?"border-primary text-primary":"border-transparent text-muted-foreground hover:text-foreground"}`}>{tabId === 'overview' ? t('studio.common.overview') : tabId === 'tools' ? t('studio.common.tools') : t('studio.common.runs')}</button>
            ))}
          </div>
          {tab==="overview" && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div className="bg-card border border-border rounded-lg p-4">
                <div className="text-xs text-muted-foreground mb-3 font-medium uppercase tracking-wider">{t('studio.settings.configuration')}</div>
                <div className="space-y-2.5">
                  {[[t('studio.settings.model'),agent.model],[t('studio.settings.agentId'),agent.id],[t('studio.settings.type'),agent.type],[t('studio.settings.lastActive'),agent.lastRun],[t('studio.settings.memoryScope'),'workflow-scoped'],[t('studio.settings.maxTokens'),'32,768']].map(([l,v]) => (
                    <div key={l} className="flex justify-between items-center"><span className="text-xs text-muted-foreground">{l}</span><span className="text-xs font-mono text-foreground/70">{v}</span></div>
                  ))}

                </div>
              </div>
              <div className="bg-card border border-border rounded-lg p-4">
                <div className="text-xs text-muted-foreground mb-3 font-medium uppercase tracking-wider">{t('studio.settings.capabilities')}</div>
                <div className="space-y-2">
                   {[t('studio.settings.capabilityToolInvocation'),t('studio.settings.capabilityMemory'),t('studio.settings.capabilityParallel'),t('studio.settings.capabilityDispatch'),t('studio.settings.capabilitySynthesis')].map((cap) => (
                    <div key={cap} className="flex items-center gap-2 text-xs"><CheckCircle2 size={12} className="text-emerald-400"/><span className="text-foreground/70">{cap}</span></div>
                  ))}
                </div>
              </div>
            </div>
          )}
          {tab==="tools" && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {agent.tools.map((tool) => (
                <div key={tool} className="bg-card border border-border rounded-lg p-4 flex items-center gap-3">
                  <div className="w-8 h-8 rounded bg-muted flex items-center justify-center flex-shrink-0"><Wrench size={13} className="text-muted-foreground"/></div>
                  <div><div className="text-sm font-medium text-foreground">{tool}</div><div className="text-xs text-muted-foreground">{t('studio.settings.toolReady')}</div></div>
                  <CheckCircle2 size={13} className="text-emerald-400 ml-auto"/>
                </div>
              ))}
            </div>
          )}
          {tab==="runs" && (
            <div className="bg-card border border-border rounded-lg overflow-hidden">
               <div className="grid grid-cols-5 px-4 py-2.5 border-b border-border">{[t('studio.common.copyId'),t('studio.common.status'),t('studio.common.started'),t('studio.common.duration'),t('studio.common.tests')].map((h) => <span key={h} className="text-xs text-muted-foreground font-medium">{h}</span>)}</div>
              {(snapshot?.runs ?? []).filter((run) => !agent.id || String(run.agent ?? "") === agent.id).map((run, i, runs) => {
                const status = normalizeRunStatus(run.status);
                const cfg = STATUS_CFG[status] ?? STATUS_CFG.idle;
                return <div key={run.run_id} className={`grid grid-cols-5 px-4 py-3 hover:bg-white/3 transition-colors ${i<runs.length-1?"border-b border-border":""}`}><span className="text-xs font-mono text-foreground/70">{run.run_id}</span><span className={`text-xs font-medium ${cfg.text}`}>{cfg.label}</span><span className="text-xs text-muted-foreground">{run.created_at ? new Date(run.created_at).toLocaleString() : "—"}</span><span className="text-xs font-mono text-muted-foreground">{run.completed_at && run.created_at ? `${((new Date(run.completed_at).getTime() - new Date(run.created_at).getTime()) / 1000).toFixed(1)}s` : "—"}</span><span className="text-xs font-mono text-muted-foreground">{String((run as any).tests_passed ?? "—")}/{String((run as any).tests_total ?? "—")}</span></div>;
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── Settings View ────────────────────────────────────────────────────────────
function SettingsView({ snapshot }: { snapshot: StudioSnapshot | null }) {
  const { t, i18n } = useTranslation();
  const app = useSettingsStore((state) => state.app);
  const updateApp = useSettingsStore((state) => state.updateApp);
  const themes = [
    { id:"mahotsukai", swatch:"bg-cyan-400", label:t("studio.theme.mahotsukai"), sub:t("studio.theme.mahotsukaiSub") },
    { id:"alice", swatch:"bg-violet-400", label:t("studio.theme.alice"), sub:t("studio.theme.aliceSub") },
    { id:"aoko", swatch:"bg-blue-500", label:t("studio.theme.aoko"), sub:t("studio.theme.aokoSub") },
    { id:"soujuurou", swatch:"bg-emerald-500", label:t("studio.theme.soujuurou"), sub:t("studio.theme.soujuurouSub") },
  ];
  const providers = snapshot?.providers?.map((provider) => ({
    id:String(provider.provider_id ?? provider.id ?? provider.name),
    label:String(provider.name ?? provider.provider_id ?? t('studio.settings.provider')),
    org:String(provider.type ?? provider.provider_type ?? "Model provider"),
    badge:String(provider.status ?? ""),
  })) ?? [];
  return (
    <div className="p-6 space-y-6 overflow-y-auto h-full max-w-3xl" style={{ scrollbarWidth:"none" }}>
      <div>
        <h2 className="text-sm font-semibold text-foreground mb-1">{t("studio.settings.appearance")}</h2>
        <p className="text-xs text-muted-foreground mb-4">{t("studio.settings.appearanceDesc")}</p>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-4">
          {themes.map((t) => (
            <button key={t.id} onClick={() => updateApp({ theme:t.id })} aria-pressed={app.theme===t.id} className={`text-left p-3 rounded-lg border transition-all ${app.theme===t.id?"border-primary/50 bg-primary/8":"border-border bg-card hover:border-border/70"}`}>
              <div className={`w-6 h-6 rounded-full ${t.swatch} mb-2 opacity-80`}/>
              <div className="text-xs font-semibold text-foreground">{t.label}</div>
              <div className="text-xs text-muted-foreground">{t.sub}</div>
            </button>
          ))}
        </div>
        <div className="flex items-center justify-between p-3 bg-card border border-border rounded-lg">
          <div><div className="text-xs font-medium text-foreground">{app.darkMode ? t("studio.settings.darkMode") : t("studio.settings.lightMode")}</div><div className="text-xs text-muted-foreground">{t("studio.settings.themeHint")}</div></div>
          <button type="button" role="switch" aria-checked={app.darkMode} onClick={() => updateApp({ darkMode:!app.darkMode })} className={`w-10 h-5 border rounded-full relative transition-colors ${app.darkMode ? "bg-primary/20 border-primary/30" : "bg-muted border-border"}`}>
            <span className={`absolute top-0.5 w-4 h-4 rounded-full transition-all ${app.darkMode ? "right-0.5 bg-primary" : "left-0.5 bg-muted-foreground/50"}`}/>
          </button>
        </div>
      </div>
      <div className="h-px bg-border"/>
      <div>
        <h2 className="text-sm font-semibold text-foreground mb-1">{t("studio.settings.language")}</h2>
        <div className="flex gap-2 mt-3">
          {[{id:"en",label:"English"},{id:"zh",label:"中文"}].map((l) => (
            <button key={l.id} onClick={() => { i18n.changeLanguage(l.id); updateApp({ language:l.id }); }} className={`px-4 py-2 rounded-lg border text-sm transition-colors ${i18n.language===l.id?"bg-primary/10 border-primary/30 text-primary":"bg-card border-border text-muted-foreground hover:text-foreground"}`}>{l.label}</button>
          ))}
        </div>
      </div>
      <div className="h-px bg-border"/>
      <div>
        <h2 className="text-sm font-semibold text-foreground mb-1">{t("studio.settings.provider")}</h2>
        <p className="text-xs text-muted-foreground mb-4">{t('studio.settings.providerDesc')}</p>
        <div className="grid grid-cols-2 gap-3 mb-4">
            {providers.map((p) => (
            <button key={p.id} onClick={() => updateApp({ provider:p.id })} className={`text-left p-3 rounded-lg border transition-all ${app.provider===p.id?"border-primary/50 bg-primary/8":"border-border bg-card hover:border-border/70"}`}>
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-semibold text-foreground">{p.label}</span>
                {p.badge && <span className="text-xs text-emerald-400">{p.badge}</span>}
              </div>
              <div className="text-xs text-muted-foreground">{p.org}</div>
            </button>
          ))}
        </div>
        <div className="space-y-3">
          <div>
             <label className="text-xs text-muted-foreground block mb-1">{t('studio.settings.apiKey')}</label>
              <input type="password" value="" placeholder={t("studio.settings.backendManaged")} readOnly className="w-full px-3 py-2 bg-muted border border-border rounded text-xs text-foreground font-mono outline-none"/>
          </div>
        </div>
      </div>
      <div className="h-px bg-border"/>
      <div>
        <h2 className="text-sm font-semibold text-foreground mb-1">{t("studio.settings.budget")}</h2>
         <div className="grid grid-cols-2 gap-4">
             <div className="text-xs text-muted-foreground">{t("studio.settings.backendManaged")}</div>
        </div>
        <div className="flex items-center justify-between mt-4 p-3 bg-card border border-border rounded-lg">
           <span className="text-xs text-muted-foreground">{t("studio.settings.costThisRun")}</span>
           <span className="text-xs font-mono text-[#f0c040]">{snapshot?.productKpi?.this_week?.total_cost != null ? `$${Number(snapshot.productKpi.this_week.total_cost).toFixed(4)}` : "—"}</span>
        </div>
      </div>
        <div className="text-xs text-muted-foreground">{t("studio.settings.backendManaged")}</div>
    </div>
  );
}

// ─── Sidebar ──────────────────────────────────────────────────────────────────
const NAV_GROUPS = [
  { label:"CORE",         items:[{ id:"dashboard",     label:"Dashboard",    icon:LayoutDashboard }] },
  { label:"RUN",          items:[
    { id:"workflow",    label:"Workflow",     icon:GitBranch },
    { id:"execution",   label:"Execution",    icon:Activity },
    { id:"kanban",      label:"Kanban",       icon:Layers },
    { id:"inspector",   label:"Run Inspector",icon:Eye },
  ]},
  { label:"QUALITY",      items:[
    { id:"reports",     label:"Reports",      icon:BarChart2 },
    { id:"gaps",        label:"Gap Discovery",icon:AlertTriangle },
  ]},
  { label:"KNOWLEDGE",    items:[
    { id:"memory",      label:"Memory",       icon:Brain },

    { id:"knowledge",   label:"Knowledge Base",icon:Database },
    { id:"graph",       label:"Knowledge Graph",icon:Network },
    { id:"artifacts",   label:"Artifacts",    icon:Box },
  ]},
  { label:"INTELLIGENCE", items:[{ id:"chat", label:"Intelligence Chat", icon:MessageSquare }] },
  { label:"MONITOR",      items:[
    { id:"observability",label:"Observability",icon:Gauge },
    { id:"history",      label:"Run History",  icon:History },
  ]},
];

function Sidebar({ view, onNav, snapshot }: { view: View; onNav: (v: View) => void; snapshot: StudioSnapshot | null }) {
  const { t, i18n } = useTranslation();
  const runningCount = snapshot?.runs.filter((run) => normalizeRunStatus(run.status) === "running").length ?? 0;
  return (
    <aside className="w-52 flex-shrink-0 bg-sidebar border-r border-sidebar-border flex flex-col">
      <div className="px-4 py-5 border-b border-sidebar-border">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-md bg-primary/15 border border-primary/25 flex items-center justify-center"><Layers size={14} className="text-primary"/></div>
          <div>
            <div className="text-sm font-semibold text-foreground leading-none">Alice</div>
            <div className="text-xs text-muted-foreground/50 leading-none mt-0.5" style={{ fontFamily:"serif" }}>{t("studio.brand_subtitle")}</div>
          </div>
        </div>
      </div>
      <div className="px-3 py-2.5 border-b border-sidebar-border">
        <div className="flex items-center gap-2 bg-cyan-400/8 border border-cyan-400/15 rounded px-2.5 py-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse flex-shrink-0"/>
          <span className="text-xs text-cyan-400 font-medium">{t("studio.runningAgents", "{{count}} agents running", { count:runningCount })}</span>
        </div>
      </div>
      <nav className="flex-1 overflow-y-auto py-2" style={{ scrollbarWidth:"none" }}>
        {NAV_GROUPS.map((group) => (
          <div key={group.label} className="mb-1">
            <div className="px-3 pt-3 pb-1">
              <span className="text-[9px] font-semibold uppercase tracking-[0.12em] text-muted-foreground/40">{t(`studio.nav.${group.label.toLowerCase()}`, group.label)}</span>
            </div>
            <div className="px-2 space-y-0.5">
              {group.items.map(({ id, label, icon: Icon }) => {
                const isActive = view===id;
                return (
                  <button key={id} onClick={() => onNav(id as View)} className={`flex items-center gap-2.5 w-full px-3 py-2 rounded text-[13px] transition-all text-left ${isActive?"bg-primary/10 text-primary border-l-2 border-primary pl-[10px]":"text-muted-foreground hover:text-foreground hover:bg-white/4"}`}>
                    <Icon size={13} className="flex-shrink-0"/>
                    <span className="truncate">{t(`studio.nav.${id}`, label)}</span>
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </nav>
      <div className="px-2 pb-3 border-t border-sidebar-border pt-2 space-y-0.5">
        <button onClick={() => onNav("settings")} className={`flex items-center gap-2.5 w-full px-3 py-2 rounded text-[13px] transition-all text-left ${view==="settings"?"bg-primary/10 text-primary border-l-2 border-primary pl-[10px]":"text-muted-foreground hover:text-foreground hover:bg-white/4"}`}>
          <Settings size={13} className="flex-shrink-0"/><span>{t("studio.nav.settings", "Settings")}</span>
        </button>
        <div className="flex items-center gap-2.5 px-3 py-2 mt-1">
          <div className="w-6 h-6 rounded-full bg-primary/20 border border-primary/30 flex items-center justify-center flex-shrink-0"><span className="text-xs font-semibold text-primary">A</span></div>
          <div className="min-w-0"><div className="text-xs font-medium text-foreground/70 truncate">alice@lab.dev</div><div className="text-xs text-muted-foreground/50">{i18n.language.startsWith('zh') ? '管理员' : 'Admin'}</div></div>
        </div>
      </div>
    </aside>
  );
}

// ─── TopBar ───────────────────────────────────────────────────────────────────
const VIEW_TITLES: Record<string,string> = {
  dashboard:"Dashboard", workflow:"Workflow Builder", execution:"Execution Center",
  kanban:"Kanban Board", inspector:"Run Inspector", reports:"Reports",
  gaps:"Gap Discovery", memory:"Memory Explorer", knowledge:"Knowledge Base",
  graph:"Knowledge Graph", artifacts:"Artifacts", chat:"Intelligence Chat",
   observability:"Observability", history:"Run History", settings:"Settings", agent:"Agent Detail", onboarding:"New Project",
};

function TopBar({ view, onCreateProject, notifications, notificationsUnread, notificationsLoading, notificationsError, onMarkNotificationRead }: { view: View; onCreateProject: () => void; notifications: StudioNotification[]; notificationsUnread: number; notificationsLoading: boolean; notificationsError: string; onMarkNotificationRead: (id: string) => void }) {
  const { t } = useTranslation();
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  return (
    <header className="relative h-12 flex-shrink-0 flex items-center px-5 gap-4 border-b border-border bg-background/80 backdrop-blur-sm">
         <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
           <span className="text-muted-foreground/50">Alice</span><ChevronRight size={11}/><ProjectSelector onCreateProject={onCreateProject}/><ChevronRight size={11}/><span className="text-foreground/70">{view === 'onboarding' ? t('onboarding.wizard_title') : t(`studio.titles.${view}`, VIEW_TITLES[view] ?? view)}</span>
      </div>
      <div className="flex items-center gap-2 bg-muted rounded px-3 py-1.5 ml-4 w-52">
        <Search size={11} className="text-muted-foreground/60 flex-shrink-0"/>
        <input placeholder={t("studio.common.search", "Search…")} className="bg-transparent text-xs text-foreground placeholder:text-muted-foreground/50 outline-none w-full"/>
        <kbd className="text-xs text-muted-foreground/40 font-mono">⌘K</kbd>
      </div>
      <div className="ml-auto flex items-center gap-3">
         <span className="text-xs text-muted-foreground font-mono hidden md:block">{new Date().toLocaleTimeString()}</span>
        <div className="h-3.5 w-px bg-border"/>
         <button data-testid="notifications-button" aria-label={t('studio.common.notifications', 'Notifications')} aria-expanded={notificationsOpen} onClick={() => setNotificationsOpen((value) => !value)} className="relative p-1.5 text-muted-foreground hover:text-foreground transition-colors rounded">
           <Bell size={14}/>
            {notificationsUnread > 0 && <span className="absolute -top-0.5 -right-0.5 min-w-3.5 h-3.5 px-0.5 rounded-full bg-amber-400 text-[9px] leading-3.5 text-black text-center">{notificationsUnread}</span>}
          </button>
          {notificationsOpen && <div data-testid="notifications-panel" role="dialog" className="pointer-events-none absolute right-5 top-10 z-30 w-80 rounded-lg border border-border bg-card p-4 shadow-xl">
            <div className="pointer-events-auto text-xs font-semibold text-foreground">{t('studio.common.notifications', 'Notifications')}</div>
            {notificationsLoading && <div className="mt-3 text-xs text-muted-foreground">{t('studio.common.loading', 'Loading…')}</div>}
            {!notificationsLoading && notificationsError && <div role="alert" className="mt-3 text-xs text-destructive">{notificationsError}</div>}
            {!notificationsLoading && !notificationsError && notifications.length === 0 && <div className="mt-3 text-xs text-muted-foreground">{t('studio.common.noNotifications', 'No new notifications')}</div>}
            {!notificationsLoading && !notificationsError && notifications.length > 0 && <div className="mt-3 space-y-2">{notifications.slice(0, 5).map((item) => <button type="button" key={item.id} data-testid={`notification-${item.id}`} onClick={() => onMarkNotificationRead(item.id)} className={`pointer-events-auto w-full text-left rounded border border-border/70 p-2 ${item.read ? 'bg-muted/20 opacity-70' : 'bg-muted/30'}`}><div className="text-xs font-medium text-foreground">{item.title}{!item.read && <span className="ml-1 text-amber-400">•</span>}</div><div className="mt-1 text-[11px] text-muted-foreground line-clamp-2">{item.message}</div></button>)}</div>}
          </div>}
      </div>
    </header>
  );
}

// ─── App Root ─────────────────────────────────────────────────────────────────
export default function DesignStudioApp() {
  const [view, setView] = useState<View>("dashboard");
  const [selectedAgent, setSelectedAgent] = useState<AgentData|null>(null);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [snapshotRefreshToken, setSnapshotRefreshToken] = useState(0);
  const appSettings = useSettingsStore((state) => state.app);
  const { i18n, t } = useTranslation();
  const projectInit = useProjectStore((state) => state.init);
  const activeProjectId = useProjectStore((state) => state.activeId);
  const studioSnapshot = useStudioSnapshot(activeProjectId, snapshotRefreshToken);
  const [notifications, setNotifications] = useState<StudioNotification[]>([]);
  const [notificationsUnread, setNotificationsUnread] = useState(0);
  const [notificationsLoading, setNotificationsLoading] = useState(false);
  const [notificationsError, setNotificationsError] = useState("");

  useEffect(() => {
    let mounted = true;
    setNotificationsLoading(true);
    setNotificationsError("");
    void listNotifications(20, activeProjectId || '').then((data) => { if (mounted) { setNotifications(data.notifications); setNotificationsUnread(data.unread); } }).catch((error: unknown) => { if (mounted) { setNotifications([]); setNotificationsUnread(0); setNotificationsError(error instanceof Error ? error.message : t('studio.common.requestFailed', 'Request failed')); } }).finally(() => { if (mounted) setNotificationsLoading(false); });
    return () => { mounted = false; };
  }, [activeProjectId, snapshotRefreshToken, t]);

  const handleMarkNotificationRead = (id: string) => {
    void markNotificationRead(id, activeProjectId || '').then(() => {
      setNotifications((items) => items.map((item) => item.id === id ? { ...item, read: true } : item));
      setNotificationsUnread((count) => Math.max(0, count - 1));
    }).catch(() => { /* keep the notification unread when persistence fails */ });
  };

  useEffect(() => { projectInit(); }, [projectInit]);

  useEffect(() => {
    const theme = appSettings.theme || "mahotsukai";
    document.documentElement.setAttribute("data-theme", theme);
    document.documentElement.classList.toggle("dark", appSettings.darkMode);
    if (i18n.language !== appSettings.language) void i18n.changeLanguage(appSettings.language);
    document.documentElement.lang = appSettings.language.startsWith("zh") ? "zh-CN" : "en";
    localStorage.setItem("tlo-theme-name", theme);
    localStorage.setItem("tlo-theme", appSettings.darkMode ? "dark" : "light");
  }, [appSettings.theme, appSettings.darkMode, appSettings.language, i18n.language, i18n]);

  useEffect(() => {
    if (!selectedRunId && studioSnapshot?.runs?.[0]?.run_id) setSelectedRunId(studioSnapshot.runs[0].run_id);
  }, [selectedRunId, studioSnapshot]);

  useEffect(() => {
    setSelectedRunId(null);
    setSelectedAgent(null);
  }, [activeProjectId]);

  function handleSelectAgent(agent: AgentData) {
    setSelectedAgent(agent);
    setView("agent");
  }

  function handleNav(v: View) {
    if (v!=="agent") setSelectedAgent(null);
    setView(v);
  }

  return (
    <div className="flex h-screen overflow-hidden bg-background text-foreground" style={{ fontFamily:"Inter, system-ui, sans-serif" }}>
      <Sidebar view={view} onNav={handleNav} snapshot={studioSnapshot}/>
      <div className="flex-1 flex flex-col overflow-hidden">
        <TopBar view={view} onCreateProject={() => setView("onboarding")} notifications={notifications} notificationsUnread={notificationsUnread} notificationsLoading={notificationsLoading} notificationsError={notificationsError} onMarkNotificationRead={handleMarkNotificationRead}/>
        <main className="flex-1 overflow-hidden">
          <div className="h-full">
               {view==="onboarding"  && <OnboardingWizardView/>}
               {view==="dashboard"    && <DashboardView onSelectAgent={handleSelectAgent} onViewHistory={() => handleNav("history")} snapshot={studioSnapshot}/>}
               {view==="workflow"     && <WorkflowBuilderView snapshot={studioSnapshot} onSaved={() => setSnapshotRefreshToken((value) => value + 1)}/>}
              {view==="execution"    && <ExecutionView snapshot={studioSnapshot}/>}
                {view==="kanban"       && <KanbanView snapshot={studioSnapshot} projectId={activeProjectId} onRefresh={() => setSnapshotRefreshToken((value) => value + 1)}/>}
               {view==="inspector"    && (selectedRunId || studioSnapshot?.runs?.[0]?.run_id ? <RunInspectorView runId={selectedRunId ?? studioSnapshot?.runs?.[0]?.run_id as string}/> : <div className="p-6 text-xs text-muted-foreground">{t("studio.common.noData")}</div>)}
              {view==="reports"      && <ReportsView snapshot={studioSnapshot}/>}
               {view==="gaps"         && <GapsView snapshot={studioSnapshot} onRefresh={() => setSnapshotRefreshToken((value) => value + 1)}/>}
              {view==="memory"       && <MemoryView snapshot={studioSnapshot}/>}
              {view==="knowledge"    && <KnowledgeView snapshot={studioSnapshot}/>}
              {view==="graph"        && <KnowledgeGraphView snapshot={studioSnapshot}/>}
              {view==="artifacts"    && <ArtifactsView snapshot={studioSnapshot}/>}
              {view==="chat"         && <ChatView/>}
               {view==="observability"&& <ObservabilityView snapshot={studioSnapshot} onRefresh={() => setSnapshotRefreshToken((value) => value + 1)}/>}
              {view==="history"      && <HistoryView snapshot={studioSnapshot}/>}
              {view==="settings"     && <SettingsView snapshot={studioSnapshot}/>}
              {view==="agent"        && selectedAgent && <AgentDetailView agent={selectedAgent} snapshot={studioSnapshot} onBack={() => handleNav("dashboard")}/>}
            </div>
        </main>
      </div>
    </div>
  );
}
