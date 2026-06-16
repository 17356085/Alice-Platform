"""
Structured Trace Logger — P1-1: 全链路追踪基础设施。

每个 LLM 调用、Skill 执行、Agent 决策均发射一个 TraceEvent，
以 JSONL 格式持久化到 governance/.traces/trace_log.jsonl。

设计原则:
  - 零外部依赖，纯标准库实现
  - 线程安全 JSONL 追加（复刻 error_logger.py 模式）
  - TraceContext: thread-local 上下文，解决跨调用栈传递 run_id/agent_name
  - 装饰器模式注入 LLMProvider.complete()，不修改子类

用法:
    from aitest.trace import TraceEvent, TraceContext, write_trace_event

    TraceContext.set(run_id="sop-equipment-1718400000", agent_name="automation-agent")

    event = TraceEvent(
        event_id="llm-abc123",
        event_type="llm_call",
        run_id=TraceContext.get_run_id(),
        agent_name=TraceContext.get_agent_name(),
        provider="claude", model="claude-sonnet-4-6",
        latency_ms=1234, token_input=500, token_output=200,
        status="success",
    )
    write_trace_event(event)

CLI:
    aitest trace list [--run-id=<r>] [--type=<t>] [--skill=<s>] [--limit=<n>]
    aitest trace summary <run-id>
    aitest trace clean [--days=<n>]
"""

import json
import threading
import time
import uuid
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
import functools

# ── 路径配置 ──────────────────────────────────────────────────────────
WORKSTUDY = Path(__file__).resolve().parent.parent
TRACE_DIR = WORKSTUDY / "governance" / ".traces"
TRACE_LOG = TRACE_DIR / "trace_log.jsonl"

# ── 线程安全锁 ──────────────────────────────────────────────────────
_write_lock = threading.Lock()


def _ensure_dir() -> None:
    """确保追踪日志目录存在。"""
    TRACE_DIR.mkdir(parents=True, exist_ok=True)


# ══════════════════════════════════════════════════════════════════════════
#  TraceContext — thread-local 上下文传递
# ══════════════════════════════════════════════════════════════════════════

class TraceContext:
    """
    Thread-local 上下文管理器。

    解决 run_id / agent_name / skill_version 需要跨多层调用栈传递的问题。
    在 AgentLoop.__init__ 中 set，在任意深度的 LLM 调用中 get。

    用法:
        TraceContext.set(run_id="sop-xxx", agent_name="automation-agent", skill_version="1.0")
        rid = TraceContext.get_run_id()
        aname = TraceContext.get_agent_name()
        ver = TraceContext.get_skill_version()
        TraceContext.reset()
    """
    _ctx = threading.local()

    @classmethod
    def set(cls, run_id: str = "", agent_name: str = "", skill_version: str = "") -> None:
        cls._ctx.run_id = run_id
        cls._ctx.agent_name = agent_name
        cls._ctx.skill_version = skill_version

    @classmethod
    def get_run_id(cls) -> str:
        return getattr(cls._ctx, "run_id", "")

    @classmethod
    def get_agent_name(cls) -> str:
        return getattr(cls._ctx, "agent_name", "")

    @classmethod
    def get_skill_version(cls) -> str:
        return getattr(cls._ctx, "skill_version", "")

    @classmethod
    def reset(cls) -> None:
        cls._ctx.run_id = ""
        cls._ctx.agent_name = ""
        cls._ctx.skill_version = ""


# ══════════════════════════════════════════════════════════════════════════
#  TraceEvent
# ══════════════════════════════════════════════════════════════════════════

