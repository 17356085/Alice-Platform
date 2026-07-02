"""Extension 用法 — 自定义扩展。"""

from alice_engine import Engine, Project, RunResult


class TimingExtension:
    """记录执行耗时的扩展。"""

    def on_init(self, engine):
        print(f"[Timing] Engine 初始化: {engine.project.name}")

    def on_phase_end(self, module, phase, result):
        print(f"[Timing] Phase {phase} 完成")

    def on_cycle_end(self, module, result: RunResult):
        print(f"[Timing] 全部完成: {result.elapsed_seconds}s")


class ReportExtension:
    """生成报告的扩展。"""

    def on_init(self, engine):
        pass

    def on_phase_end(self, module, phase, result):
        pass

    def on_cycle_end(self, module, result: RunResult):
        print(f"\n{'='*50}")
        print(f"测试报告 — {module}")
        print(f"状态: {result.status}")
        print(f"耗时: {result.elapsed_seconds}s")
        print(f"{'='*50}\n")


# 使用
project = Project("D:/Desktop/TestingProject/ZJSN_Test-master526")
engine = Engine(
    project=project,
    llm_provider="mock",
    extensions=[TimingExtension(), ReportExtension()],
)

result = engine.run("equipment", pages=["alarm-config"])
print(f"最终状态: {result.status}")
