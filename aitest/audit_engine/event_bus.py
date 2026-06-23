"""
Event Bus — 轻量事件系统（文件持久化 + 订阅者模式）

事件类型:
  ── Knowledge Events (已有) ──
  - AgentCompleted(agent, module, status, skill, artifacts)
  - BugClosed(bug_id, module, root_cause, known_issue_id)
  - CycleEnd(module, stats)
  - ContextUpdated(file, changes)

  ── Governance Events (P0-3: 新增) ──
  - StateDrift(module, run_id, drift_count, error_count, warning_count, overall_status)
  - SOPViolation(module, run_id, violation_type, detail)
  - PromptChanged(skill_id, old_version, new_version, changelog)
  - EvalRegressed(skill_id, case_id, old_score, new_score)
  - CostAnomaly(skill_id, agent, anomaly_type, detail)
  - AuditCompleted(audit_type, module, report_path, overall_status)

  ── Quality Governance Events (P2-5: 业务覆盖质量门禁) ──
  - BusinessCoverageInsufficient(module, page, score, threshold, dimensions_detail)
  - WorkflowCoverageInsufficient(module, page_count, cross_page_scenarios)
  - TestDesignQualityRegressed(module, page, old_score, new_score, delta)

  ── Safety Events (P0: Safety Auditor) ──
  - SafetyViolation(module, severity, rule_id, violation_count, critical_count, description, suggestion)
  - SafetyAuditCompleted(module, overall_status, safety_score, violation_count)

  ── Online Monitoring Events (P0: Online Monitor) ──
  - OnlineMetricAnomaly(module, metric, current_value, threshold, direction, suggestion)

  ── Meta-Governance Review Events (P0: Architecture Review Skills) ──
  - ArchitectureRiskDetected(module, risk_type, severity, description, recommendation)
  - GovernanceGapDetected(gap_type, affected_modules, risk_level, recommendation)
  - TechnicalDebtDetected(debt_type, location, severity, estimated_cost, recommendation)
  - ProductionRiskDetected(risk_type, severity, is_blocker, recommendation)
  - ReviewCompleted(review_type, module, overall_score, critical_count, warning_count, report_path)

Knowledge Agent 作为订阅者监听这些事件，自动触发知识沉淀。

用法:
  python -m aitest.event_bus emit AgentCompleted --agent=automation-agent --module=equipment --status=success
  python -m aitest.event_bus emit StateDrift --module=equipment --drift_count=3
  python -m aitest.event_bus listen             # 列出待处理事件
  python -m aitest.event_bus process            # 处理所有待处理事件
  python -m aitest.event_bus watch              # 持续监听模式（每 60s 轮询）
"""
import os
import json
import time
import uuid
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, Callable

# ── 路径配置 ──────────────────────────────────────────────────────────
WORKSTUDY = Path(__file__).resolve().parent.parent.parent
EVENT_DIR = WORKSTUDY / "governance" / ".events"
EVENT_DIR.mkdir(parents=True, exist_ok=True)

