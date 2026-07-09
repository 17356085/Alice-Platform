# Executor Refactoring Progress

## 已完成 (Phase 1)

### 新模块创建

#### 1. `executor_utils.py` (155 行)
**职责**: 执行器工具函数
- `fix_stdout_encoding()`: Windows 编码修复
- `get_logger()`: 日志获取
- `get_project_dir()`, `get_test_project_root()`: 路径辅助
- `config`: 最小化配置类
- `TraceContext`: 线程本地跟踪上下文
- `get_tracer()`: No-op OpenTelemetry tracer

**从 executor.py 提取的行数**: ~140 行 (第29-169行)

#### 2. `agent_helpers.py` (105 行)
**职责**: Agent 定义与 skill 执行辅助
- `get_agent_skill_map()`, `get_dev_agent_skill_map()`: Skill map 加载
- `get_agent_definition()`: Agent 定义查询
- `run_skill()`: Skill 执行包装器
- `list_agents()`, `list_dev_agents()`: Agent 列表

**从 executor.py 提取的行数**: ~100 行 (第86-169行 + 第1190-1218行)

#### 3. `test_executor_refactor.py` (125 行)
**职责**: 新模块的单元测试
- 覆盖 `executor_utils` 的所有导出
- 覆盖 `agent_helpers` 的所有导出
- 验证向后兼容性

### 净减少 executor.py 行数
- 原始: 1218 行
- 提取: ~240 行辅助函数
- 预期剩余: ~978 行

---

## 待完成 (Phase 2)

### 1. 更新 executor.py 导入
**状态**: 部分完成
- ✅ 删除了 `fix_stdout_encoding()` 函数定义
- ⏳ 需要将所有辅助函数的定义替换为从新模块导入
- ⏳ 需要更新 `AGENT_SKILL_MAP` 和 `DEV_AGENT_SKILL_MAP` 的初始化方式

**具体改动**:
```python
# 替换第66-169行的所有辅助函数定义为:
from alice_engine.core.executor_utils import (
    get_logger, get_project_dir, get_test_project_root,
    config, TraceContext, get_tracer,
)
from alice_engine.core.agent_helpers import (
    get_agent_skill_map, get_dev_agent_skill_map,
    get_agent_definition, run_skill,
    list_agents, list_dev_agents,
)

# 向后兼容: 模块级别暴露
AGENT_SKILL_MAP = get_agent_skill_map()
DEV_AGENT_SKILL_MAP = get_dev_agent_skill_map()
```

### 2. 删除冗余定义
**目标行**: 第72-169行
- 删除 `get_logger()` (第72-74行)
- 删除 `get_project_dir()` (第77-79行)
- 删除 `get_test_project_root()` (第82-84行)
- 删除 `_get_governance_root()` (第88-91行)
- 删除 `_get_defs()` (第93-97行)
- 删除 `get_agent_definition()` (第102-104行)
- 删除 `run_skill()` (第107-119行)
- 删除 `_Config` (第122-132行)
- 删除 `_TraceContext` (第135-148行)
- 删除 `_NoopSpan`, `_NoopTracer`, `get_tracer()` (第151-162行)

### 3. 删除冗余函数
**目标行**: 第1190-1218行
- 删除 `run_agent()` 包装器 (可选，保留向后兼容)
- 删除 `list_agents()` 和 `list_dev_agents()` (第1209-1218行)

### 4. 运行测试验证
```bash
# SDK 测试
uv run pytest packages/alice-engine/tests/test_executor_refactor.py -v
uv run pytest packages/alice-engine/tests/test_sdk_boundary.py -v

# 全量测试
uv run pytest packages/alice-engine/tests -v
uv run pytest aitest/tests -v
```

---

## 进一步拆分建议 (Phase 3)

### 候选拆分点

#### 1. 路径解析逻辑 → `executor_path_resolver.py`
**当前位置**: `AgentLoop` 类内 (第419-459行)
- `_slug_to_page_name()`
- `_page_slug_to_underscore()`
- `_resolve_artifact_path()`
- `_resolve_path()`

**理由**: 这些是纯函数，不依赖 AgentLoop 状态

#### 2. 用户输入构建 → `executor_prompt_builder.py`
**当前位置**: `AgentLoop` 类内 (第480-547行)
- `_build_user_input()`: 构建 skill 的 user prompt

**理由**: 150+ 行逻辑，职责单一，可测试性强

