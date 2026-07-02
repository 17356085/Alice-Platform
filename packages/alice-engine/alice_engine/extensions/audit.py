"""AuditExtension — 执行审计，记录每个阶段的状态变化。"""

import logging
import time
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class AuditEntry:
    """单条审计记录。"""

    timestamp: float = 0.0
    phase: str = ""
    module: str = ""
    event: str = ""
    data: dict = field(default_factory=dict)


class AuditExtension:
    """执行审计 Extension。

    记录 Engine 执行过程中的所有阶段变化，用于调试和可观测性。

    用法:
        from alice_engine import Engine
        from alice_engine.extensions import AuditExtension

        audit = AuditExtension()
        engine = Engine(project=project, extensions=[audit])
        result = engine.run("equipment")

        # 查看审计日志
        for entry in audit.entries:
            print(f"{entry.phase}: {entry.event}")
    """

    def __init__(self):
        self.entries: list[AuditEntry] = []

    def on_init(self, engine) -> None:
        """Engine 初始化后调用。"""
        self.entries.append(AuditEntry(
            timestamp=time.time(),
            event="engine_init",
            data={"project": str(engine.project.path)},
        ))
        logger.info("Audit: engine initialized")

    def on_phase_end(self, module: str, phase: str, result: dict) -> None:
        """每个 Phase 完成后调用。"""
        entry = AuditEntry(
            timestamp=time.time(),
            phase=phase,
            module=module,
            event="phase_complete",
            data=result,
        )
        self.entries.append(entry)
        logger.info("Audit: %s/%s completed", module, phase)

    def on_cycle_end(self, module: str, result) -> None:
        """整个 SOP 完成后调用。"""
        entry = AuditEntry(
            timestamp=time.time(),
            module=module,
            event="cycle_complete",
            data={
                "status": result.status,
                "elapsed": result.elapsed_seconds,
                "phases": result.completed_phases,
            },
        )
        self.entries.append(entry)
        logger.info("Audit: %s completed (%s, %.1fs)",
                     module, result.status, result.elapsed_seconds)

    def summary(self) -> dict:
        """返回审计摘要。"""
        return {
            "total_entries": len(self.entries),
            "phases": [e.phase for e in self.entries if e.phase],
            "events": [e.event for e in self.entries],
        }
