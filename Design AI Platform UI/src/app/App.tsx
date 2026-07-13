import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  LayoutDashboard, GitBranch, Activity, Brain, Wrench,
  History, Settings, Search, Bell, CheckCircle2, XCircle,
  Clock, Cpu, Zap, Network, Plus, MoreHorizontal,
  AlertTriangle, ChevronDown, Circle, Server, Tag,
  Terminal, Eye, Bot, Filter, Play, RotateCcw, Copy,
  ChevronLeft, Database, Hash, Layers, ArrowRight,
  ChevronRight, MessageSquare, FileText, BarChart2,
  Gauge, Box, Send, Download, File, Image, Code2,
  FileJson, X, RefreshCw, ZoomIn, ZoomOut,
} from "lucide-react";

// ─── Types ───────────────────────────────────────────────────────────────────
type View =
  | "dashboard" | "workflow" | "execution" | "kanban" | "inspector"
  | "reports"   | "gaps"     | "memory"    | "knowledge" | "graph"
  | "artifacts" | "chat"     | "observability" | "history"
  | "settings"  | "agent";

type AgentStatus = "idle" | "running" | "success" | "failed" | "warning";

interface AgentData {
  id: string; name: string; type: string; status: AgentStatus;
  lastRun: string; successRate: number; totalRuns: number;
  model: string; tools: string[]; description: string; memoryNodes: number;
}

// ─── Data ─────────────────────────────────────────────────────────────────────
const AGENTS: AgentData[] = [
  { id: "alice-core",    name: "Alice-Core",       type: "Orchestrator",  status: "running",
    lastRun: "2m ago",  successRate: 98.2, totalRuns: 1847, model: "claude-sonnet-4-6",
    tools: ["TestRunner","BrowserDriver","APIClient","FileSystem"],
    description: "Primary orchestration agent. Coordinates multi-agent test workflows and manages execution state.", memoryNodes: 342 },
  { id: "test-runner",   name: "Test Runner",       type: "Execution",     status: "running",
    lastRun: "Now",     successRate: 96.4, totalRuns: 3241, model: "claude-haiku-4-5",
    tools: ["Jest","Playwright","Vitest","Coverage"],
    description: "Executes unit and integration tests. Parses results and surfaces failures with full context.", memoryNodes: 218 },
  { id: "browser-driver",name: "Browser Driver",    type: "Execution",     status: "running",
    lastRun: "Now",     successRate: 91.7, totalRuns: 2108, model: "claude-haiku-4-5",
    tools: ["Playwright","Screenshot","NetworkInterceptor","DOMQuery"],
    description: "Controls headless browser sessions for E2E testing and visual regression.", memoryNodes: 156 },
  { id: "api-validator", name: "API Validator",     type: "Validation",    status: "success",
    lastRun: "14m ago", successRate: 99.1, totalRuns: 4520, model: "claude-haiku-4-5",
    tools: ["OpenAPI","HTTPClient","SchemaValidator","Diff"],
    description: "Validates REST and GraphQL API contracts. Auto-generates test cases from OpenAPI specs.", memoryNodes: 289 },
  { id: "report-gen",    name: "Report Generator", type: "Analysis",      status: "idle",
    lastRun: "1h ago",  successRate: 100,  totalRuns: 892,  model: "claude-sonnet-4-6",
    tools: ["Markdown","Chart","Email","S3"],
    description: "Synthesizes execution results into structured reports. Identifies regression patterns.", memoryNodes: 94 },
  { id: "scheduler",     name: "Scheduler",         type: "Infrastructure",status: "idle",
    lastRun: "5m ago",  successRate: 97.8, totalRuns: 6103, model: "claude-haiku-4-5",
    tools: ["CronJob","Queue","Webhook","Notify"],
    description: "Manages execution schedules, trigger queues, and workflow dispatch.", memoryNodes: 185 },
];

const LOG_ENTRIES = [
  { ts: "14:32:01.847", level: "info",    msg: "Workflow execution started: workflow-9f2a3b", ctx: "alice-core" },
  { ts: "14:32:01.901", level: "debug",   msg: "Loading agent configuration: alice-core v2.1.4", ctx: "system" },
  { ts: "14:32:02.134", level: "info",    msg: "Alice-Core initialized. Dispatching parallel subtasks.", ctx: "alice-core" },
  { ts: "14:32:02.567", level: "info",    msg: "Test Runner activated. Queue depth: 12 suites", ctx: "test-runner" },
  { ts: "14:32:02.601", level: "info",    msg: "Browser Driver activated. Browser: chromium 121.0", ctx: "browser-driver" },
  { ts: "14:32:03.445", level: "info",    msg: "Running suite: auth.spec.ts — 12 tests", ctx: "test-runner" },
  { ts: "14:32:04.221", level: "success", msg: "✓ auth.login.success — 234ms", ctx: "test-runner" },
  { ts: "14:32:04.489", level: "success", msg: "✓ auth.login.invalid_credentials — 198ms", ctx: "test-runner" },
  { ts: "14:32:04.801", level: "success", msg: "✓ auth.logout.session_clear — 156ms", ctx: "test-runner" },
  { ts: "14:32:05.112", level: "info",    msg: "Navigating to /dashboard for visual baseline", ctx: "browser-driver" },
  { ts: "14:32:05.678", level: "debug",   msg: "Screenshot: dashboard-baseline.png (1920×1080, 847KB)", ctx: "browser-driver" },
  { ts: "14:32:06.334", level: "success", msg: "✓ api.users.list — 112ms", ctx: "test-runner" },
  { ts: "14:32:06.712", level: "warning", msg: "⚠ api.users.create — 1847ms (threshold: 1500ms)", ctx: "test-runner" },
  { ts: "14:32:07.001", level: "debug",   msg: "Memory snapshot: 48 episodic nodes updated", ctx: "alice-core" },
  { ts: "14:32:07.234", level: "info",    msg: "Form interaction: 6/9 steps complete", ctx: "browser-driver" },
  { ts: "14:32:07.891", level: "success", msg: "✓ api.users.update — 89ms", ctx: "test-runner" },
  { ts: "14:32:08.102", level: "success", msg: "✓ api.users.delete — 94ms", ctx: "test-runner" },
  { ts: "14:32:08.780", level: "success", msg: "✓ auth.spec.ts — 12 passed, 0 failed", ctx: "test-runner" },
  { ts: "14:32:09.001", level: "info",    msg: "Form interaction: 9/9 steps complete.", ctx: "browser-driver" },
  { ts: "14:32:09.445", level: "debug",   msg: "Network: POST /api/checkout 200 (341ms)", ctx: "browser-driver" },
];

const MEMORY_BLOCKS = [
  { id: 1, type: "episodic",   title: "Auth Flow Run #3241",         tokens: 847,  age: "2m",  tags: ["auth","test"] },
  { id: 2, type: "semantic",   title: "API Rate Limit Behavior",     tokens: 312,  age: "1h",  tags: ["api","constraint"] },
  { id: 3, type: "procedural", title: "Browser Form Interaction",    tokens: 1240, age: "14m", tags: ["browser","e2e"] },
  { id: 4, type: "semantic",   title: "Auth Token Expiry Pattern",   tokens: 201,  age: "6h",  tags: ["auth","session"] },
  { id: 5, type: "episodic",   title: "Dashboard Load Regression",   tokens: 634,  age: "3h",  tags: ["regression","perf"] },
  { id: 6, type: "procedural", title: "OpenAPI Spec Validation",     tokens: 892,  age: "30m", tags: ["api","schema"] },
  { id: 7, type: "semantic",   title: "Test Timeout Heuristics",     tokens: 445,  age: "2d",  tags: ["timeout","config"] },
  { id: 8, type: "episodic",   title: "Visual Regression Baseline",  tokens: 2108, age: "1d",  tags: ["visual","snapshot"] },
  { id: 9, type: "procedural", title: "CI Pipeline Integration",     tokens: 567,  age: "4h",  tags: ["ci","pipeline"] },
];

const RECENT_RUNS = [
  { id: "run-a8f2c4", status: "success", workflow: "workflow-auth",    started: "2m ago",  duration: "3.2s", passed: 12, total: 12 },
  { id: "run-9e1b83", status: "warning", workflow: "workflow-auth",    started: "14m ago", duration: "4.8s", passed: 7,  total: 8  },
  { id: "run-7d3f91", status: "success", workflow: "workflow-api",     started: "1h ago",  duration: "5.1s", passed: 20, total: 20 },
  { id: "run-6c2a45", status: "failed",  workflow: "workflow-auth",    started: "2h ago",  duration: "1.2s", passed: 3,  total: 12 },
  { id: "run-5b8e72", status: "success", workflow: "workflow-browser", started: "3h ago",  duration: "8.7s", passed: 9,  total: 9  },
];

const ALL_RUNS = [
  ...RECENT_RUNS,
  { id: "run-4d7e21", status: "success", workflow: "workflow-api",     started: "5h ago",  duration: "4.3s", passed: 20, total: 20 },
  { id: "run-3c9f15", status: "warning", workflow: "workflow-auth",    started: "8h ago",  duration: "6.2s", passed: 10, total: 12 },
  { id: "run-2b4a03", status: "success", workflow: "workflow-browser", started: "1d ago",  duration: "7.1s", passed: 9,  total: 9  },
  { id: "run-1a8b91", status: "failed",  workflow: "workflow-api",     started: "1d ago",  duration: "2.4s", passed: 15, total: 20 },
  { id: "run-0z7c84", status: "success", workflow: "workflow-auth",    started: "2d ago",  duration: "3.8s", passed: 12, total: 12 },
];

