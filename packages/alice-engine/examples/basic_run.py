"""基础用法 — 使用 Project 分离。"""

from alice_engine import Engine, Project

# 1. 创建 Project (配置和资源发现)
project = Project("D:/Desktop/TestingProject/ZJSN_Test-master526")
print(f"项目: {project.name}")
print(f"模块: {project.modules}")

# 2. 验证项目
validation = project.validate()
if not validation.valid:
    print("验证失败:")
    for err in validation.errors:
        print(f"  - {err}")
    exit(1)

# 3. 创建 Engine (执行引擎)
engine = Engine(project=project, llm_provider="mock")

# 4. 执行测试
result = engine.run("equipment", pages=["alarm-config"])

print(f"\n结果:")
print(f"  状态: {result.status}")
print(f"  成功: {result.success}")
print(f"  耗时: {result.elapsed_seconds}s")
print(f"  完成阶段: {result.completed_phases}")