# Event → Knowledge Agent action 映射
EVENT_ACTIONS = {
    # ── Knowledge Events (已有) ──
    "AgentCompleted": {
        "trigger": "knowledge-manager (mode: extract)",
        "condition": "agent_status == 'success'",
        "prompt_template": "Agent {agent} 完成了 {module} 模块 {skill} 的工作。检查是否有可沉淀的知识模式。"
    },
    "BugClosed": {
        "trigger": "knowledge-manager (mode: extract)",
        "condition": "always",
        "prompt_template": "Bug {bug_id} 已关闭。根因: {root_cause}。关联已知问题: {known_issue_id}。沉淀到知识库。"
    },
    "CycleEnd": {
        "trigger": "knowledge-manager (mode: precipitate)",
        "condition": "always",
        "prompt_template": "模块 {module} 测试周期结束。统计: {stats}。执行知识沉淀。"
    },
    "ContextUpdated": {
        "trigger": "context-sync",
        "condition": "always",
        "prompt_template": "上下文文件 {file} 已更新。变更: {changes}。检查下游文档是否需要同步。"
    },

    # ── Governance Events (P0-3: 新增) ──
    "StateDrift": {
        "trigger": "state-auditor (自动审计)",
        "condition": "drift_count > 0",
        "prompt_template": "模块 {module} 检测到 {drift_count} 个状态漂移 (error={error_count}, warning={warning_count})。建议审查审计报告。"
    },
    "SOPViolation": {
        "trigger": "sop-auditor (违规告警)",
        "condition": "always",
        "prompt_template": "模块 {module} 检测到 SOP 违规: [{violation_type}] {detail}。运行 '{run_id}'。"
    },
    "PromptChanged": {
        "trigger": "regression-gate (自动回归测试)",
        "condition": "always",
        "prompt_template": "Skill {skill_id} 从 {old_version} 升级到 {new_version}。Changelog: {changelog}。触发自动回归测试。"
    },
    "EvalRegressed": {
        "trigger": "regression-gate (退化告警)",
        "condition": "always",
        "prompt_template": "Skill {skill_id} 在用例 {case_id} 上退化: score {old_score} → {new_score}。阻止版本发布。"
    },
    "CostAnomaly": {
        "trigger": "cost-auditor (异常告警)",
        "condition": "always",
        "prompt_template": "检测到成本异常: Skill={skill_id}, Agent={agent}, Type={anomaly_type}, Detail={detail}。"
    },
    "BusinessCoverageInsufficient": {
        "trigger": "TESTCASE_QUALITY_GATE (L3 Validator)",
        "condition": "score < threshold",
        "prompt_template": "模块 {module} 页面 {page} 业务覆盖不足: score={score}, threshold={threshold}, details={dimensions_detail}。阻断 Test Design → Automation 流程。"
    },
    "WorkflowCoverageInsufficient": {
        "trigger": "TESTCASE_QUALITY_GATE (L3 Validator)",
        "condition": "cross_page_scenarios == 0 and page_count >= 2",
        "prompt_template": "模块 {module} 有 {page_count} 个页面但跨页面流程覆盖为 0。警告：可能缺失端到端业务流程测试。"
    },
    "TestDesignQualityRegressed": {
        "trigger": "TESTCASE_QUALITY_GATE (L3 Validator)",
        "condition": "new_score < old_score - 20",
        "prompt_template": "模块 {module} 页面 {page} 测试设计质量退化: score {old_score} → {new_score} (delta={delta})。建议审查变更。"
    },
    "AuditCompleted": {
        "trigger": "knowledge-manager (审计沉淀)",
        "condition": "overall_status != 'ok'",
        "prompt_template": "审计完成: Type={audit_type}, Module={module}, Status={overall_status}。报告: {report_path}。沉淀审计发现。"
    },

    # ── Safety Events (P0: Safety Auditor) ──
    "SafetyViolation": {
        "trigger": "safety-auditor (安全违规告警)",
        "condition": "severity == 'critical'",
        "prompt_template": "检测到安全违规: Module={module}, Severity={severity}, Rule={rule_id}, Count={violation_count}。{description}。建议: {suggestion}。"
    },
    "SafetyAuditCompleted": {
        "trigger": "knowledge-manager (安全审计沉淀)",
        "condition": "overall_status != 'ok'",
        "prompt_template": "安全审计完成: Module={module}, Status={overall_status}, Score={safety_score}, Violations={violation_count}。沉淀安全发现。"
    },

    # ── Online Monitoring Events (P0: Online Monitor) ──
    "OnlineMetricAnomaly": {
        "trigger": "online-monitor (指标异常告警)",
        "condition": "always",
        "prompt_template": "在线指标异常: Module={module}, Metric={metric}, Current={current_value}, Threshold={threshold}, Direction={direction}。{suggestion}。"
    },

    # ── Meta-Governance Review Events (P0: Architecture Review Skills) ──
    "ArchitectureRiskDetected": {
        "trigger": "review/architecture-assessment",
        "condition": "severity == 'critical'",
        "prompt_template": "检测到架构风险: Module={module}, Type={risk_type}, Severity={severity}。{description}。建议: {recommendation}。"
    },
    "GovernanceGapDetected": {
        "trigger": "review/governance-coverage",
        "condition": "risk_level == 'critical'",
        "prompt_template": "检测到治理盲区: Type={gap_type}, Modules={affected_modules}, Risk={risk_level}。建议: {recommendation}。"
    },
    "TechnicalDebtDetected": {
        "trigger": "review/token-efficiency (扩展: 综合技术债务检测)",
        "condition": "severity == 'critical'",
        "prompt_template": "检测到技术债务: Type={debt_type}, Location={location}, Severity={severity}, Est.Cost={estimated_cost}。建议: {recommendation}。"
    },
    "ProductionRiskDetected": {
        "trigger": "review/production-readiness",
        "condition": "is_blocker == true",
        "prompt_template": "检测到生产风险: Type={risk_type}, Severity={severity}, Blocker={is_blocker}。建议: {recommendation}。"
    },
    "ReviewCompleted": {
        "trigger": "review/* (所有 review skill 完成时)",
        "condition": "critical_count > 0",
        "prompt_template": "评审完成: Type={review_type}, Module={module}, Score={overall_score}, Critical={critical_count}, Warnings={warning_count}。报告: {report_path}。"
    },
}

