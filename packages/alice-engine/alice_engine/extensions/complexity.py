"""ComplexityExtension — 任务复杂度评估。"""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ComplexityScore:
    """复杂度评分。"""

    module: str = ""
    page_count: int = 0
    estimated_seconds: float = 0.0
    level: str = "medium"  # "low" | "medium" | "high"
    factors: dict = None

    def __post_init__(self):
        if self.factors is None:
            self.factors = {}


class ComplexityExtension:
    """任务复杂度评估 Extension。

    根据页面数量、模块特性等因素评估任务复杂度，
    可用于资源调度和超时设置。

    用法:
        from alice_engine import Engine
        from alice_engine.extensions import ComplexityExtension

        ext = ComplexityExtension()
        engine = Engine(project=project, extensions=[ext])
        result = engine.run("equipment")

        print(ext.last_score.level)  # "low" | "medium" | "high"
    """

    def __init__(self, thresholds: dict | None = None):
        """
        Args:
            thresholds: 复杂度阈值 {"low": 3, "medium": 8}
        """
        self.thresholds = thresholds or {"low": 3, "medium": 8}
        self.last_score: ComplexityScore | None = None

    def on_init(self, engine) -> None:
        """Engine 初始化后调用。"""
        self.engine = engine

    def on_phase_end(self, module: str, phase: str, result: dict) -> None:
        """每个 Phase 完成后调用。"""
        pass

    def on_cycle_end(self, module: str, result) -> None:
        """完成后计算复杂度。"""
        pages = result.pages
        page_count = len(pages) if pages else 0

        level = "low"
        if page_count >= self.thresholds.get("medium", 8):
            level = "high"
        elif page_count >= self.thresholds.get("low", 3):
            level = "medium"

        self.last_score = ComplexityScore(
            module=module,
            page_count=page_count,
            estimated_seconds=result.elapsed_seconds,
            level=level,
            factors={
                "completed_phases": len(result.completed_phases),
                "failed_phases": len(result.failed_phases),
            },
        )

        logger.info("Complexity: %s = %s (%d pages)",
                     module, level, page_count)

    def estimate(self, module: str, pages: list[str]) -> ComplexityScore:
        """预估复杂度（不执行）。"""
        page_count = len(pages) if pages else 0

        level = "low"
        if page_count >= self.thresholds.get("medium", 8):
            level = "high"
        elif page_count >= self.thresholds.get("low", 3):
            level = "medium"

        # 粗略估计: 每页面 30-60 秒
        seconds_per_page = {"low": 20, "medium": 40, "high": 60}
        estimated = page_count * seconds_per_page.get(level, 40)

        return ComplexityScore(
            module=module,
            page_count=page_count,
            estimated_seconds=estimated,
            level=level,
        )