const KANBAN_PHASES = ["Project Init","Requirements","Planning","Design","Development","Testing","Integration","Review","Knowledge"];

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
interface WFNodeDef { id: string; cx: number; cy: number; label: string; sub: string; status: "completed"|"running"|"pending"|"failed" }
interface WFEdgeDef { d: string; status: "completed"|"active"|"pending" }

const WF_NODES: WFNodeDef[] = [
  { id: "trigger",  cx: 90,  cy: 160, label: "Trigger",       sub: "Cron Schedule",   status: "completed" },
  { id: "core",     cx: 270, cy: 160, label: "Alice-Core",    sub: "Orchestrator",    status: "completed" },
  { id: "tests",    cx: 470, cy: 90,  label: "Test Runner",   sub: "Execution Agent", status: "completed" },
  { id: "browser",  cx: 470, cy: 230, label: "Browser Driver",sub: "E2E Agent",       status: "running"   },
  { id: "validate", cx: 660, cy: 160, label: "Validator",     sub: "Validation",      status: "pending"   },
  { id: "end",      cx: 830, cy: 160, label: "Complete",      sub: "Report Gen",      status: "pending"   },
];

const WF_EDGES: WFEdgeDef[] = [
  { d: "M 160,160 L 200,160",               status: "completed" },
  { d: "M 340,160 C 375,160 400,90 400,90", status: "completed" },
  { d: "M 340,160 C 375,160 400,230 400,230",status: "active"   },
  { d: "M 540,90 C 575,90 590,160 590,160", status: "pending"   },
  { d: "M 540,230 C 575,230 590,160 590,160",status: "pending"  },
  { d: "M 730,160 L 760,160",               status: "pending"   },
];

