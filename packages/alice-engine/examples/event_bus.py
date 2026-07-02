"""EventBus 用法 — 监听引擎事件。"""

from alice_engine import Engine, EventBus

# 创建事件总线
bus = EventBus()

# 注册事件处理器
bus.subscribe("run_start", lambda d: print(f"▶ 开始: {d['module']} / {d['pages']}"))
bus.subscribe("phase_start", lambda d: print(f"  ⏳ {d['phase']}..."))
bus.subscribe("phase_complete", lambda d: print(f"  ✓ {d['phase']}"))
bus.subscribe("complete", lambda d: print(f"■ 完成: {d['status']} ({d['elapsed_seconds']}s)"))
bus.subscribe("error", lambda d: print(f"✗ 错误: {d.get('message', 'unknown')}"))

# 创建 Engine 并执行
engine = Engine(
    project_path="D:/Desktop/TestingProject/ZJSN_Test-master526",
    llm_provider="mock",
    event_bus=bus,
)

result = engine.run("equipment", pages=["alarm-config"])
print(f"\n结果: {result.status}")