# ── 订阅者注册表 ────────────────────────────────────────────────────
_subscribers: dict[str, list[Callable]] = {
    event_type: [] for event_type in EVENT_ACTIONS
}


@dataclass
class Event:
    """事件定义。"""
    id: str
    type: str  # AgentCompleted | BugClosed | CycleEnd | ContextUpdated
    timestamp: float
    data: dict
    processed: bool = False
    processed_at: float = 0.0
    result: str = ""

    @classmethod
    def create(cls, event_type: str, **kwargs) -> "Event":
        return cls(
            id=f"{event_type.lower()}-{uuid.uuid4().hex[:8]}",
            type=event_type,
            timestamp=time.time(),
            data=kwargs,
        )

    def to_file(self) -> Path:
        path = EVENT_DIR / f"{self.id}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, ensure_ascii=False, indent=2)
        return path

    @classmethod
    def from_file(cls, path: Path) -> "Event":
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        return cls(**d)


# ══════════════════════════════════════════════════════════════════════════
#  Event operations
# ══════════════════════════════════════════════════════════════════════════

def emit(event_type: str, **kwargs) -> Event:
    """发送事件并通知所有订阅者。"""
    if event_type not in EVENT_ACTIONS:
        raise ValueError(f"Unknown event type: {event_type}. Available: {list(EVENT_ACTIONS.keys())}")
    event = Event.create(event_type, **kwargs)
    event.to_file()
    _notify_subscribers(event)
    return event


def list_pending() -> list[Event]:
    """列出所有未处理的事件。"""
    events = []
    for f in sorted(EVENT_DIR.glob("*.json")):
        try:
            evt = Event.from_file(f)
            if not evt.processed:
                events.append(evt)
        except Exception as e:
            from aitest.infra.error_logger import log_error
            log_error("event_bus.list_pending", "read_event_file", e, {"file": str(f)})
    return events