function WorkflowGraph({ selectedNode, onSelectNode }: { selectedNode: string|null; onSelectNode: (id: string) => void }) {
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
      {WF_EDGES.map((e, i) => {
        const ec = edgeColors[e.status];
        return <path key={i} d={e.d} fill="none" stroke={ec.stroke} strokeWidth="1.5" className={e.status==="active"?"ef":""} markerEnd={ec.marker}/>;
      })}
      {WF_NODES.map((n) => {
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
  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-medium ${cfg.bg} ${cfg.text} border ${cfg.border}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot} ${status==="running"?"animate-pulse":""}`}/>
      {cfg.label}
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
  return (
    <button onClick={onClick} className="bg-card border border-border rounded-lg p-4 text-left hover:border-primary/30 transition-all group w-full">
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="flex items-center gap-1.5 mb-1">
            <Bot size={11} className="text-muted-foreground"/><span className="text-xs text-muted-foreground">{agent.type}</span>
          </div>
          <div className="text-sm font-semibold text-foreground">{agent.name}</div>
        </div>
        <StatusBadge status={agent.status}/>
      </div>
      <p className="text-xs text-muted-foreground leading-relaxed line-clamp-2 mb-3">{agent.description}</p>
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1"><CheckCircle2 size={11} className="text-emerald-500"/>{agent.successRate}%</span>
          <span className="flex items-center gap-1"><Activity size={11}/>{agent.totalRuns.toLocaleString()} runs</span>
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

function LogStream({ entries, filter }: { entries: typeof LOG_ENTRIES; filter: string }) {
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

function SOPStepper() {
  return (
    <div className="flex items-center gap-0 overflow-x-auto" style={{ scrollbarWidth:"none" }}>
      {SOP_PHASES.map((p, i) => {
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
                {p.label}
              </span>
            </div>
            {i < SOP_PHASES.length-1 && (
              <div className={`h-px w-6 flex-shrink-0 mb-4 ${isComplete ? "bg-emerald-400/40" : "bg-border"}`}/>
            )}
          </div>
        );
      })}
    </div>
  );
}

// ─── Dashboard View ───────────────────────────────────────────────────────────
function DashboardView({ onSelectAgent }: { onSelectAgent: (a: AgentData) => void }) {
  return (
    <div className="p-6 space-y-5 max-w-[1400px] overflow-y-auto h-full" style={{ scrollbarWidth:"none" }}>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={Bot}          label="Active Agents"   value={`${AGENTS.filter(a=>a.status==="running").length} / ${AGENTS.length}`} sub="3 running workflows" accent="text-cyan-400"/>
        <StatCard icon={GitBranch}    label="Workflows Today" value="14"    sub="↑ 3 from yesterday"  accent="text-primary"/>
        <StatCard icon={CheckCircle2} label="Success Rate"    value="94.2%" sub="Last 30 days"         accent="text-emerald-400"/>
        <StatCard icon={Brain}        label="Memory Nodes"    value="1,284" sub="48 updated this run"  accent="text-violet-400"/>
      </div>
      <div className="bg-cyan-400/5 border border-cyan-400/20 rounded-lg px-5 py-3 flex items-center gap-4">
        <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"/><span className="text-sm font-medium text-cyan-400">Execution in progress</span>
        <span className="text-xs text-muted-foreground font-mono">workflow-9f2a3b</span>
        <div className="flex items-center gap-3 ml-auto text-xs text-muted-foreground">
          <span className="flex items-center gap-1"><Clock size={11}/> 7.8s elapsed</span>
          <span className="flex items-center gap-1"><Activity size={11}/> 3 agents active</span>
        </div>
      </div>
      <div className="grid grid-cols-1 xl:grid-cols-[1fr_300px] gap-5">
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-foreground">Agent Registry</h2>
            <span className="text-xs text-muted-foreground">{AGENTS.length} agents</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {AGENTS.map((a) => <AgentCard key={a.id} agent={a} onClick={() => onSelectAgent(a)}/>)}
          </div>
        </div>
        <div className="space-y-4">
          <div>
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-semibold text-foreground">Recent Runs</h2>
              <button className="text-xs text-muted-foreground hover:text-foreground transition-colors">View all</button>
            </div>
            <div className="bg-card border border-border rounded-lg overflow-hidden">
              {RECENT_RUNS.map((r, i) => {
                const cfg = STATUS_CFG[r.status] ?? STATUS_CFG.idle;
                return (
                  <div key={r.id} className={`flex items-center gap-3 px-4 py-3 hover:bg-white/4 transition-colors ${i<RECENT_RUNS.length-1?"border-b border-border":""}`}>
                    <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${cfg.dot}`}/>
                    <div className="flex-1 min-w-0">
                      <div className="text-xs font-mono text-foreground/70">{r.id}</div>
                      <div className="text-xs text-muted-foreground mt-0.5">{r.started} · {r.duration}</div>
                    </div>
                    <div className={`text-xs font-medium ${cfg.text}`}>{r.passed}/{r.total}</div>
                  </div>
                );
              })}
            </div>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-foreground mb-3">System Health</h3>
            <div className="bg-card border border-border rounded-lg divide-y divide-border">
              {[{label:"API Gateway",status:"Healthy",dot:"bg-emerald-400"},{label:"Memory Store",status:"2.1 GB",dot:"bg-cyan-400"},{label:"Task Queue",status:"4 pending",dot:"bg-amber-400"},{label:"Model API",status:"< 200ms",dot:"bg-emerald-400"}].map((r) => (
                <div key={r.label} className="flex items-center justify-between px-4 py-2.5">
                  <div className="flex items-center gap-2"><span className={`w-1.5 h-1.5 rounded-full ${r.dot}`}/><span className="text-xs text-muted-foreground">{r.label}</span></div>
                  <span className="text-xs font-mono text-foreground/70">{r.status}</span>
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
function WorkflowBuilderView() {
  const [selNode, setSelNode] = useState<string|null>("browser");
  const [wfName, setWfName] = useState("");
  const [wfDesc, setWfDesc] = useState("");
  const existingWFs = [
    { name:"workflow-auth",    status:"running",  updated:"2m ago",  nodes:6 },
    { name:"workflow-api",     status:"success",  updated:"1h ago",  nodes:4 },
    { name:"workflow-browser", status:"idle",     updated:"1d ago",  nodes:5 },
  ];
  return (
    <div className="flex h-full overflow-hidden">
      <div className="w-72 border-r border-border flex flex-col flex-shrink-0">
        <div className="p-4 border-b border-border">
          <div className="text-sm font-semibold text-foreground mb-3">New Workflow</div>
          <div className="space-y-3">
            <div>
              <label className="text-xs text-muted-foreground mb-1 block">Name</label>
              <input value={wfName} onChange={(e) => setWfName(e.target.value)} placeholder="workflow-name" className="w-full px-3 py-2 bg-muted border border-border rounded text-xs text-foreground placeholder:text-muted-foreground/50 outline-none focus:border-primary/50 font-mono"/>
            </div>
            <div>
              <label className="text-xs text-muted-foreground mb-1 block">Description</label>
              <textarea value={wfDesc} onChange={(e) => setWfDesc(e.target.value)} placeholder="Describe this workflow..." rows={3} className="w-full px-3 py-2 bg-muted border border-border rounded text-xs text-foreground placeholder:text-muted-foreground/50 outline-none focus:border-primary/50 resize-none"/>
            </div>
            <div>
              <label className="text-xs text-muted-foreground mb-2 block">Agents</label>
              <div className="flex flex-wrap gap-1.5">
                {AGENTS.slice(0,4).map((a) => (
                  <span key={a.id} className="px-2 py-0.5 bg-primary/10 border border-primary/25 rounded text-xs text-primary font-mono cursor-pointer hover:bg-primary/20 transition-colors">{a.name}</span>
                ))}
              </div>
            </div>
            <div className="flex gap-2 pt-1">
              <button className="flex-1 py-2 bg-muted border border-border rounded text-xs text-muted-foreground hover:text-foreground transition-colors">Save Draft</button>
              <button className="flex-1 py-2 bg-primary/10 border border-primary/30 rounded text-xs text-primary hover:bg-primary/20 transition-colors">Publish</button>
            </div>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto p-4" style={{ scrollbarWidth:"none" }}>
          <div className="text-xs text-muted-foreground mb-3 font-medium uppercase tracking-wider">Existing Workflows</div>
          <div className="space-y-2">
            {existingWFs.map((w) => {
              const cfg = STATUS_CFG[w.status] ?? STATUS_CFG.idle;
              return (
                <div key={w.name} className="bg-card border border-border rounded-lg p-3 hover:border-border/80 transition-colors cursor-pointer">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-mono text-foreground/80 truncate">{w.name}</span>
                    <span className={`text-xs font-medium ${cfg.text}`}>{cfg.label}</span>
                  </div>
                  <div className="flex items-center gap-3 text-xs text-muted-foreground">
                    <span>{w.nodes} nodes</span><span>{w.updated}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="flex items-center gap-3 px-5 py-3 border-b border-border flex-shrink-0">
          <span className="text-xs font-mono text-muted-foreground">workflow-9f2a3b</span>
          <StatusBadge status="running"/>
          <div className="ml-auto flex gap-2">
            <button className="flex items-center gap-1.5 px-3 py-1.5 bg-muted rounded text-xs text-muted-foreground hover:text-foreground transition-colors"><RotateCcw size={11}/> Replay</button>
            <button className="flex items-center gap-1.5 px-3 py-1.5 bg-primary/10 border border-primary/25 rounded text-xs text-primary hover:bg-primary/15 transition-colors"><Eye size={11}/> Inspect</button>
          </div>
        </div>
        <div className="flex-1 flex items-center justify-center p-6">
          <WorkflowGraph selectedNode={selNode} onSelectNode={setSelNode}/>
        </div>
      </div>
    </div>
  );
}

// ─── Execution Center View ────────────────────────────────────────────────────
function ExecutionView() {
  const [logFilter, setLogFilter] = useState("all");
  const [selNode, setSelNode] = useState<string|null>(null);
  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Control bar */}
      <div className="flex items-center gap-4 px-5 py-3 border-b border-border flex-shrink-0">
        <div className="flex items-center gap-2 bg-muted rounded px-3 py-1.5">
          <span className="text-xs text-muted-foreground">Module:</span>
          <span className="text-xs font-medium text-foreground font-mono">authentication</span>
          <ChevronDown size={11} className="text-muted-foreground"/>
        </div>
        <div className="flex items-center gap-2 bg-muted rounded px-3 py-1.5">
          <span className="text-xs text-muted-foreground">Mode:</span>
          <span className="text-xs font-medium text-foreground">Full SOP</span>
          <ChevronDown size={11} className="text-muted-foreground"/>
        </div>
        <div className="flex items-center gap-2 ml-auto">
          <StatusBadge status="running"/>
          <button className="flex items-center gap-1.5 px-3 py-1.5 bg-amber-400/10 border border-amber-400/25 rounded text-xs text-amber-400 hover:bg-amber-400/15 transition-colors"><RotateCcw size={11}/> Pause</button>
          <button className="flex items-center gap-1.5 px-3 py-1.5 bg-red-400/10 border border-red-400/25 rounded text-xs text-red-400 hover:bg-red-400/15 transition-colors"><X size={11}/> Cancel</button>
        </div>
      </div>
      {/* SOP Stepper */}
      <div className="px-5 py-4 border-b border-border flex-shrink-0 bg-card/50">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-muted-foreground font-medium">SOP Progress</span>
          <span className="text-xs font-mono text-cyan-400">Phase 6/9 — Testing</span>
        </div>
        <SOPStepper/>
      </div>
      {/* Main content: graph + logs */}
      <div className="flex-1 flex overflow-hidden">
        <div className="flex-1 flex flex-col overflow-hidden border-r border-border">
          <div className="px-4 py-2.5 border-b border-border flex-shrink-0">
            <span className="text-xs font-semibold text-foreground">Live Agent Graph</span>
          </div>
          <div className="flex-1 flex items-center justify-center p-4">
            <WorkflowGraph selectedNode={selNode} onSelectNode={setSelNode}/>
          </div>
        </div>
        <div className="w-[420px] flex flex-col flex-shrink-0">
          <div className="flex items-center gap-3 px-4 py-2.5 border-b border-border flex-shrink-0">
            <Terminal size={12} className="text-muted-foreground"/>
            <span className="text-xs font-semibold text-foreground">Agent Terminal</span>
            <div className="ml-auto flex gap-1">
              {["all","info","warning","debug"].map((f) => (
                <button key={f} onClick={() => setLogFilter(f)} className={`px-2 py-0.5 rounded text-xs transition-colors ${logFilter===f?"bg-primary/15 text-primary":"text-muted-foreground hover:text-foreground"}`}>{f}</button>
              ))}
            </div>
          </div>
          <div className="flex-1 overflow-hidden bg-muted/30">
            <LogStream entries={LOG_ENTRIES} filter={logFilter}/>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Kanban Board View ────────────────────────────────────────────────────────
function KanbanView() {
  return (
    <div className="h-full flex flex-col overflow-hidden">
      <div className="flex items-center gap-3 px-5 py-3 border-b border-border flex-shrink-0">
        <span className="text-sm font-semibold text-foreground">Kanban Board</span>
        <span className="text-xs text-muted-foreground">— SOP Phase Overview</span>
        <div className="ml-auto flex items-center gap-2">
          <span className="text-xs text-muted-foreground">{KANBAN_MODULES.length} modules</span>
          <button className="flex items-center gap-1.5 px-3 py-1.5 bg-primary/10 border border-primary/25 rounded text-xs text-primary hover:bg-primary/15 transition-colors"><Plus size={11}/> Add Module</button>
        </div>
      </div>
      <div className="flex-1 overflow-x-auto overflow-y-hidden" style={{ scrollbarWidth:"thin" }}>
        <div className="flex gap-3 p-4 h-full min-w-max">
          {KANBAN_PHASES.map((phase) => {
            const cards = KANBAN_MODULES.filter((m) => m.phase===phase);
            const isActive = phase==="Testing";
            return (
              <div key={phase} className={`w-48 flex flex-col rounded-lg border flex-shrink-0 ${isActive?"border-cyan-400/25 bg-cyan-400/5":"border-border bg-card/50"}`}>
                <div className="px-3 py-2.5 border-b border-border flex items-center justify-between">
                  <span className={`text-xs font-semibold ${isActive?"text-cyan-400":"text-foreground/70"}`}>{phase}</span>
                  <span className={`text-xs px-1.5 py-0.5 rounded font-mono ${isActive?"bg-cyan-400/15 text-cyan-400":"bg-muted text-muted-foreground"}`}>{cards.length}</span>
                </div>
                <div className="flex-1 overflow-y-auto p-2 space-y-2" style={{ scrollbarWidth:"none" }}>
                  {cards.map((m) => {
                    const cfg = STATUS_CFG[m.status] ?? STATUS_CFG.idle;
                    return (
                      <div key={m.id} className={`bg-card border rounded-md p-3 cursor-pointer hover:border-primary/30 transition-colors ${cfg.border}`}>
                        <div className="flex items-center justify-between mb-2">
                          <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${cfg.dot} ${m.status==="running"?"animate-pulse":""}`}/>
                          <span className={`text-xs ${cfg.text}`}>{cfg.label}</span>
                        </div>
                        <div className="text-xs font-semibold text-foreground mb-2 leading-tight">{m.name}</div>
                        <div className="flex items-center gap-2 text-xs text-muted-foreground">
                          <span>{m.pages}p</span>
                          <span>{m.artifacts} artifacts</span>
                        </div>
                      </div>
                    );
                  })}
                  {cards.length===0 && <div className="text-xs text-muted-foreground/40 text-center py-4">Empty</div>}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

// ─── Run Inspector View ───────────────────────────────────────────────────────
function RunInspectorView() {
  const [tab, setTab] = useState("timeline");
  const TABS = ["Timeline","Artifacts","Agent Calls","Metrics","Logs","Report"];
  const kpis = [
    { label:"Duration",  value:"8.4s",        icon:Clock },
    { label:"Module",    value:"auth",         icon:Box },
    { label:"Agent",     value:"alice-core",   icon:Bot },
    { label:"Tokens",    value:"24,891",       icon:Zap },
    { label:"Cost",      value:"$0.032",       icon:Tag },
    { label:"Artifacts", value:"6",            icon:FileText },
    { label:"Pages",     value:"12",           icon:Layers },
    { label:"Tests",     value:"12/12",        icon:CheckCircle2 },
  ];
  const artifactsList = ARTIFACTS_DATA.slice(0,6);
  const agentCalls = [
    { agent:"Alice-Core",    prompt:"Analyze test results and dispatch subtasks for authentication module...", tokens:1847, status:"success" },
    { agent:"Test Runner",   prompt:"Execute test suite auth.spec.ts and return structured results...", tokens:12340, status:"success" },
    { agent:"Browser Driver",prompt:"Navigate to /dashboard, capture baseline screenshot, then execute checkout flow...", tokens:10704, status:"running" },
  ];
  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-4 px-5 py-3 border-b border-border flex-shrink-0">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-foreground font-mono">run-a8f2c4</span>
            <StatusBadge status="running"/>
          </div>
          <div className="text-xs text-muted-foreground mt-0.5 font-mono">Started 14:32:01 · workflow-auth · alice-core v2.1.4</div>
        </div>
        <div className="ml-auto flex gap-2">
          <button className="flex items-center gap-1.5 px-3 py-1.5 bg-muted rounded text-xs text-muted-foreground hover:text-foreground transition-colors"><Copy size={11}/> Copy ID</button>
          <button className="flex items-center gap-1.5 px-3 py-1.5 bg-muted rounded text-xs text-muted-foreground hover:text-foreground transition-colors"><Download size={11}/> Export</button>
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
        {TABS.map((t) => (
          <button key={t} onClick={() => setTab(t.toLowerCase().replace(" ","-"))} className={`px-4 py-2.5 text-xs font-medium border-b-2 -mb-px transition-colors ${tab===t.toLowerCase().replace(" ","-")?"border-primary text-primary":"border-transparent text-muted-foreground hover:text-foreground"}`}>{t}</button>
        ))}
      </div>
      {/* Tab content */}
      <div className="flex-1 overflow-hidden">
        <AnimatePresence mode="wait">
          <motion.div key={tab} initial={{opacity:0,y:4}} animate={{opacity:1,y:0}} exit={{opacity:0}} transition={{duration:0.12}} className="h-full overflow-y-auto p-5" style={{ scrollbarWidth:"none" }}>
            {tab==="timeline" && (
              <div>
                <div className="text-xs text-muted-foreground mb-4">Swimlane Timeline — 3 agents · 0–10s</div>
                <svg viewBox="0 0 800 180" className="w-full rounded-lg bg-card border border-border" style={{ fontFamily:"Inter, sans-serif" }}>
                  {/* Time axis */}
                  {[0,2,4,6,8,10].map((t) => {
                    const x = 120 + t*(680/10);
                    return <g key={t}><line x1={x} y1="20" x2={x} y2="170" stroke="rgba(50,90,180,0.1)" strokeWidth="1"/><text x={x} y="15" textAnchor="middle" fontSize="9" fill="#4e6a92">{t}s</text></g>;
                  })}
                  {/* Agent rows */}
                  {[
                    { label:"Alice-Core",    y:40,  start:0,   end:1.2,  color:"#4a7cf7",  running:false },
                    { label:"Test Runner",   y:90,  start:0.8, end:10,   color:"#22d3ee",  running:true  },
                    { label:"Browser Driver",y:140, start:0.8, end:10,   color:"#34d399",  running:true  },
                  ].map((row) => {
                    const x1 = 120 + row.start*(680/10);
                    const w = (row.end - row.start)*(680/10);
                    return (
                      <g key={row.label}>
                        <text x="4" y={row.y+5} fontSize="10" fill="#4e6a92" dominantBaseline="middle">{row.label}</text>
                        <rect x={x1} y={row.y-10} width={w} height="22" rx="3" fill={row.color} opacity={row.running?".6":".4"}/>
                        {row.running && <rect x={x1+w-20} y={row.y-10} width="20" height="22" rx="3" fill={row.color} opacity=".9" className="ef"/>}
                      </g>
                    );
                  })}
                </svg>
              </div>
            )}
            {tab==="artifacts" && (
              <div className="space-y-2">
                {artifactsList.map((a) => (
                  <div key={a.name} className="flex items-center gap-3 bg-card border border-border rounded-lg px-4 py-3 hover:border-border/80 transition-colors group">
                    <FileText size={14} className="text-muted-foreground flex-shrink-0"/>
                    <div className="flex-1 min-w-0">
                      <div className="text-xs font-mono text-foreground">{a.name}</div>
                      <div className="text-xs text-muted-foreground mt-0.5">{a.size} · {a.age}</div>
                    </div>
                    <span className="px-1.5 py-0.5 bg-muted rounded text-xs text-muted-foreground font-mono">{a.module}</span>
                    <div className="flex gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button className="p-1.5 bg-muted rounded hover:bg-card transition-colors"><Download size={11} className="text-muted-foreground"/></button>
                      <button className="p-1.5 bg-muted rounded hover:bg-card transition-colors"><Copy size={11} className="text-muted-foreground"/></button>
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
                  <StatCard icon={CheckCircle2} label="Pass Rate"   value="92%"   accent="text-emerald-400"/>
                  <StatCard icon={Zap}          label="Avg Duration" value="0.34s" accent="text-cyan-400"/>
                </div>
                <div className="bg-card border border-border rounded-lg p-4">
                  <div className="text-xs text-muted-foreground mb-3 font-medium uppercase tracking-wider">Phase Breakdown</div>
                  <div className="space-y-3">
                    {SOP_PHASES.slice(0,6).map((p) => {
                      const pct = p.status==="success" ? 100 : p.status==="running" ? 65 : 0;
                      return (
                        <div key={p.id}>
                          <div className="flex justify-between text-xs mb-1">
                            <span className="text-muted-foreground">{p.label}</span>
                            <span className="font-mono text-foreground/70">{pct}%</span>
                          </div>
                          <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                            <div className={`h-full rounded-full ${p.status==="success"?"bg-emerald-400":p.status==="running"?"bg-cyan-400 animate-pulse":"bg-muted"}`} style={{ width:`${pct}%` }}/>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            )}
            {tab==="logs" && <div className="h-80 flex flex-col bg-card border border-border rounded-lg overflow-hidden"><LogStream entries={LOG_ENTRIES} filter="all"/></div>}
            {tab==="report" && (
              <div className="bg-card border border-border rounded-lg p-5 space-y-4">
                <div className="flex items-center gap-2 text-xs text-muted-foreground mb-2"><Cpu size={11}/><span>AI-generated report · run-a8f2c4</span></div>
                <h3 className="text-sm font-semibold text-foreground">Execution Summary</h3>
                <p className="text-sm text-foreground/80 leading-relaxed">The authentication module completed with <strong className="text-emerald-400">92% pass rate</strong> (11/12 tests passing). One warning was raised for slow API response on user creation endpoint (1847ms vs 1500ms threshold).</p>
                <h4 className="text-sm font-semibold text-foreground">Key Findings</h4>
                <ul className="space-y-2 text-sm text-foreground/80">
                  {["Login flow: fully covered and performing within SLA","Token management: 94% coverage, expiry edge cases need attention","Session handling: 78% coverage — recommend additional negative test cases","API performance: user.create endpoint exceeds latency threshold"].map((f,i) => (
                    <li key={i} className="flex items-start gap-2"><ArrowRight size={12} className="text-muted-foreground flex-shrink-0 mt-0.5"/>{f}</li>
                  ))}
                </ul>
              </div>
            )}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
}

// ─── Reports View ─────────────────────────────────────────────────────────────
function ReportsView() {
  return (
    <div className="p-6 space-y-5 overflow-y-auto h-full" style={{ scrollbarWidth:"none" }}>
      <div className="grid grid-cols-3 gap-4">
        <StatCard icon={CheckCircle2} label="Pass Rate"    value="94.2%" sub="+1.3% from last week" accent="text-emerald-400"/>
        <StatCard icon={BarChart2}    label="Coverage"     value="87.3%" sub="↑ 2.1% this sprint"   accent="text-[#f0c040]"/>
        <StatCard icon={AlertTriangle}label="Open Defects" value="3"     sub="1 high · 2 medium"    accent="text-amber-400"/>
      </div>
      <div className="bg-card border border-border rounded-lg overflow-hidden">
        <div className="px-4 py-3 border-b border-border flex items-center justify-between">
          <span className="text-sm font-semibold text-foreground">Recent Test Runs</span>
          <button className="flex items-center gap-1.5 px-3 py-1.5 bg-muted rounded text-xs text-muted-foreground hover:text-foreground transition-colors"><Download size={11}/> Export</button>
        </div>
        <div>
          <div className="grid grid-cols-5 px-4 py-2 border-b border-border">
            {["Module","Status","Tests","Coverage","Date"].map((h) => <span key={h} className="text-xs text-muted-foreground font-medium">{h}</span>)}
          </div>
          {[
            { module:"Authentication", status:"success", tests:"12/12", cov:"87.3%", date:"2m ago"  },
            { module:"API Gateway",    status:"warning", tests:"7/8",   cov:"91.2%", date:"14m ago" },
            { module:"Dashboard UI",  status:"success", tests:"20/20", cov:"82.1%", date:"1h ago"  },
            { module:"Browser Flow",  status:"success", tests:"9/9",   cov:"76.4%", date:"3h ago"  },
            { module:"User Mgmt",     status:"failed",  tests:"3/12",  cov:"45.0%", date:"2h ago"  },
          ].map((r, i, arr) => {
            const cfg = STATUS_CFG[r.status] ?? STATUS_CFG.idle;
            return (
              <div key={r.module} className={`grid grid-cols-5 px-4 py-3 hover:bg-white/3 transition-colors ${i<arr.length-1?"border-b border-border":""}`}>
                <span className="text-xs text-foreground/80">{r.module}</span>
                <span className={`text-xs font-medium ${cfg.text}`}>{cfg.label}</span>
                <span className="text-xs font-mono text-foreground/70">{r.tests}</span>
                <span className="text-xs font-mono text-foreground/70">{r.cov}</span>
                <span className="text-xs text-muted-foreground">{r.date}</span>
              </div>
            );
          })}
        </div>
      </div>
      <div className="bg-card border border-border rounded-lg p-4">
        <div className="text-xs text-muted-foreground mb-3 font-medium uppercase tracking-wider">Top Failing Tests</div>
        {[
          { name:"api.users.create", reason:"Response time 1847ms (threshold 1500ms)", module:"authentication" },
          { name:"user.profile.update", reason:"Assertion failed: 404 Not Found", module:"user-management" },
          { name:"search.debounce", reason:"Timing-dependent failure (flaky)", module:"search" },
        ].map((t) => (
          <div key={t.name} className="flex items-start gap-3 py-2.5 border-b last:border-0 border-border">
            <XCircle size={13} className="text-red-400 flex-shrink-0 mt-0.5"/>
            <div>
              <div className="text-xs font-mono text-foreground/80">{t.name}</div>
              <div className="text-xs text-muted-foreground mt-0.5">{t.reason}</div>
            </div>
            <span className="ml-auto text-xs px-1.5 py-0.5 bg-muted rounded font-mono text-muted-foreground">{t.module}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Gap Discovery View ───────────────────────────────────────────────────────
function GapsView() {
  const [filter, setFilter] = useState("all");
  const types = ["all","Missing Tests","Missing Types","Insufficient Coverage","Flaky","Untested Components"];
  const filtered = filter==="all" ? GAPS : GAPS.filter((g) => g.type===filter);
  return (
    <div className="p-6 space-y-5 overflow-y-auto h-full" style={{ scrollbarWidth:"none" }}>
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold text-foreground">Gap Discovery</h2>
          <p className="text-xs text-muted-foreground mt-0.5">{GAPS.length} gaps identified — last scan 14m ago</p>
        </div>
        <button className="flex items-center gap-1.5 px-3 py-1.5 bg-primary/10 border border-primary/25 rounded text-xs text-primary hover:bg-primary/15 transition-colors"><RefreshCw size={11}/> Re-scan</button>
      </div>
      <div className="flex gap-2 flex-wrap">
        {types.map((t) => (
          <button key={t} onClick={() => setFilter(t)} className={`px-3 py-1.5 rounded text-xs transition-colors ${filter===t?"bg-primary/15 border border-primary/30 text-primary":"bg-muted border border-border text-muted-foreground hover:text-foreground"}`}>{t}</button>
        ))}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        {filtered.map((g) => {
          const sv = SEV_CFG[g.severity];
          return (
            <div key={g.id} className="bg-card border border-border rounded-lg p-4 hover:border-border/80 transition-colors">
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
                <button className="px-2.5 py-1 bg-primary/10 border border-primary/25 rounded text-xs text-primary hover:bg-primary/15 transition-colors">Create Task</button>
                <button className="px-2.5 py-1 bg-muted border border-border rounded text-xs text-muted-foreground hover:text-foreground transition-colors">Ignore</button>
                <button className="px-2.5 py-1 bg-muted border border-border rounded text-xs text-muted-foreground hover:text-foreground transition-colors">Archive</button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ─── Memory Explorer View ─────────────────────────────────────────────────────
function MemoryView() {
  const [selected, setSelected] = useState<number|null>(1);
  const [search, setSearch] = useState("");
  const total = MEMORY_BLOCKS.reduce((a, m) => a+m.tokens, 0);
  const filtered = MEMORY_BLOCKS.filter((m) => m.title.toLowerCase().includes(search.toLowerCase()) || m.tags.some((t) => t.includes(search.toLowerCase())));
  const sel = MEMORY_BLOCKS.find((m) => m.id===selected);
  return (
    <div className="flex h-full overflow-hidden">
      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="px-5 py-3.5 border-b border-border flex items-center gap-4 flex-shrink-0">
          <div className="flex items-center gap-2 bg-muted rounded px-3 py-1.5 flex-1 max-w-xs">
            <Search size={11} className="text-muted-foreground/60 flex-shrink-0"/>
            <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search memory…" className="bg-transparent text-xs text-foreground placeholder:text-muted-foreground/50 outline-none w-full"/>
          </div>
          <div className="flex items-center gap-3 text-xs text-muted-foreground ml-auto">
            {(["episodic","semantic","procedural"] as const).map((type) => {
              const count = MEMORY_BLOCKS.filter((m) => m.type===type).length;
              const mc = MEM_CFG[type];
              return <div key={type} className="flex items-center gap-1.5"><span className={`w-2 h-2 rounded-sm ${mc.bg} border ${mc.border}`}/><span className={mc.color}>{mc.label}</span><span className="text-muted-foreground">{count}</span></div>;
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
                    <span className={`text-xs px-1.5 py-0.5 rounded ${mc.bg} ${mc.color} border ${mc.border} font-medium`}>{mc.label}</span>
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
            <span className={`text-xs px-1.5 py-0.5 rounded ${MEM_CFG[sel.type as keyof typeof MEM_CFG].bg} ${MEM_CFG[sel.type as keyof typeof MEM_CFG].color} border ${MEM_CFG[sel.type as keyof typeof MEM_CFG].border} font-medium`}>{MEM_CFG[sel.type as keyof typeof MEM_CFG].label}</span>
            <div className="text-sm font-semibold text-foreground mt-2">{sel.title}</div>
          </div>
          <div className="p-4 space-y-2.5 border-b border-border text-xs">
            {[["Tokens",sel.tokens.toString()],["Age",sel.age+" ago"],["ID",`mem-${String(sel.id).padStart(4,"0")}`],["Associations","3 nodes"]].map(([l,v]) => (
              <div key={l} className="flex justify-between"><span className="text-muted-foreground">{l}</span><span className="text-foreground/70 font-mono">{v}</span></div>
            ))}
          </div>
          <div className="p-4">
            <div className="text-xs text-muted-foreground mb-2 font-medium uppercase tracking-wider">Tags</div>
            <div className="flex flex-wrap gap-1.5">{sel.tags.map((t) => <span key={t} className="px-1.5 py-0.5 bg-muted rounded text-xs text-muted-foreground font-mono">#{t}</span>)}</div>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Knowledge Base View ──────────────────────────────────────────────────────
function KnowledgeView() {
  const collections = [
    { name:"test-knowledge", docs:892,  updated:"2m ago",  status:"ready" },
    { name:"api-specs",      docs:241,  updated:"1h ago",  status:"ready" },
    { name:"defect-patterns",docs:151,  updated:"3h ago",  status:"ready" },
  ];
  return (
    <div className="p-6 space-y-5 overflow-y-auto h-full" style={{ scrollbarWidth:"none" }}>
      <div className="grid grid-cols-3 gap-4">
        <StatCard icon={Database}     label="Collections"  value="3"     accent="text-primary"/>
        <StatCard icon={FileText}     label="Documents"    value="1,284" sub="Total indexed"    accent="text-sky-400"/>
        <StatCard icon={CheckCircle2} label="ChromaDB"     value="● Online" sub="Response < 5ms" accent="text-emerald-400"/>
      </div>
      <div className="bg-card border border-border rounded-lg overflow-hidden">
        <div className="px-4 py-3 border-b border-border"><span className="text-sm font-semibold text-foreground">Collections</span></div>
        <div>
          <div className="grid grid-cols-4 px-4 py-2.5 border-b border-border">
            {["Name","Documents","Last Updated","Status"].map((h) => <span key={h} className="text-xs text-muted-foreground font-medium">{h}</span>)}
          </div>
          {collections.map((c, i) => (
            <div key={c.name} className={`grid grid-cols-4 px-4 py-3 hover:bg-white/3 transition-colors items-center ${i<collections.length-1?"border-b border-border":""}`}>
              <span className="text-xs font-mono text-foreground/80">{c.name}</span>
              <span className="text-xs font-mono text-foreground/70">{c.docs.toLocaleString()}</span>
              <span className="text-xs text-muted-foreground">{c.updated}</span>
              <StatusBadge status={c.status}/>
            </div>
          ))}
        </div>
      </div>
      <div className="bg-card border border-border rounded-lg p-4">
        <div className="text-xs text-muted-foreground mb-3 font-medium uppercase tracking-wider">Recent Additions</div>
        {["auth-token-patterns.json","api-rate-limit-cases.yaml","dashboard-component-specs.md","payment-edge-cases.md","session-management.json"].map((doc) => (
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
function KnowledgeGraphView() {
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
  ];
  const nodeColors = { module:"#4a7cf7", issue:"#f0c040", pattern:"#a78bfa" };
  return (
    <div className="p-6 space-y-4 overflow-y-auto h-full" style={{ scrollbarWidth:"none" }}>
      <div className="flex items-center justify-between">
        <div><h2 className="text-sm font-semibold text-foreground">Knowledge Graph</h2><p className="text-xs text-muted-foreground mt-0.5">15 nodes · 15 relationships</p></div>
        <div className="flex gap-2">
          <button className="flex items-center gap-1 px-2.5 py-1.5 bg-muted border border-border rounded text-xs text-muted-foreground hover:text-foreground transition-colors"><ZoomIn size={11}/></button>
          <button className="flex items-center gap-1 px-2.5 py-1.5 bg-muted border border-border rounded text-xs text-muted-foreground hover:text-foreground transition-colors"><ZoomOut size={11}/></button>
          <button className="px-2.5 py-1.5 bg-muted border border-border rounded text-xs text-muted-foreground hover:text-foreground transition-colors">Reset</button>
        </div>
      </div>
      <div className="bg-card border border-border rounded-lg overflow-hidden">
        <svg viewBox="0 0 800 380" className="w-full" style={{ fontFamily:"Inter, sans-serif" }}>
          <defs>
            <radialGradient id="bg-grad" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="rgba(74,124,247,0.03)"/>
              <stop offset="100%" stopColor="transparent"/>
            </radialGradient>
          </defs>
          <rect width="800" height="380" fill="url(#bg-grad)"/>
          {edges.map(([a,b]) => {
            const na = nodes.find((n) => n.id===a)!;
            const nb = nodes.find((n) => n.id===b)!;
            return <line key={`${a}-${b}`} x1={na.x} y1={na.y} x2={nb.x} y2={nb.y} stroke="rgba(50,90,180,0.2)" strokeWidth="1"/>;
          })}
          {nodes.map((n) => {
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
        {[{color:"#4a7cf7",label:"Module (6)"},{color:"#f0c040",label:"Issue (5)"},{color:"#a78bfa",label:"Pattern (4)"}].map(({ color,label }) => (
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
function ArtifactsView() {
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");
  const typeIcons: Record<string,React.ElementType> = { markdown:FileText, image:Image, json:FileJson, code:Code2, yaml:FileText, pdf:File };
  const typeColors: Record<string,string> = { markdown:"text-sky-400", image:"text-violet-400", json:"text-amber-400", code:"text-emerald-400", yaml:"text-orange-400", pdf:"text-red-400" };
  const types = ["all","markdown","json","image","code","yaml","pdf"];
  const filtered = ARTIFACTS_DATA.filter((a) => {
    const matchSearch = a.name.toLowerCase().includes(search.toLowerCase()) || a.module.toLowerCase().includes(search.toLowerCase());
    const matchType = typeFilter==="all" || a.type===typeFilter;
    return matchSearch && matchType;
  });
  return (
    <div className="p-5 space-y-4 overflow-y-auto h-full" style={{ scrollbarWidth:"none" }}>
      <div className="flex items-center gap-3 flex-wrap">
        <div className="flex items-center gap-2 bg-muted rounded px-3 py-1.5 flex-1 min-w-[180px] max-w-xs">
          <Search size={11} className="text-muted-foreground/60 flex-shrink-0"/>
          <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search artifacts…" className="bg-transparent text-xs text-foreground placeholder:text-muted-foreground/50 outline-none w-full"/>
        </div>
        <div className="flex gap-1.5 flex-wrap">
          {types.map((t) => <button key={t} onClick={() => setTypeFilter(t)} className={`px-2.5 py-1.5 rounded text-xs transition-colors ${typeFilter===t?"bg-primary/15 border border-primary/30 text-primary":"bg-muted border border-border text-muted-foreground hover:text-foreground"}`}>{t}</button>)}
        </div>
        <span className="text-xs text-muted-foreground ml-auto">{filtered.length} artifacts</span>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {filtered.map((a) => {
          const Icon = typeIcons[a.type] ?? File;
          const iconColor = typeColors[a.type] ?? "text-muted-foreground";
          return (
            <div key={a.name} className="bg-card border border-border rounded-lg p-4 hover:border-border/70 transition-colors group cursor-pointer">
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
                  <button className="p-1 bg-muted rounded hover:bg-secondary transition-colors" title="Download"><Download size={10} className="text-muted-foreground"/></button>
                  <button className="p-1 bg-muted rounded hover:bg-secondary transition-colors" title="Copy path"><Copy size={10} className="text-muted-foreground"/></button>
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
  const [input, setInput] = useState("");
  const [msgs, setMsgs] = useState(CHAT_MESSAGES);
  const sessions = [
    { id:1, title:"Auth module coverage", active:true,  time:"2m" },
    { id:2, title:"Risk assessment",       active:false, time:"1h" },
    { id:3, title:"Gap analysis sprint 4", active:false, time:"2d" },
  ];
  const suggestions = ["Show failing tests","Summarize last run","Find coverage gaps","Explain error"];

  function handleSend() {
    if (!input.trim()) return;
    setMsgs((m) => [...m, { id: m.length+1, role:"user", content:input }]);
    setInput("");
  }

  return (
    <div className="flex h-full overflow-hidden">
      <div className="w-44 border-r border-border flex flex-col flex-shrink-0 bg-sidebar">
        <div className="px-3 py-3 border-b border-border">
          <button className="flex items-center gap-1.5 w-full px-2.5 py-1.5 bg-primary/10 border border-primary/25 rounded text-xs text-primary hover:bg-primary/15 transition-colors"><Plus size={11}/> New Chat</button>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-1" style={{ scrollbarWidth:"none" }}>
          {sessions.map((s) => (
            <button key={s.id} className={`w-full text-left px-3 py-2 rounded text-xs transition-colors ${s.active?"bg-primary/10 text-primary":"text-muted-foreground hover:text-foreground hover:bg-white/4"}`}>
              <div className="truncate font-medium">{s.title}</div>
              <div className="text-muted-foreground/60 mt-0.5">{s.time} ago</div>
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
                    {(m.tools as string[]).map((t) => <span key={t} className="px-2 py-0.5 bg-muted border border-border rounded text-xs text-muted-foreground font-mono">⚙ {t}</span>)}
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
          <textarea value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => { if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();handleSend();}}} placeholder="Ask Alice about your tests, coverage, or agents…" rows={2} className="flex-1 bg-muted border border-border rounded-lg px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground/50 outline-none focus:border-primary/50 resize-none"/>
          <button onClick={handleSend} className="flex items-center gap-1.5 px-4 py-3 bg-primary/10 border border-primary/30 rounded-lg text-sm text-primary hover:bg-primary/20 transition-colors flex-shrink-0"><Send size={14}/></button>
        </div>
      </div>
    </div>
  );
}

// ─── Observability View ───────────────────────────────────────────────────────
function ObservabilityView() {
  const [tab, setTab] = useState("overview");
  return (
    <div className="h-full flex flex-col overflow-hidden">
      <div className="flex items-center gap-4 px-5 py-3 border-b border-border flex-shrink-0">
        <div className="flex gap-0 flex-1">
          {["overview","memory","threads","queue"].map((t) => (
            <button key={t} onClick={() => setTab(t)} className={`px-4 py-2 text-xs font-medium capitalize border-b-2 -mb-px transition-colors ${tab===t?"border-primary text-primary":"border-transparent text-muted-foreground hover:text-foreground"}`}>{t==="queue"?"Queue & WS":t==="threads"?"Threads & Tasks":t==="memory"?"Memory & GC":t}</button>
          ))}
        </div>
        <div className="flex items-center gap-2 text-xs text-muted-foreground ml-auto">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"/>
          <span>Auto-refresh 10s</span>
          <button className="p-1.5 bg-muted rounded hover:bg-secondary transition-colors"><RefreshCw size={11}/></button>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto p-5" style={{ scrollbarWidth:"none" }}>
        {tab==="overview" && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              <StatCard icon={Cpu}     label="RSS Memory" value="245 MB"  sub="of 512 MB"    accent="text-cyan-400"/>
              <StatCard icon={Network} label="Threads"    value="12"      sub="4 active"     accent="text-primary"/>
              <StatCard icon={Zap}     label="Active Tasks"value="3"      sub="4 queued"     accent="text-emerald-400"/>
              <StatCard icon={Server}  label="WS Conns"   value="7"       sub="2 active"     accent="text-violet-400"/>
            </div>
            <div className="bg-card border border-border rounded-lg divide-y divide-border">
              {[{label:"API Gateway",ok:true},{label:"ChromaDB",ok:true},{label:"Redis Queue",ok:true},{label:"WebSocket Server",ok:true},{label:"Model API (Anthropic)",ok:true}].map((r) => (
                <div key={r.label} className="flex items-center justify-between px-4 py-3">
                  <div className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-emerald-400"/><span className="text-xs text-muted-foreground">{r.label}</span></div>
                  <span className="text-xs font-medium text-emerald-400">Healthy</span>
                </div>
              ))}
            </div>
          </div>
        )}
        {tab==="memory" && (
          <div className="space-y-4">
            {[{label:"RSS Memory",used:245,total:512,unit:"MB"},{label:"VMS Memory",used:1200,total:4096,unit:"MB"}].map((m) => (
              <div key={m.label} className="bg-card border border-border rounded-lg p-4">
                <div className="flex justify-between text-xs mb-2"><span className="text-muted-foreground">{m.label}</span><span className="font-mono text-foreground/70">{m.used} / {m.total} {m.unit}</span></div>
                <div className="h-2 bg-muted rounded-full overflow-hidden"><div className="h-full bg-cyan-400/70 rounded-full" style={{ width:`${(m.used/m.total)*100}%` }}/></div>
              </div>
            ))}
            <div className="bg-card border border-border rounded-lg p-4">
              <div className="text-xs text-muted-foreground mb-3 font-medium uppercase tracking-wider">GC Generations</div>
              {[{gen:"Gen 0",count:1284},{gen:"Gen 1",count:12},{gen:"Gen 2",count:1}].map((g) => (
                <div key={g.gen} className="flex items-center justify-between py-2 border-b last:border-0 border-border">
                  <span className="text-xs text-muted-foreground">{g.gen}</span>
                  <span className="text-xs font-mono text-foreground/70">{g.count.toLocaleString()} collections</span>
                </div>
              ))}
            </div>
          </div>
        )}
        {tab==="threads" && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <StatCard icon={Cpu}   label="Total Threads" value="12" accent="text-primary"/>
              <StatCard icon={Zap}   label="Active"        value="4"  accent="text-cyan-400"/>
            </div>
            <div className="bg-card border border-border rounded-lg overflow-hidden">
              <div className="grid grid-cols-3 px-4 py-2.5 border-b border-border">{["Thread","Status","Task"].map((h) => <span key={h} className="text-xs text-muted-foreground font-medium">{h}</span>)}</div>
              {[{id:"Thread-1",status:"running",task:"workflow-9f2a3b/alice-core"},{id:"Thread-2",status:"running",task:"workflow-9f2a3b/test-runner"},{id:"Thread-3",status:"running",task:"workflow-9f2a3b/browser-driver"},{id:"Thread-4",status:"idle",task:"—"},{id:"Thread-5",status:"idle",task:"—"}].map((t,i,arr) => {
                const cfg = STATUS_CFG[t.status] ?? STATUS_CFG.idle;
                return <div key={t.id} className={`grid grid-cols-3 px-4 py-2.5 hover:bg-white/3 transition-colors ${i<arr.length-1?"border-b border-border":""}`}><span className="text-xs font-mono text-foreground/70">{t.id}</span><span className={`text-xs font-medium ${cfg.text}`}>{cfg.label}</span><span className="text-xs font-mono text-muted-foreground truncate">{t.task}</span></div>;
              })}
            </div>
          </div>
        )}
        {tab==="queue" && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              <StatCard icon={Server}  label="Queue Depth"  value="4"  accent="text-amber-400"/>
              <StatCard icon={Network} label="WS Active"    value="2"  accent="text-cyan-400"/>
              <StatCard icon={Zap}     label="Msg/sec (in)" value="12" accent="text-primary"/>
              <StatCard icon={Zap}     label="Msg/sec (out)"value="8"  accent="text-violet-400"/>
            </div>
            <div className="bg-card border border-border rounded-lg p-4">
              <div className="text-xs text-muted-foreground mb-3 font-medium uppercase tracking-wider">Queue Items</div>
              {[{id:"q-001",type:"workflow_dispatch",priority:"high"},{id:"q-002",type:"agent_task",priority:"normal"},{id:"q-003",type:"memory_write",priority:"low"},{id:"q-004",type:"notification",priority:"low"}].map((q) => (
                <div key={q.id} className="flex items-center justify-between py-2.5 border-b last:border-0 border-border">
                  <span className="text-xs font-mono text-foreground/70">{q.id}</span>
                  <span className="text-xs text-muted-foreground">{q.type}</span>
                  <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${q.priority==="high"?"bg-amber-400/10 text-amber-400 border border-amber-400/20":"bg-muted text-muted-foreground border border-border"}`}>{q.priority}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Global Runs View ─────────────────────────────────────────────────────────
function HistoryView() {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const filtered = ALL_RUNS.filter((r) => {
    const matchSearch = r.id.includes(search) || r.workflow.includes(search);
    const matchStatus = statusFilter==="all" || r.status===statusFilter;
    return matchSearch && matchStatus;
  });
  return (
    <div className="p-5 space-y-4 overflow-y-auto h-full" style={{ scrollbarWidth:"none" }}>
      <div className="flex items-center gap-3 flex-wrap">
        <div className="flex items-center gap-2 bg-muted rounded px-3 py-1.5 flex-1 min-w-[180px] max-w-xs">
          <Search size={11} className="text-muted-foreground/60 flex-shrink-0"/>
          <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search runs…" className="bg-transparent text-xs text-foreground placeholder:text-muted-foreground/50 outline-none w-full"/>
        </div>
        <div className="flex gap-1.5">
          {["all","success","warning","failed","running"].map((s) => {
            const cfg = s==="all" ? null : STATUS_CFG[s];
            return <button key={s} onClick={() => setStatusFilter(s)} className={`px-2.5 py-1.5 rounded text-xs capitalize transition-colors ${statusFilter===s?"bg-primary/15 border border-primary/30 text-primary":"bg-muted border border-border text-muted-foreground hover:text-foreground"}`}>{s}</button>;
          })}
        </div>
        <span className="text-xs text-muted-foreground ml-auto">{filtered.length} of {ALL_RUNS.length} runs</span>
      </div>
      <div className="bg-card border border-border rounded-lg overflow-hidden">
        <div className="grid grid-cols-6 px-4 py-2.5 border-b border-border">
          {["Run ID","Status","Workflow","Started","Duration","Tests"].map((h) => <span key={h} className="text-xs text-muted-foreground font-medium">{h}</span>)}
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
        <span>Showing {filtered.length} of 47 total runs</span>
        <div className="flex items-center gap-2">
          <button className="px-2.5 py-1 bg-muted border border-border rounded hover:text-foreground transition-colors">← Prev</button>
          <span className="px-3 py-1 bg-primary/10 border border-primary/30 rounded text-primary">1</span>
          <button className="px-2.5 py-1 bg-muted border border-border rounded hover:text-foreground transition-colors">Next →</button>
        </div>
      </div>
    </div>
  );
}

// ─── Agent Detail View ────────────────────────────────────────────────────────
function AgentDetailView({ agent, onBack }: { agent: AgentData; onBack: () => void }) {
  const [tab, setTab] = useState<"overview"|"tools"|"runs">("overview");
  return (
    <div className="h-full overflow-y-auto" style={{ scrollbarWidth:"none" }}>
      <div className="sticky top-0 z-10 bg-background border-b border-border px-6 py-4">
        <button onClick={onBack} className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors mb-3"><ChevronLeft size={13}/> Back to dashboard</button>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center"><Bot size={16} className="text-primary"/></div>
            <div>
              <div className="flex items-center gap-2"><h1 className="text-lg font-semibold text-foreground">{agent.name}</h1><StatusBadge status={agent.status}/></div>
              <div className="text-xs text-muted-foreground">{agent.type} · {agent.model}</div>
            </div>
          </div>
          <div className="flex gap-2">
            <button className="flex items-center gap-1.5 px-3 py-1.5 bg-muted rounded text-xs text-muted-foreground hover:text-foreground transition-colors"><RotateCcw size={11}/> Restart</button>
            <button className="flex items-center gap-1.5 px-3 py-1.5 bg-primary/10 border border-primary/25 rounded text-xs text-primary hover:bg-primary/15 transition-colors"><Play size={11}/> Run</button>
          </div>
        </div>
      </div>
      <div className="p-6 space-y-5">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard icon={CheckCircle2} label="Success Rate" value={`${agent.successRate}%`} accent="text-emerald-400"/>
          <StatCard icon={Activity}     label="Total Runs"   value={agent.totalRuns.toLocaleString()}/>
          <StatCard icon={Brain}        label="Memory Nodes" value={agent.memoryNodes.toString()} accent="text-violet-400"/>
          <StatCard icon={Wrench}       label="Tools"        value={agent.tools.length.toString()}/>
        </div>
        <div className="bg-card border border-border rounded-lg p-5">
          <div className="text-xs text-muted-foreground mb-2 font-medium uppercase tracking-wider">Description</div>
          <p className="text-sm text-foreground/80 leading-relaxed">{agent.description}</p>
        </div>
        <div>
          <div className="flex gap-0 border-b border-border mb-4">
            {(["overview","tools","runs"] as const).map((t) => (
              <button key={t} onClick={() => setTab(t)} className={`px-4 py-2 text-xs font-medium capitalize border-b-2 -mb-px transition-colors ${tab===t?"border-primary text-primary":"border-transparent text-muted-foreground hover:text-foreground"}`}>{t}</button>
            ))}
          </div>
          {tab==="overview" && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div className="bg-card border border-border rounded-lg p-4">
                <div className="text-xs text-muted-foreground mb-3 font-medium uppercase tracking-wider">Configuration</div>
                <div className="space-y-2.5">
                  {[["Model",agent.model],["Agent ID",agent.id],["Type",agent.type],["Last Active",agent.lastRun],["Memory Scope","workflow-scoped"],["Max Tokens","32,768"]].map(([l,v]) => (
                    <div key={l} className="flex justify-between items-center"><span className="text-xs text-muted-foreground">{l}</span><span className="text-xs font-mono text-foreground/70">{v}</span></div>
                  ))}
                </div>
              </div>
              <div className="bg-card border border-border rounded-lg p-4">
                <div className="text-xs text-muted-foreground mb-3 font-medium uppercase tracking-wider">Capabilities</div>
                <div className="space-y-2">
                  {["Tool invocation","Memory read/write","Parallel execution","Workflow dispatch","Result synthesis"].map((cap) => (
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
                  <div><div className="text-sm font-medium text-foreground">{tool}</div><div className="text-xs text-muted-foreground">Tool · Ready</div></div>
                  <CheckCircle2 size={13} className="text-emerald-400 ml-auto"/>
                </div>
              ))}
            </div>
          )}
          {tab==="runs" && (
            <div className="bg-card border border-border rounded-lg overflow-hidden">
              <div className="grid grid-cols-5 px-4 py-2.5 border-b border-border">{["Run ID","Status","Started","Duration","Tests"].map((h) => <span key={h} className="text-xs text-muted-foreground font-medium">{h}</span>)}</div>
              {RECENT_RUNS.map((run, i) => {
                const cfg = STATUS_CFG[run.status] ?? STATUS_CFG.idle;
                return <div key={run.id} className={`grid grid-cols-5 px-4 py-3 hover:bg-white/3 transition-colors ${i<RECENT_RUNS.length-1?"border-b border-border":""}`}><span className="text-xs font-mono text-foreground/70">{run.id}</span><span className={`text-xs font-medium ${cfg.text}`}>{cfg.label}</span><span className="text-xs text-muted-foreground">{run.started}</span><span className="text-xs font-mono text-muted-foreground">{run.duration}</span><span className="text-xs font-mono text-muted-foreground">{run.passed}/{run.total}</span></div>;
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── Settings View ────────────────────────────────────────────────────────────
function SettingsView() {
  const [theme, setTheme] = useState("alice");
  const [lang, setLang] = useState("en");
  const [provider, setProvider] = useState("claude");
  const themes = [
    { id:"alice",     label:"Alice",     sub:"Cool Cyan",     swatch:"bg-cyan-400"   },
    { id:"aoko",      label:"Aoko",      sub:"Blue & Amber",  swatch:"bg-blue-500"   },
    { id:"soujuurou", label:"Soujuurou", sub:"Green & Brown", swatch:"bg-emerald-500"},
  ];
  const providers = [
    { id:"claude",   label:"Claude",   org:"Anthropic",  badge:"✓ Active" },
    { id:"deepseek", label:"DeepSeek", org:"DeepSeek AI",badge:"" },
    { id:"openai",   label:"OpenAI",   org:"OpenAI",     badge:"" },
    { id:"ollama",   label:"Ollama",   org:"Local",      badge:"" },
  ];
  return (
    <div className="p-6 space-y-6 overflow-y-auto h-full max-w-2xl" style={{ scrollbarWidth:"none" }}>
      <div>
        <h2 className="text-sm font-semibold text-foreground mb-1">Appearance</h2>
        <p className="text-xs text-muted-foreground mb-4">Choose your theme and visual preferences</p>
        <div className="grid grid-cols-3 gap-3 mb-4">
          {themes.map((t) => (
            <button key={t.id} onClick={() => setTheme(t.id)} className={`text-left p-3 rounded-lg border transition-all ${theme===t.id?"border-primary/50 bg-primary/8":"border-border bg-card hover:border-border/70"}`}>
              <div className={`w-6 h-6 rounded-full ${t.swatch} mb-2 opacity-80`}/>
              <div className="text-xs font-semibold text-foreground">{t.label}</div>
              <div className="text-xs text-muted-foreground">{t.sub}</div>
            </button>
          ))}
        </div>
        <div className="flex items-center justify-between p-3 bg-card border border-border rounded-lg">
          <div><div className="text-xs font-medium text-foreground">Dark Mode</div><div className="text-xs text-muted-foreground">Always on for this theme</div></div>
          <div className="w-10 h-5 bg-primary/20 border border-primary/30 rounded-full relative"><div className="absolute right-0.5 top-0.5 w-4 h-4 bg-primary rounded-full"/></div>
        </div>
      </div>
      <div className="h-px bg-border"/>
      <div>
        <h2 className="text-sm font-semibold text-foreground mb-1">Language</h2>
        <div className="flex gap-2 mt-3">
          {[{id:"en",label:"English"},{id:"zh",label:"中文"}].map((l) => (
            <button key={l.id} onClick={() => setLang(l.id)} className={`px-4 py-2 rounded-lg border text-sm transition-colors ${lang===l.id?"bg-primary/10 border-primary/30 text-primary":"bg-card border-border text-muted-foreground hover:text-foreground"}`}>{l.label}</button>
          ))}
        </div>
      </div>
      <div className="h-px bg-border"/>
      <div>
        <h2 className="text-sm font-semibold text-foreground mb-1">AI Provider</h2>
        <p className="text-xs text-muted-foreground mb-4">Select and configure the AI model provider</p>
        <div className="grid grid-cols-2 gap-3 mb-4">
          {providers.map((p) => (
            <button key={p.id} onClick={() => setProvider(p.id)} className={`text-left p-3 rounded-lg border transition-all ${provider===p.id?"border-primary/50 bg-primary/8":"border-border bg-card hover:border-border/70"}`}>
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
            <label className="text-xs text-muted-foreground block mb-1">API Key</label>
            <input type="password" value="sk-ant-api03-••••••••••••••••" readOnly className="w-full px-3 py-2 bg-muted border border-border rounded text-xs text-foreground font-mono outline-none"/>
          </div>
        </div>
      </div>
      <div className="h-px bg-border"/>
      <div>
        <h2 className="text-sm font-semibold text-foreground mb-1">Budget</h2>
        <div className="grid grid-cols-2 gap-4">
          {[{label:"Daily Limit",value:"$10.00"},{label:"Monthly Limit",value:"$100.00"}].map((b) => (
            <div key={b.label}>
              <label className="text-xs text-muted-foreground block mb-1">{b.label}</label>
              <input defaultValue={b.value} className="w-full px-3 py-2 bg-muted border border-border rounded text-xs text-foreground outline-none focus:border-primary/50"/>
            </div>
          ))}
        </div>
        <div className="flex items-center justify-between mt-4 p-3 bg-card border border-border rounded-lg">
          <span className="text-xs text-muted-foreground">Cost this run</span>
          <span className="text-xs font-mono text-[#f0c040]">$0.032</span>
        </div>
      </div>
      <button className="px-4 py-2 bg-primary/10 border border-primary/30 rounded text-xs text-primary hover:bg-primary/20 transition-colors">Save Changes</button>
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

function Sidebar({ view, onNav }: { view: View; onNav: (v: View) => void }) {
  const runningCount = AGENTS.filter((a) => a.status==="running").length;
  return (
    <aside className="w-52 flex-shrink-0 bg-sidebar border-r flex flex-col" style={{ borderColor:"rgba(50,90,180,0.1)" }}>
      <div className="px-4 py-5 border-b" style={{ borderColor:"rgba(50,90,180,0.1)" }}>
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-md bg-primary/15 border border-primary/25 flex items-center justify-center"><Layers size={14} className="text-primary"/></div>
          <div>
            <div className="text-sm font-semibold text-foreground leading-none">Alice</div>
            <div className="text-xs text-muted-foreground/50 leading-none mt-0.5" style={{ fontFamily:"serif" }}>有珠 Studio</div>
          </div>
        </div>
      </div>
      <div className="px-3 py-2.5 border-b" style={{ borderColor:"rgba(50,90,180,0.1)" }}>
        <div className="flex items-center gap-2 bg-cyan-400/8 border border-cyan-400/15 rounded px-2.5 py-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse flex-shrink-0"/>
          <span className="text-xs text-cyan-400 font-medium">{runningCount} agents running</span>
        </div>
      </div>
      <nav className="flex-1 overflow-y-auto py-2" style={{ scrollbarWidth:"none" }}>
        {NAV_GROUPS.map((group) => (
          <div key={group.label} className="mb-1">
            <div className="px-3 pt-3 pb-1">
              <span className="text-[9px] font-semibold uppercase tracking-[0.12em] text-muted-foreground/40">{group.label}</span>
            </div>
            <div className="px-2 space-y-0.5">
              {group.items.map(({ id, label, icon: Icon }) => {
                const isActive = view===id;
                return (
                  <button key={id} onClick={() => onNav(id as View)} className={`flex items-center gap-2.5 w-full px-3 py-2 rounded text-[13px] transition-all text-left ${isActive?"bg-primary/10 text-primary border-l-2 border-primary pl-[10px]":"text-muted-foreground hover:text-foreground hover:bg-white/4"}`}>
                    <Icon size={13} className="flex-shrink-0"/>
                    <span className="truncate">{label}</span>
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </nav>
      <div className="px-2 pb-3 border-t pt-2 space-y-0.5" style={{ borderColor:"rgba(50,90,180,0.1)" }}>
        <button onClick={() => onNav("settings")} className={`flex items-center gap-2.5 w-full px-3 py-2 rounded text-[13px] transition-all text-left ${view==="settings"?"bg-primary/10 text-primary border-l-2 border-primary pl-[10px]":"text-muted-foreground hover:text-foreground hover:bg-white/4"}`}>
          <Settings size={13} className="flex-shrink-0"/><span>Settings</span>
        </button>
        <div className="flex items-center gap-2.5 px-3 py-2 mt-1">
          <div className="w-6 h-6 rounded-full bg-primary/20 border border-primary/30 flex items-center justify-center flex-shrink-0"><span className="text-xs font-semibold text-primary">A</span></div>
          <div className="min-w-0"><div className="text-xs font-medium text-foreground/70 truncate">alice@lab.dev</div><div className="text-xs text-muted-foreground/50">Admin</div></div>
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
  observability:"Observability", history:"Run History", settings:"Settings", agent:"Agent Detail",
};

function TopBar({ view }: { view: View }) {
  return (
    <header className="h-12 flex-shrink-0 flex items-center px-5 gap-4 border-b border-border bg-background/80 backdrop-blur-sm">
      <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
        <span className="text-muted-foreground/50">Alice</span><ChevronRight size={11}/><span className="text-foreground/70">{VIEW_TITLES[view] ?? view}</span>
      </div>
      <div className="flex items-center gap-2 bg-muted rounded px-3 py-1.5 ml-4 w-52">
        <Search size={11} className="text-muted-foreground/60 flex-shrink-0"/>
        <input placeholder="Search…" className="bg-transparent text-xs text-foreground placeholder:text-muted-foreground/50 outline-none w-full"/>
        <kbd className="text-xs text-muted-foreground/40 font-mono">⌘K</kbd>
      </div>
      <div className="ml-auto flex items-center gap-3">
        <span className="text-xs text-muted-foreground font-mono hidden md:block">14:32:09</span>
        <div className="h-3.5 w-px bg-border"/>
        <button className="relative p-1.5 text-muted-foreground hover:text-foreground transition-colors rounded">
          <Bell size={14}/><span className="absolute top-0.5 right-0.5 w-1.5 h-1.5 rounded-full bg-cyan-400"/>
        </button>
      </div>
    </header>
  );
}

// ─── App Root ─────────────────────────────────────────────────────────────────
export default function App() {
  const [view, setView] = useState<View>("dashboard");
  const [selectedAgent, setSelectedAgent] = useState<AgentData|null>(null);

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
      <Sidebar view={view} onNav={handleNav}/>
      <div className="flex-1 flex flex-col overflow-hidden">
        <TopBar view={view}/>
        <main className="flex-1 overflow-hidden">
          <AnimatePresence mode="wait">
            <motion.div key={view} initial={{ opacity:0, y:5 }} animate={{ opacity:1, y:0 }} exit={{ opacity:0, y:-3 }} transition={{ duration:0.14 }} className="h-full">
              {view==="dashboard"    && <DashboardView onSelectAgent={handleSelectAgent}/>}
              {view==="workflow"     && <WorkflowBuilderView/>}
              {view==="execution"    && <ExecutionView/>}
              {view==="kanban"       && <KanbanView/>}
              {view==="inspector"    && <RunInspectorView/>}
              {view==="reports"      && <ReportsView/>}
              {view==="gaps"         && <GapsView/>}
              {view==="memory"       && <MemoryView/>}
              {view==="knowledge"    && <KnowledgeView/>}
              {view==="graph"        && <KnowledgeGraphView/>}
              {view==="artifacts"    && <ArtifactsView/>}
              {view==="chat"         && <ChatView/>}
              {view==="observability"&& <ObservabilityView/>}
              {view==="history"      && <HistoryView/>}
              {view==="settings"     && <SettingsView/>}
              {view==="agent"        && selectedAgent && <AgentDetailView agent={selectedAgent} onBack={() => handleNav("dashboard")}/>}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
}