# 模型定价表 ($/1M tokens: input, output)
# 来源: Anthropic / OpenAI 官方定价 + 本地模型
MODEL_PRICING = {
    # Anthropic Claude
    "claude-opus-4-8": (15.0, 75.0),
    "claude-sonnet-4-6": (3.0, 15.0),
    "claude-fable-5": (3.0, 15.0),
    "claude-haiku-4-5": (0.8, 4.0),
    "claude-opus-4-7": (15.0, 75.0),
    "claude-haiku-3-5": (0.8, 4.0),
    "claude-sonnet-4": (3.0, 15.0),
    "claude-opus-4": (15.0, 75.0),
    # OpenAI
    "gpt-4o": (2.5, 10.0),
    "gpt-4o-mini": (0.15, 0.6),
    "gpt-4-turbo": (10.0, 30.0),
    "gpt-4": (30.0, 60.0),
    "gpt-3.5-turbo": (0.5, 1.5),
    # DeepSeek
    "deepseek-v3": (0.27, 1.10),
    "deepseek-v4": (0.27, 1.10),
    "deepseek-r1": (0.55, 2.19),
    "deepseek-chat": (0.27, 1.10),       # alias → V3
    "deepseek-reasoner": (0.55, 2.19),   # alias → R1
    # Qwen (Ollama — 本地免费)
    "qwen3": (0.0, 0.0),
    "qwen2.5": (0.0, 0.0),
    "qwen": (0.0, 0.0),
    # Llama (Ollama — 本地免费)
    "llama3": (0.0, 0.0),
    "gemma": (0.0, 0.0),
    "mistral": (0.0, 0.0),
    "codellama": (0.0, 0.0),
}


