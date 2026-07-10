# SDK 迁移清理计划

**状态**: 70% 完成 → 目标: 85%  
**工作量**: 2-3 周  
**风险**: 低（主要是清理工作）

---

## 快速摘要

SDK 提取工作**执行良好**。大部分核心逻辑已在 `alice-engine` 中。剩余工作是：

1. **删除**已弃用/重复代码
2. **明确** 3-4 个目录的归属
3. **验证** SDK 可以独立运行

---

## 阶段 1: 审计（3 天）

运行这些命令并记录结果：

```bash
# 1. 检查 SDK 没有平台依赖
cd packages/alice-engine
grep -r "from aitest\." alice_engine/ | grep -v "test" | grep -v "__pycache__"
# 预期：空（或仅测试导入）

# 2. 检查 CLI 使用 SDK 公共 API
cd ../..
grep -r "from aitest\.engine\." aitest/cli/
grep -r "from aitest\.graphs\." aitest/cli/
grep -r "from aitest\.llm\." aitest/cli/
# 预期：空（应使用 "from alice_engine import ..."）

# 3. 检查发现重复
grep -r "from aitest\.discovery" . | grep -v "__pycache__"
# 如果有结果 → 需要迁移

# 4. 检查弃用的 provider 使用
grep -r "from aitest\.llm\.providers" . | grep -v "__pycache__"
# 如果为空 → 可以删除 aitest/llm/providers/

# 5. 检查 aitest/runtime/ 依赖
cd aitest/runtime
grep -r "^from aitest\." *.py | grep -v "from aitest.runtime"
grep -r "^from alice_engine" *.py
# 确定：这是 SDK 级别还是平台级别？
```

**交付物**: `docs/architecture/cleanup-audit-YYYY-MM-DD.md` 附带发现。

---

## 阶段 2: 清理（1 周）

### 任务 1: 删除重复项

如果审计确认这些未使用：

```bash
# 删除弃用的 providers（如果 grep 未找到使用情况）
rm -rf aitest/llm/providers/
git commit -m "chore: 删除弃用的 llm providers（现在在 alice-engine 中）"

# 删除重复的 discovery（如果到处都使用 alice-discovery）
rm -rf aitest/discovery/
git commit -m "chore: 删除重复的 discovery 模块（使用 alice-discovery 包）"
```

### 任务 2: 解决 `aitest/runtime/` 归属

根据审计发现：

**选项 A**: 移至 SDK（如果被 SDK 使用）
```bash
mv aitest/runtime/* packages/alice-engine/alice_engine/runtime/utils/
# 更新整个代码库的导入
git commit -m "refactor: 将 runtime 工具移至 SDK"
```

**选项 B**: 移至平台（如果仅被平台使用）
```bash
mv aitest/runtime/* aitest/infra/runtime/
# 更新导入
git commit -m "refactor: 将 runtime 工具移至平台 infra"
```

**选项 C**: 拆分（如果混合使用）
- SDK 级别工具 → `alice-engine/runtime/utils/`
- 平台级别工具 → `aitest/infra/runtime/`

### 任务 3: 明确 `aitest/graphs/` vs SDK workflow

比较文件：
```bash
diff aitest/graphs/state.py packages/alice-engine/alice_engine/workflow/state.py
```

**如果重复** → 合并到 SDK  
**如果平台特定** → 重命名为 `aitest/platform/workflow_utils/` 以明确

---

## 阶段 3: 重构 CLI（3-4 天）

用 SDK 公共 API 替换内部导入：

```python
# 之前（坏）
from aitest.graphs.sop_graph import build_graph
from aitest.engine.executor import AgentLoop

# 之后（好）
from alice_engine import Engine
from alice_engine.workflow import WorkflowBuilder
```

**策略**: 一次一个 CLI 命令。每次更改后测试。

---

## 阶段 4: 验证（2 天）

### 独立 SDK 测试

```bash
# 创建干净的测试环境
mkdir /tmp/sdk-standalone-test
cd /tmp/sdk-standalone-test
python -m venv .venv
source .venv/bin/activate

# 仅安装 SDK（不是平台）
pip install /path/to/packages/alice-engine
pip install /path/to/packages/alice-governance

# 编写测试脚本
cat > test_sdk.py << 'EOF'
from alice_engine import Engine, Project

project = Project("./test-project")
engine = Engine(project=project)
result = engine.run("equipment", pages=["alarm-config"])
print(f"Status: {result['status']}")
EOF

# 运行测试
python test_sdk.py
```

**成功标准**: 脚本运行时不在任何地方导入 `aitest.*`。

---

## 阶段 5: 文档（2 天）

更新文档：

1. **ADR**: 用最终结构更新 `docs/adr/ADR_002_SDK_ARCHITECTURE.md`
2. **README**: 向 `packages/alice-engine/README.md` 添加 SDK 使用示例
3. **迁移指南**: 创建 `docs/guides/platform-to-sdk-migration.md`

---

## 验证清单

在认为迁移完成之前：

- [ ] `grep -r "from aitest\." packages/alice-engine/` 不返回结果（测试除外）
- [ ] `grep -r "from aitest\.engine\." aitest/cli/` 不返回结果
- [ ] `grep -r "from aitest\.graphs\." aitest/cli/` 不返回结果
- [ ] 没有重复模块（discovery、providers）
- [ ] `aitest/runtime/` 归属已记录
- [ ] 独立 SDK 测试通过
- [ ] CI/CD 通过所有测试

---

## 风险缓解

**低风险项目**（安全执行）:
- 删除弃用的 `aitest/llm/providers/`（在 grep 确认未使用后）
- 删除重复的 `aitest/discovery/`（迁移后）

**中等风险项目**（彻底测试）:
- 移动 `aitest/runtime/` 文件
- 重构 CLI 导入

**策略**: 进行小提交。每次更改后测试。可以轻松回滚。

---

## 时间线

| 周 | 重点 | 交付物 |
|----|------|--------|
| 第 1 周 | 审计 + 简单删除 | 审计报告，删除重复项 |
| 第 2 周 | Runtime 归属 + CLI 重构 | 代码移动/重构，测试通过 |
| 第 3 周 | 验证 + 文档 | 独立测试，文档更新 |

---

## 成功指标

**之前**: 70% 完成，4-5 个不明确的归属区域  
**之后**: 85%+ 完成，所有归属已记录  
**SDK 状态**: 可以发布到 PyPI 并独立使用

---

## 审计期间需要解决的问题

1. **aitest/runtime/**: SDK 还是平台？检查导入。
2. **aitest/graphs/**: 重复还是平台特定？与 SDK 比较。
3. **aitest/agents/**: 与 SDK agents 重叠？检查重复。
4. **aitest/adapters/**: 实现 SDK 接口还是重复 SDK？明确。
5. **aitest/audit_engine/**: 包含属于治理的验证逻辑？
6. **aitest/knowledge/**: 通用 RAG（SDK）还是平台特定（平台）？

---

## 联系方式

有问题？在 `#architecture` 频道讨论或在此文档上评论。