#### 3. 产出持久化 → 已有 `output_persistence.py`
**当前位置**: `AgentLoop` 类内 (第685-786行)
- `_save_skill_output()`: 委托给 `output_persistence.py`
- `_persist_skill_artifact()`: 60+ 行逻辑
- `_persist_consistency_report()`: 委托
- `_persist_review_report()`: 委托

**建议**: 将 `_persist_skill_artifact()` 的实现移到 `output_persistence.py`

#### 4. 核心保留: AgentLoop orchestration
**保留在 executor.py**:
- `AgentLoop` 类初始化 (第205-340行)
- PAOU 循环方法: `perceive()`, `plan()`, `act()`, `observe()`, `update()` (第556-924行)
- Session 管理: `_do_continuation()`, `run()`, `_finalize_session()` (第938-1098行)
- 主循环: `_run_single_session()`, `run_interactive()` (第1104-1182行)

**最终目标行数**: ~600-700 行（仍然是核心协调器）

---

## 不拆分的理由

### AgentLoop 应保持整体性
- **职责明确**: AgentLoop 是执行器的协调中心
- **高内聚**: PAOU 循环方法紧密协作
- **低耦合**: 已通过委托将重型逻辑外移
- **可读性**: 保持 PAOU 循环在同一个类中更易理解

### 已通过委托实现解耦
- Planner → `planner.py`
- State updater → `state_machine.py`
- Session orchestration → `session_orchestrator.py`
- Runtime lifecycle → `runtime_lifecycle.py`
- Context building → `runtime_context_builder.py`

---

## 验收标准

### Phase 2 完成标准
- [ ] `executor.py` 不再包含辅助函数定义
- [ ] `executor.py` 从新模块导入所有辅助函数
- [ ] 向后兼容: `from alice_engine.core.executor import AGENT_SKILL_MAP, run_agent, list_agents` 仍然有效
- [ ] SDK 测试通过: `packages/alice-engine/tests` 105 passed
- [ ] 平台测试通过: `aitest/tests` 1328 passed

### Phase 3 完成标准 (可选)
- [ ] 路径解析逻辑提取到独立模块
- [ ] 用户输入构建逻辑提取到独立模块
- [ ] `_persist_skill_artifact()` 移到 `output_persistence.py`
- [ ] `executor.py` 降至 ~700 行
- [ ] 所有测试仍通过

---

## 风险与缓解

### 风险 1: 循环导入
**场景**: 新模块导入 `executor.py` 中的类型
**缓解**: 
- 使用 `from __future__ import annotations`
- 类型提示用字符串 `"AgentLoop"`
- 避免运行时导入 executor

### 风险 2: 向后兼容性破坏
**场景**: 外部代码直接导入内部辅助函数
**缓解**:
- 在 `executor.py` 保留 re-export
- 在 `__init__.py` 暴露公开 API
- 添加 deprecation warning

### 风险 3: 测试失败
**场景**: 重构导致行为变化
**缓解**:
- 每步改动后运行测试
- 保持小步提交
- 失败立即回滚

---

## 下一步行动

1. ✅ **创建新模块** (已完成)
   - `executor_utils.py`
   - `agent_helpers.py`
   - `test_executor_refactor.py`

2. ⏳ **更新 executor.py 导入** (进行中)
   - 替换辅助函数定义为导入
   - 验证语法正确

3. ⏳ **运行测试**
   - `uv run pytest packages/alice-engine/tests/test_executor_refactor.py`
   - `uv run pytest packages/alice-engine/tests`

4. ⏳ **删除冗余定义**
   - 确认测试通过后删除旧定义

5. ⏳ **Phase 3 拆分** (可选)
   - 根据测试结果决定是否继续

---

## 当前状态总结

**已完成**: 
- ✅ 创建 2 个新模块 (260 行代码)
- ✅ 编写单元测试 (125 行)
- ✅ 部分更新 executor.py 导入

**当前 executor.py 状态**:
- 行数: 1211 行 (删除了 `fix_stdout_encoding()` 定义)
- 仍包含: ~140 行待删除的辅助函数定义

**阻塞点**:
- 需要完整替换第66-169行的辅助函数定义
- 需要在有 pytest 的环境中运行测试验证

**预期最终状态**:
- `executor.py`: ~970 行 (Phase 2) 或 ~700 行 (Phase 3)
- 新增 2 个辅助模块: 260 行
- 净效果: 代码更模块化，职责更清晰，executor.py 更聚焦核心协调逻辑