@dataclass
class TraceEvent:
    """一次可观测事件的完整记录。"""
    event_id: str                        # uuid4 hex[:12]
    event_type: str                      # llm_call | skill_execution | agent_decision | artifact_check | milestone
    timestamp: str                       # datetime.now().isoformat()
    run_id: str = ""                     # SOPState.run_id
    agent_name: str = ""                 # AgentLoop.agent_name
    skill_id: str = ""                   # "automation/tech-analysis"
    provider: str = ""                   # "claude" | "openai" | "ollama"
    model: str = ""                      # 实际响应中的模型名
    latency_ms: int = 0                  # 墙体时钟耗时
    token_input: int = 0
    token_output: int = 0
    token_cost_estimate: float = 0.0     # $ 估算
    status: str = "success"              # success | error | partial
    prompt_preview: str = ""             # 前 200 字符
    response_preview: str = ""           # 前 500 字符
    error_message: str = ""              # 失败时填充
    metadata: dict = field(default_factory=dict)  # temperature, max_tokens, finish_reason 等

    @staticmethod
    def calculate_cost(model: str, token_input: int, token_output: int) -> float:
        """
        根据模型名称估算成本（零外部依赖）。

        参数:
            model: 模型名称字符串（支持子串匹配）
            token_input: 输入 token 数
            token_output: 输出 token 数

        返回:
            估算成本（美元 $）
        """
        if not model or (token_input == 0 and token_output == 0):
            return 0.0

        model_lower = model.lower()
        # 精确匹配优先
        if model_lower in MODEL_PRICING:
            input_p, output_p = MODEL_PRICING[model_lower]
        else:
            # 子串匹配
            matched = None
            for key, prices in MODEL_PRICING.items():
                if key in model_lower or model_lower in key:
                    matched = prices
                    break
            if matched is None:
                return 0.0
            input_p, output_p = matched

        return round(
            (token_input / 1_000_000 * input_p) +
            (token_output / 1_000_000 * output_p),
            6,
        )

    @classmethod
    def create(
        cls,
        event_type: str,
        run_id: str = "",
        agent_name: str = "",
        skill_id: str = "",
        provider: str = "",
        model: str = "",
        latency_ms: int = 0,
        token_input: int = 0,
        token_output: int = 0,
        status: str = "success",
        prompt_preview: str = "",
        response_preview: str = "",
        error_message: str = "",
        metadata: dict = None,
    ) -> "TraceEvent":
        """工厂方法：自动填充 event_id 和 timestamp。"""
        return cls(
            event_id=f"{event_type[:4]}-{uuid.uuid4().hex[:12]}",
            event_type=event_type,
            timestamp=datetime.now().isoformat(),
            run_id=run_id or TraceContext.get_run_id(),
            agent_name=agent_name or TraceContext.get_agent_name(),
            skill_id=skill_id,
            provider=provider,
            model=model,
            latency_ms=latency_ms,
            token_input=token_input,
            token_output=token_output,
            token_cost_estimate=cls.calculate_cost(model, token_input, token_output),
            status=status,
            prompt_preview=(prompt_preview or "")[:200].replace("\n", " "),
            response_preview=(response_preview or "")[:500].replace("\n", " "),
            error_message=(error_message or "")[:300],
            metadata=metadata or {},
        )

    def to_dict(self) -> dict:
        """序列化为字典（用于 JSONL 写入）。"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "run_id": self.run_id,
            "agent_name": self.agent_name,
            "skill_id": self.skill_id,
            "provider": self.provider,
            "model": self.model,
            "latency_ms": self.latency_ms,
            "token_input": self.token_input,
            "token_output": self.token_output,
            "token_cost_estimate": self.token_cost_estimate,
            "status": self.status,
            "prompt_preview": self.prompt_preview,
            "response_preview": self.response_preview,
            "error_message": self.error_message,
            "metadata": self.metadata,
        }


# ══════════════════════════════════════════════════════════════════════════
#  JSONL 写入与查询
# ══════════════════════════════════════════════════════════════════════════

def write_trace_event(event: TraceEvent) -> dict:
    """
    线程安全地将 TraceEvent 写入 JSONL 文件。

    P0-1 (2026-06-16): 自动从 TraceContext 注入 skill_version，
    确保所有 trace event 都携带版本信息（Prompt Versioning 数据流闭合）。

    参数:
        event: TraceEvent 实例

    返回:
        已写入的事件字典
    """
    _ensure_dir()

    # P0-1: 自动注入 skill_version — 调用者无需手动传递
    sv = TraceContext.get_skill_version()
    if sv and "skill_version" not in event.metadata:
        event.metadata["skill_version"] = sv

    entry = event.to_dict()

    try:
        with _write_lock:
            with open(TRACE_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        import sys
        print(
            f"[aitest.trace FATAL] Cannot write to {TRACE_LOG}: "
            f"event_id={event.event_id} type={event.event_type}",
            file=sys.stderr,
        )

    return entry


def query_trace_events(
    run_id: str = None,
    event_type: str = None,
    skill_id: str = None,
    agent_name: str = None,
    status: str = None,
    limit: int = 100,
) -> list[dict]:
    """
    查询追踪事件（最近优先）。

    参数:
        run_id: 按运行 ID 筛选
        event_type: 按事件类型筛选 (llm_call | skill_execution | agent_decision | …)
        skill_id: 按 Skill ID 筛选（支持子串匹配）
        agent_name: 按 Agent 筛选
        status: 按状态筛选 (success | error | partial)
        limit: 返回条数上限

    返回:
        事件字典列表（最近优先）
    """
    _ensure_dir()
    if not TRACE_LOG.exists():
        return []

    events = []
    try:
        with open(TRACE_LOG, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    if run_id and entry.get("run_id") != run_id:
                        continue
                    if event_type and entry.get("event_type") != event_type:
                        continue
                    if skill_id and skill_id not in entry.get("skill_id", ""):
                        continue
                    if agent_name and entry.get("agent_name") != agent_name:
                        continue
                    if status and entry.get("status") != status:
                        continue
                    events.append(entry)
                except json.JSONDecodeError:
                    continue
    except Exception:
        return []

    # 最近优先
    events.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
    return events[:limit]


def get_trace_summary(run_id: str = None) -> dict:
    """
    获取追踪摘要：按事件类型和 Skill 聚合统计。

    参数:
        run_id: 按运行 ID 筛选（None = 所有 run）

    返回:
        {
            "total_events": 42,
            "by_type": {"llm_call": 30, "skill_execution": 10, ...},
            "by_skill": {"automation/tech-analysis": {...}, ...},
            "total_cost": 0.123,
            "total_latency_ms": 12000,
            "total_tokens_input": 50000,
            "total_tokens_output": 30000,
            "models_seen": ["claude-sonnet-4-6"],
        }
    """
    _ensure_dir()
    if not TRACE_LOG.exists():
        return {
            "total_events": 0,
            "by_type": {},
            "by_skill": {},
            "total_cost": 0.0,
            "total_latency_ms": 0,
            "total_tokens_input": 0,
            "total_tokens_output": 0,
            "models_seen": [],
        }

    by_type = {}
    by_skill = {}
    total_cost = 0.0
    total_latency = 0
    total_in = 0
    total_out = 0
    models = set()
    event_count = 0

    try:
        with open(TRACE_LOG, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    if run_id and entry.get("run_id") != run_id:
                        continue

                    event_count += 1
                    etype = entry.get("event_type", "unknown")
                    by_type[etype] = by_type.get(etype, 0) + 1

                    sid = entry.get("skill_id", "")
                    if sid:
                        if sid not in by_skill:
                            by_skill[sid] = {"count": 0, "success": 0, "error": 0,
                                           "total_latency_ms": 0, "total_tokens_in": 0,
                                           "total_tokens_out": 0}
                        by_skill[sid]["count"] += 1
                        by_skill[sid]["total_latency_ms"] += entry.get("latency_ms", 0)
                        by_skill[sid]["total_tokens_in"] += entry.get("token_input", 0)
                        by_skill[sid]["total_tokens_out"] += entry.get("token_output", 0)
                        if entry.get("status") == "success":
                            by_skill[sid]["success"] += 1
                        elif entry.get("status") == "error":
                            by_skill[sid]["error"] += 1

                    total_cost += entry.get("token_cost_estimate", 0)
                    total_latency += entry.get("latency_ms", 0)
                    total_in += entry.get("token_input", 0)
                    total_out += entry.get("token_output", 0)
                    if entry.get("model"):
                        models.add(entry["model"])

                except json.JSONDecodeError:
                    continue
    except Exception:
        pass

    # 计算每个 skill 的平均值
    for sid, stats in by_skill.items():
        count = stats["count"]
        if count > 0:
            stats["avg_latency_ms"] = round(stats["total_latency_ms"] / count)
            stats["avg_tokens_in"] = round(stats["total_tokens_in"] / count)
            stats["avg_tokens_out"] = round(stats["total_tokens_out"] / count)
            stats["success_rate"] = round(stats["success"] / count, 3)
        del stats["total_latency_ms"]
        del stats["total_tokens_in"]
        del stats["total_tokens_out"]

    return {
        "total_events": event_count,
        "by_type": by_type,
        "by_skill": by_skill,
        "total_cost": round(total_cost, 6),
        "total_latency_ms": total_latency,
        "total_tokens_input": total_in,
        "total_tokens_output": total_out,
        "models_seen": sorted(models),
    }


def get_run_stats(run_id: str) -> dict:
    """
    P0 可观测性: 按 run_id 聚合单次 SOP 运行的 Token/调用/成本统计。

    返回:
        {run_id, total_tokens_in, total_tokens_out, total_cost,
         total_llm_calls, agent_decision_calls, skill_executions,
         by_agent: {agent_name: {calls, tokens_in, tokens_out, cost}},
         by_skill: {skill_id: {calls, tokens_in, tokens_out, cost}},
         total_latency_ms, models_seen}
    """
    events = query_trace_events(run_id=run_id, limit=0)
    if not events:
        return {"error": f"No trace events found for run_id='{run_id}'"}

    total_in = 0
    total_out = 0
    total_cost = 0.0
    total_latency = 0
    llm_calls = 0
    decision_calls = 0
    skill_execs = 0
    by_agent: dict = {}
    by_skill: dict = {}
    models: set = set()

    for e in events:
        tokens_in = e.get("token_input", 0) or 0
        tokens_out = e.get("token_output", 0) or 0
        cost = e.get("token_cost_estimate", 0) or 0
        latency = e.get("latency_ms", 0) or 0
        etype = e.get("event_type", "")
        agent = e.get("agent_name", "") or "(unknown)"
        skill = e.get("skill_id", "") or "(unknown)"
        model = e.get("model", "")
        if model:
            models.add(model)

        total_in += tokens_in
        total_out += tokens_out
        total_cost += cost
        total_latency += latency

        if etype == "llm_call":
            llm_calls += 1
        elif etype == "agent_decision":
            decision_calls += 1
        elif etype == "skill_execution":
            skill_execs += 1

        # by_agent
        if agent not in by_agent:
            by_agent[agent] = {"calls": 0, "tokens_in": 0, "tokens_out": 0, "cost": 0.0}
        by_agent[agent]["calls"] += 1
        by_agent[agent]["tokens_in"] += tokens_in
        by_agent[agent]["tokens_out"] += tokens_out
        by_agent[agent]["cost"] += cost

        # by_skill (仅 skill_execution 事件)
        if etype == "skill_execution":
            if skill not in by_skill:
                by_skill[skill] = {"calls": 0, "tokens_in": 0, "tokens_out": 0, "cost": 0.0}
            by_skill[skill]["calls"] += 1
            by_skill[skill]["tokens_in"] += tokens_in
            by_skill[skill]["tokens_out"] += tokens_out
            by_skill[skill]["cost"] += cost

    # 按成本排序
    by_agent_sorted = dict(sorted(by_agent.items(), key=lambda x: x[1]["cost"], reverse=True))
    by_skill_sorted = dict(sorted(by_skill.items(), key=lambda x: x[1]["cost"], reverse=True))

    return {
        "run_id": run_id,
        "total_tokens_in": total_in,
        "total_tokens_out": total_out,
        "total_tokens": total_in + total_out,
        "total_cost": round(total_cost, 6),
        "total_llm_calls": llm_calls,
        "agent_decision_calls": decision_calls,
        "skill_executions": skill_execs,
        "by_agent": by_agent_sorted,
        "by_skill": by_skill_sorted,
        "total_latency_ms": total_latency,
        "models_seen": sorted(models),
    }


def get_cost_leaderboard(days: int = 7, limit: int = 10) -> list[dict]:
    """
    P1 可观测性: Agent 成本排行榜 — 按 agent_name 聚合最近 N 天的成本。

    返回: [{agent, calls, tokens_in, tokens_out, cost, avg_tokens_per_call}, ...]
    """
    events = query_trace_events(limit=0)
    if not events:
        return []

    cutoff = datetime.now() - timedelta(days=days)
    by_agent: dict = {}

    for e in events:
        try:
            ts = datetime.fromisoformat(e.get("timestamp", "2000-01-01T00:00:00"))
        except (ValueError, TypeError):
            continue
        if ts < cutoff:
            continue

        agent = e.get("agent_name", "") or "(unknown)"
        tokens_in = e.get("token_input", 0) or 0
        tokens_out = e.get("token_output", 0) or 0
        cost = e.get("token_cost_estimate", 0) or 0

        if agent not in by_agent:
            by_agent[agent] = {"calls": 0, "tokens_in": 0, "tokens_out": 0, "cost": 0.0}
        by_agent[agent]["calls"] += 1
        by_agent[agent]["tokens_in"] += tokens_in
        by_agent[agent]["tokens_out"] += tokens_out
        by_agent[agent]["cost"] += cost

    result = []
    for agent, stats in by_agent.items():
        calls = stats["calls"]
        result.append({
            "agent": agent,
            "calls": calls,
            "tokens_in": stats["tokens_in"],
            "tokens_out": stats["tokens_out"],
            "cost": round(stats["cost"], 6),
            "avg_tokens_per_call": round(stats["tokens_in"] / calls) if calls > 0 else 0,
        })

    result.sort(key=lambda x: x["cost"], reverse=True)
    return result[:limit]


def cleanup_old_traces(days: int = 7) -> int:
    """
    清理 N 天前的追踪日志。

    返回: 删除的条目数
    """
    _ensure_dir()
    if not TRACE_LOG.exists():
        return 0

    cutoff = datetime.now() - timedelta(days=days)
    kept = []
    deleted = 0

    try:
        with open(TRACE_LOG, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    ts = datetime.fromisoformat(entry.get("timestamp", "2000-01-01T00:00:00"))
                    if ts >= cutoff:
                        kept.append(line)
                    else:
                        deleted += 1
                except (json.JSONDecodeError, ValueError):
                    deleted += 1

        with open(TRACE_LOG, "w", encoding="utf-8") as f:
            for line in kept:
                f.write(line + "\n")
    except Exception:
        return 0

    return deleted


# ══════════════════════════════════════════════════════════════════════════
#  LLM Provider 装饰器
# ══════════════════════════════════════════════════════════════════════════

def _trace_llm_call(fn):
    """
    包装 LLMProvider.complete() 方法，在每次 LLM 调用时发射 TraceEvent。

    装饰器应用在 get_provider() 工厂中，不修改 Provider 类定义。
    这样保证零影响子类化、测试 mock 和已有调用者。

    fn 是 bound method (instance.complete)，已绑定 self。
    wrapper 作为 instance 属性直接赋值，Python descriptor 协议不触发，
    因此 wrapper 签名不含 self——instance 从 fn.__self__ 获取。

    发射的 TraceEvent 带有:
      - event_type="llm_call"
      - latency_ms: 墙体时钟耗时
      - token 使用量 + 成本估算
      - provider + model
      - 截断的 prompt/response 预览

    同时给 LLMResponse 动态附加:
      - trace_event_id: 下游可用此 ID 补全 skill_id 等上下文
      - latency_ms: 墙体时钟耗时 (ms)
    """
    # 从 bound method 获取 provider instance
    instance = getattr(fn, "__self__", None)
    provider_name = instance.__class__.__name__.replace("Provider", "").lower() if instance else "unknown"
    instance_model = getattr(instance, "model", "") if instance else ""

    @functools.wraps(fn)
    def wrapper(system_prompt="", user_prompt="", **kwargs):
        start_ns = time.time()
        # fn 是 bound method，已绑定 instance，不再传 self
        response = fn(system_prompt, user_prompt, **kwargs)
        elapsed_ms = int((time.time() - start_ns) * 1000)

        token_usage = response.token_usage or {}
        inp = token_usage.get("input", 0)
        out = token_usage.get("output", 0)
        model = response.model or instance_model

        # P0-1: 从 TraceContext 获取 skill_version
        skill_ver = TraceContext.get_skill_version()

        event = TraceEvent.create(
            event_type="llm_call",
            provider=provider_name,
            model=model,
            latency_ms=elapsed_ms,
            token_input=inp,
            token_output=out,
            status="success" if (response.finish_reason and response.finish_reason != "error") else "error",
            prompt_preview=(system_prompt or ""),
            response_preview=(response.content or ""),
            error_message=(response.content or "")[:300] if response.finish_reason == "error" else "",
            metadata={
                "temperature": kwargs.get("temperature"),
                "max_tokens": kwargs.get("max_tokens"),
                "finish_reason": response.finish_reason,
                "skill_version": skill_ver,           # P0-1: Prompt 版本跟踪
            },
        )
        write_trace_event(event)

        # 动态附加 trace 元数据到响应对象
        response.trace_event_id = event.event_id
        response.latency_ms = elapsed_ms

        return response

    return wrapper