def list_all(limit: int = 20) -> list[Event]:
    """列出最近的事件。"""
    events = []
    for f in sorted(EVENT_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            events.append(Event.from_file(f))
        except Exception as e:
            from aitest.infra.error_logger import log_error
            log_error("event_bus.list_all", "read_event_file", e, {"file": str(f)})
    return events[:limit]


def mark_processed(event_id: str, result: str = "") -> bool:
    """标记事件已处理。"""
    path = EVENT_DIR / f"{event_id}.json"
    if not path.exists():
        return False
    evt = Event.from_file(path)
    evt.processed = True
    evt.processed_at = time.time()
    evt.result = result
    evt.to_file()
    return True


def get_action(event_type: str) -> dict:
    """获取事件对应的 Knowledge Agent 动作。"""
    return EVENT_ACTIONS.get(event_type, {})


def process_pending() -> list[dict]:
    """处理所有待处理事件，返回每个事件的动作建议。"""
    pending = list_pending()
    results = []
    for evt in pending:
        action = get_action(evt.type)
        if action:
            # 检查条件
            condition_met = True
            if action["condition"] == "agent_status == 'success'":
                condition_met = evt.data.get("status") == "success"
            elif action["condition"] == "always":
                condition_met = True

            if condition_met:
                try:
                    prompt = action["prompt_template"].format(**evt.data) if evt.data else ""
                except KeyError:
                    prompt = action["prompt_template"] + " " + str(evt.data)
                results.append({
                    "event_id": evt.id,
                    "type": evt.type,
                    "timestamp": evt.timestamp,
                    "action": action["trigger"],
                    "prompt": prompt,
                    "data": evt.data,
                })
                mark_processed(evt.id, f"Action: {action['trigger']}")

    return results


# ══════════════════════════════════════════════════════════════════════════
#  订阅者模式
# ══════════════════════════════════════════════════════════════════════════

def subscribe(event_type: str, callback: Callable[[Event], None]) -> None:
    """注册事件订阅者。当指定类型的事件被 emit 时，自动调用 callback。"""
    if event_type not in _subscribers:
        raise ValueError(f"Unknown event type: {event_type}. Available: {list(_subscribers.keys())}")
    _subscribers[event_type].append(callback)


def _notify_subscribers(event: Event) -> None:
    """通知所有订阅者。在 emit() 中自动调用。"""
    for callback in _subscribers.get(event.type, []):
        try:
            callback(event)
        except Exception as e:
            from aitest.infra.error_logger import log_error
            log_error("event_bus._notify", "subscriber_callback", e, {"event_type": event.type, "event_id": event.id})


class KnowledgeAgentSubscriber:
    """
    Knowledge Agent 事件订阅者。

    监听 AgentCompleted / BugClosed / CycleEnd / ContextUpdated 事件，
    在事件发生时自动触发知识管理动作。

    用法:
        sub = KnowledgeAgentSubscriber(provider="claude")
        sub.activate()  # 注册到 event_bus，自动响应事件

        # 或者手动处理积压事件:
        results = sub.process_pending()
    """

    def __init__(self, provider: str = "claude", auto_process: bool = True):
        self.provider = provider
        self.auto_process = auto_process
        self._active = False
        self.processed_count = 0
        self._dedup_cache: set = set()  # W06: (event_type, file, content_hash) for idempotency
        self._dedup_max_size = 500      # Prevent unbounded growth

    def activate(self) -> None:
        """激活订阅——注册到 event_bus，事件发射时自动处理。"""
        if self._active:
            return
        for event_type in EVENT_ACTIONS:
            subscribe(event_type, self._on_event)
        self._active = True

    def deactivate(self) -> None:
        """取消订阅。"""
        for event_type in EVENT_ACTIONS:
            _subscribers[event_type] = [
                cb for cb in _subscribers[event_type] if cb != self._on_event
            ]
        self._active = False

    def _on_event(self, event: Event) -> None:
        """事件回调——自动处理单个事件。"""
        if not self.auto_process:
            return

        # W06: ContextUpdated idempotency — dedupe by (file, content_hash)
        if event.type == "ContextUpdated":
            dedup_key = (event.type, event.data.get("file", ""), event.data.get("content_hash", ""))
            if dedup_key in self._dedup_cache:
                return  # Already processed — skip
            self._dedup_cache.add(dedup_key)
            # Prune cache if it grows too large
            if len(self._dedup_cache) > self._dedup_max_size:
                self._dedup_cache = set(list(self._dedup_cache)[-self._dedup_max_size // 2:])

        action = get_action(event.type)
        if not action:
            return

        # 条件检查
        condition_met = True
        if action["condition"] == "agent_status == 'success'":
            condition_met = event.data.get("status") == "success"
        elif action["condition"] != "always":
            condition_met = True

        if condition_met:
            self._execute_knowledge_action(event, action)
            mark_processed(event.id, f"Auto-processed by KnowledgeAgent")
            self.processed_count += 1

    def _execute_knowledge_action(self, event: Event, action: dict) -> None:
        """执行知识管理动作——调用 knowledge-manager Skill。"""
        try:
            from aitest.agents.agent_runner import run_skill
            prompt = action["prompt_template"].format(**event.data) if event.data else str(event.data)
            run_skill(
                skill_id="knowledge/knowledge-manager",
                user_input=prompt,
                provider=self.provider,
                context_vars={"source_event": event.type, "event_data": event.data},
            )
        except Exception as e:
            from aitest.infra.error_logger import log_error
            log_error("event_bus.knowledge_subscriber", "execute_action", e, {"event_type": event.type, "event_id": event.id})

    def process_pending(self) -> list[dict]:
        """手动处理所有积压的未处理事件。"""
        return process_pending()


class ReviewAgentSubscriber:
    """
    Architecture Review Agent 事件订阅者 (P1).

    监听 Governance Events (StateDrift / SOPViolation / CostAnomaly /
    EvalRegressed / PromptChanged / AuditCompleted)，在事件发生时自动触发
    相应的 review skill 或 review graph run。

    用法:
        sub = ReviewAgentSubscriber(provider="claude", auto_trigger=False)
        sub.activate()  # 注册到 event_bus，事件发生时自动排队
        sub.process_triggered()  # 批量处理触发的评审
    """

    # Event → review mode mapping
    EVENT_REVIEW_MAP = {
        # Governance events → review mode
        "StateDrift":       "architecture",
        "SOPViolation":     "governance",
        "CostAnomaly":      "cost",
        "EvalRegressed":    "architecture",
        "PromptChanged":    "quality",
        "AuditCompleted":   "architecture",
        # Safety events → review mode
        "SafetyViolation":       "security",
        "SafetyAuditCompleted":  "security",
        # Online monitoring → review mode
        "OnlineMetricAnomaly":   "architecture",
        # Meta-review events → review mode (P0: close audit loop)
        "ArchitectureRiskDetected":   "architecture",
        "GovernanceGapDetected":      "governance",
        "TechnicalDebtDetected":      "debt",
        "ProductionRiskDetected":     "production",
        "ReviewCompleted":            "architecture",
    }

    def __init__(self, provider: str = "claude", auto_trigger: bool = False):
        self.provider = provider
        self.auto_trigger = auto_trigger  # True = run review immediately on event
        self._active = False
        self._triggered: list[dict] = []  # Queued review requests

    def activate(self) -> None:
        """注册到 event_bus，监听治理事件。"""
        if self._active:
            return
        for event_type in self.EVENT_REVIEW_MAP:
            try:
                subscribe(event_type, self._on_event)
            except ValueError:
                pass  # Event type may not be registered yet
        self._active = True

    def deactivate(self) -> None:
        """取消订阅。"""
        for event_type in self.EVENT_REVIEW_MAP:
            if event_type in _subscribers:
                _subscribers[event_type] = [
                    cb for cb in _subscribers[event_type] if cb != self._on_event
                ]
        self._active = False

    def _on_event(self, event: Event) -> None:
        """事件回调 — 排队或立即触发 review。"""
        review_mode = self.EVENT_REVIEW_MAP.get(event.type, "quick")
        entry = {
            "event_type": event.type,
            "event_id": event.id,
            "event_data": event.data,
            "review_mode": review_mode,
            "timestamp": event.timestamp,
        }
        self._triggered.append(entry)

        if self.auto_trigger:
            self._run_review_for_event(entry)
            mark_processed(event.id, f"Review triggered: {review_mode}")

    def _run_review_for_event(self, entry: dict) -> dict:
        """Execute a review run for a triggered event."""
        try:
            from aitest.graphs.review_graph import run_review
            return run_review(
                mode=entry["review_mode"],
                trigger=entry["event_type"],
                module=entry["event_data"].get("module", "system"),
            )
        except Exception as e:
            from aitest.infra.error_logger import log_error
            log_error("event_bus.review_subscriber", "run_review", e, entry)
            return {"status": "error", "error": str(e)}

    def process_triggered(self) -> list[dict]:
        """处理所有排队触发的评审请求。"""
        results = []
        for entry in self._triggered:
            result = self._run_review_for_event(entry)
            results.append({**entry, "result": result})
        self._triggered.clear()
        return results

    @property
    def pending_count(self) -> int:
        return len(self._triggered)


# ══════════════════════════════════════════════════════════════════════════
#  CLI
# ══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python event_bus.py emit|listen|process|watch|clean")
        print(f"Events dir: {EVENT_DIR}")
        print(f"Subscribers active: {sum(len(v) for v in _subscribers.values())}")
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "emit":
        if len(sys.argv) < 3:
            print("Usage: python event_bus.py emit <EventType> [key=value ...]")
            print(f"Types: {list(EVENT_ACTIONS.keys())}")
            sys.exit(1)

        event_type = sys.argv[2]
        data = {}
        for arg in sys.argv[3:]:
            if "=" in arg:
                k, v = arg.split("=", 1)
                data[k] = v

        evt = emit(event_type, **data)
        print(f"Emitted: {evt.id} ({evt.type})")

    elif cmd == "listen":
        pending = list_pending()
        print(f"Pending events: {len(pending)}")
        for evt in pending:
            print(f"  [{evt.type}] {evt.id} — {evt.data}")

    elif cmd == "process":
        results = process_pending()
        print(f"Processed: {len(results)} events")
        for r in results:
            print(f"  [{r['type']}] → {r['action']}")
            print(f"    Prompt: {r['prompt'][:120]}")

    elif cmd == "watch":
        # 持续监听模式 — Knowledge Agent 作为事件订阅者运行
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 60
        print(f"Knowledge Agent watching for events (interval={interval}s)...")
        print(f"Events dir: {EVENT_DIR}")
        print("Press Ctrl+C to stop.")

        sub = KnowledgeAgentSubscriber(auto_process=True)
        sub.activate()
        print(f"Subscriber activated: {sub._active}")
        print(f"Auto-process: {sub.auto_process}")

        try:
            while True:
                # 处理积压事件
                pending = list_pending()
                if pending:
                    print(f"\n[{time.strftime('%H:%M:%S')}] Processing {len(pending)} pending events...")
                    results = sub.process_pending()
                    for r in results:
                        print(f"  ✅ [{r['type']}] → {r['action']}")
                        print(f"     {r['prompt'][:100]}")
                    print(f"  Total processed: {sub.processed_count}")
                else:
                    print(f"[{time.strftime('%H:%M:%S')}] No pending events.", end="\r")

                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n\nKnowledge Agent stopped.")
            sub.deactivate()
            print(f"Total events processed: {sub.processed_count}")

    elif cmd == "clean":
        processed = 0
        for f in EVENT_DIR.glob("*.json"):
            try:
                evt = Event.from_file(f)
                if evt.processed and time.time() - evt.processed_at > 86400:  # 24h old
                    f.unlink()
                    processed += 1
            except Exception as e:
                from aitest.infra.error_logger import log_error
                log_error("event_bus.clean", "delete_old_event", e, {"file": str(f)})
        print(f"Cleaned {processed} old processed events")

    else:
        print(f"Unknown: {cmd}")
