# Quickstart

## 安装

```bash
pip install alice-engine
```

## 5 分钟上手

### 1. 准备项目配置

在项目根目录创建 `.tlo/project.yaml`:

```yaml
name: my-project
url: https://example.com
tech_stack:
  framework: vue3
  ui: element-plus
test_framework: pytest
modules:
  - equipment
  - tank
```

### 2. 编写测试脚本

```python
from alice_engine import Engine

engine = Engine(project_path="./my-project", llm_provider="mock")
result = engine.run("equipment", pages=["alarm-config"])

assert result.success, f"测试失败: {result.failed_phases}"
print(f"通过! 耗时 {result.elapsed_seconds}s")
```

### 3. 运行

```bash
python test_equipment.py
```

## 下一步

- [API Reference](api-reference.md) — 完整 API 文档
- [Extensions](extensions.md) — 编写自定义扩展
- [Migration](migration.md) — 从 aitest 迁移
