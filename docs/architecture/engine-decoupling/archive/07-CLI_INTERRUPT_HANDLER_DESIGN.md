# CLI Interrupt Handler 设计

> 架构解耦分析 — 文档 7/7
> 核心问题: CLI 模式下，每个 Phase 完成后怎么让用户审查、修改、决策?

## 1. 设计决策记录

| 问题 | 决策 |
|------|------|
| 哪些 Phase 暂停? | **全部 9 个 Phase 都暂停** |
| 暂停时能做什么? | 混合方案: 摘要展示 + v 查看 + e 修改 + r 重新生成 + s 跳过 |
| 修改后怎么处理? | 重新读取 + 严格合法性检查 (B) |
| reject 后怎么办? | 用户给修改意见 → AI 重新生成 → 再审核 (D→B→审核) |
| CLI 交互格式? | 展示内容摘要 + 审批 (方案 C) |
| 和现有 HITL 关系? | 替换现有 HITL (方案 A) |

## 2. 9 个暂停点

### 2.1 暂停点清单

| # | Phase | 触发时机 | 展示内容 | 可用操作 |
|---|-------|----------|----------|----------|
| 1 | Project Init | PROJECT_CONTEXT.md 生成后 | 项目概览、模块数、页面数 | v/e/r/s |
| 2 | Requirement | MODULE_CONTEXT.md 生成后 | 模块概览、页面列表、业务流程 | v/e/r/s |
| 3 | Test Design | TEST_DESIGN.md + TEST_CASES.md 生成后 | 测试场景数、用例数、P0 数 | v/e/r/s |
| 4 | Automation | AUTO_STRATEGY.md + 代码生成后 | 策略摘要、生成的文件列表 | v/e/r/s |
| 5 | Execute & Debug | pytest 执行完成后 | 通过/失败/错误数、耗时、失败用例列表 | v/s |
| 6 | Bug Analysis | 分析完成后 | 失败原因分类、修复建议 | v/e/s |
| 7 | Data Sanitization | 脏数据扫描完成后 | 要清理的数据清单、条目数、类型 | v/确认清理/s |
| 8 | Report | 报告生成后 | 报告文件路径 + 内容摘要 | v/s |
| 9 | Knowledge | 知识沉淀后 | 沉淀位置 + 内容摘要 | v/s |

### 2.2 暂停点详情

#### Phase 1: Project Init

```
━━━ Phase 1/9: Project Init ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  正在生成 PROJECT_CONTEXT.md...
  ✅ 完成 (3.2s)

┌──────────────────────────────────────────────────────────────┐
│ Phase 1: Project Init — 完成                                  │
│                                                               │
│ 生成文件:                                                     │
│   📄 PROJECT_CONTEXT.md                                       │
│     - 项目概览: 鞍集涂源管理系统                               │
│     - 模块数: 5 个                                            │
│     - 页面数: 12 个                                           │
│                                                               │
│ 操作: [Enter] 继续  [v] 查看  [e] 修改  [r] 重新生成  [s] 跳过│
│ >                                                             │
└──────────────────────────────────────────────────────────────┘
```

**合法性检查**:
- 文件非空
- 包含 `#` 标题
- 包含模块列表

#### Phase 2: Requirement

```
┌──────────────────────────────────────────────────────────────┐
│ Phase 2: Requirement — 完成                                   │
│                                                               │
│ 生成文件:                                                     │
│   📄 MODULE_CONTEXT.md                                        │
│     - 模块: equipment (设备管理)                               │
│     - 页面: 4 个 (alarm-config, camera, key-param, maintenance)│
│     - 业务流程: 3 条                                          │
│                                                               │
│ 操作: [Enter] 继续  [v] 查看  [e] 修改  [r] 重新生成  [s] 跳过│
│ >                                                             │
└──────────────────────────────────────────────────────────────┘
```

**合法性检查**:
- 文件非空
- 包含 `#` 标题
- 包含页面列表

#### Phase 3: Test Design

```
┌──────────────────────────────────────────────────────────────┐
│ Phase 3: Test Design — 完成                                   │
│                                                               │
│ 生成文件:                                                     │
│   📄 TEST_DESIGN.md                                           │
│     - 测试场景: 15 个                                         │
│     - 风险点: 8 个                                            │
│                                                               │
│   📄 TEST_CASES.md                                            │
│     - 测试用例: 37 个                                         │
│     - P0 用例: 3 个                                           │
│     - P1 用例: 12 个                                          │
│                                                               │
│ 操作: [Enter] 继续  [v] 查看  [e] 修改  [r] 重新生成  [s] 跳过│
│ >                                                             │
└──────────────────────────────────────────────────────────────┘
```

**合法性检查**:
- TEST_DESIGN.md 非空、包含测试场景、有 BS-XXX 编号
- TEST_CASES.md 非空、包含测试用例、有 TC-XXX 编号、有 P0/P1 标记

#### Phase 4: Automation

```
┌──────────────────────────────────────────────────────────────┐
│ Phase 4: Automation — 完成                                    │
│                                                               │
│ 生成文件:                                                     │
│   📄 AUTO_STRATEGY.md                                         │
│     - 定位器策略: 优先 CSS 选择器                              │
│     - 等待策略: wait_vue_stable                               │
│                                                               │
│   📄 page/equipment_page/AlarmConfigPage.py                   │
│   📄 script/equipment/test_alarm_config.py                    │
│   📄 page/equipment_page/CameraPage.py                        │
│   📄 script/equipment/test_camera.py                          │
│                                                               │
│ 操作: [Enter] 继续  [v] 查看  [e] 修改  [r] 重新生成  [s] 跳过│
│ >                                                             │
└──────────────────────────────────────────────────────────────┘
```

**合法性检查**:
- AUTO_STRATEGY.md 非空、包含定位器策略、包含等待策略
- PageObject.py: Python 语法正确、能被 import
- test_*.py: Python 语法正确、能被 pytest 收集

#### Phase 5: Execute & Debug

```
━━━ Phase 5/9: Execute & Debug ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  正在执行 pytest...
  ✅ 完成 (45.2s)

┌──────────────────────────────────────────────────────────────┐
│ Phase 5: Execute & Debug — 执行完成                           │
│                                                               │
│ 测试结果:                                                     │
│   ✅ 通过: 8 个                                               │
│   ❌ 失败: 3 个                                               │
│   ⚠️  错误: 1 个                                              │
│   ⏱️  耗时: 45.2s                                             │
│                                                               │
│ 失败用例:                                                     │
│   ❌ test_alarm_config.py::test_add_alarm — AssertionError    │
│   ❌ test_alarm_config.py::test_edit_alarm — TimeoutError     │
│   ❌ test_camera.py::test_camera_preview — ElementNotFound    │
│   ⚠️  test_camera.py::test_camera_settings — WebDriverError  │
│                                                               │
│ 操作: [Enter] 继续  [v] 查看详细报告  [s] 跳过               │
│ >                                                             │
└──────────────────────────────────────────────────────────────┘
```

**无合法性检查** — 结果由 pytest 决定。

#### Phase 6: Bug Analysis

```
┌──────────────────────────────────────────────────────────────┐
│ Phase 6: Bug Analysis — 完成                                  │
│                                                               │
│ 分析结果:                                                     │
│   🔍 3 个失败用例分析完成                                      │
│                                                               │
│ ❌ test_add_alarm — AssertionError                            │
│   原因: 保存后未等待页面刷新                                   │
│   修复: 添加 wait_vue_stable() 后重试断言                      │
│                                                               │
│ ❌ test_edit_alarm — TimeoutError                             │
│   原因: 编辑弹窗加载超时                                       │
│   修复: 增加显式等待时间到 10s                                  │
│                                                               │
│ ❌ test_camera_preview — ElementNotFound                      │
│   原因: 页面路由未正确跳转                                     │
│   修复: 先导航到正确的菜单路径                                  │
│                                                               │
│ 操作: [Enter] 继续  [v] 查看完整分析  [e] 修改修复建议  [s] 跳过│
│ >                                                             │
└──────────────────────────────────────────────────────────────┘
```

**合法性检查**:
- 分析报告非空
- 每个失败用例有原因和修复建议

#### Phase 7: Data Sanitization

```
┌──────────────────────────────────────────────────────────────┐
│ Phase 7: Data Sanitization — 扫描完成                         │
│                                                               │
│ 发现测试残留数据:                                              │
│   🗑️  测试告警配置: 3 条                                      │
│      - "测试告警_001" (设备 A-001)                             │
│      - "测试告警_002" (设备 A-002)                             │
│      - "测试告警_003" (设备 A-003)                             │
│                                                               │
│   🗑️  测试摄像头配置: 2 条                                    │
│      - "测试摄像头_001"                                        │
│      - "测试摄像头_002"                                        │
│                                                               │
│   🗑️  测试用户账号: 1 个                                      │
│      - "test_user_001"                                        │
│                                                               │
│ 总计: 6 条残留数据                                             │
│                                                               │
│ 操作: [Enter] 清理  [v] 查看详情  [s] 跳过 (保留脏数据)       │
│ >                                                             │
└──────────────────────────────────────────────────────────────┘
```

**无合法性检查** — 由用户决定是否清理。

#### Phase 8: Report

```
┌──────────────────────────────────────────────────────────────┐
│ Phase 8: Report — 完成                                        │
│                                                               │
│ 生成文件:                                                     │
│   📄 governance/artifacts/TEST_REPORT_equipment.md            │
│                                                               │
│ 报告摘要:                                                     │
│   - 总用例: 12                                                │
│   - 通过: 8 (66.7%)                                           │
│   - 失败: 3 (25.0%)                                           │
│   - 错误: 1 (8.3%)                                            │
│   - 耗时: 45.2s                                               │
│                                                               │
│ 操作: [Enter] 继续  [v] 查看报告  [s] 跳过                   │
│ >                                                             │
└──────────────────────────────────────────────────────────────┘
```

#### Phase 9: Knowledge

```
┌──────────────────────────────────────────────────────────────┐
│ Phase 9: Knowledge — 完成                                     │
│                                                               │
│ 知识沉淀:                                                     │
│   📁 .tlo/knowledge/modules/equipment/pages/alarm-config/     │
│     - PAGE_CONTEXT.md (已更新)                                 │
│     - TEST_CASES.md (已更新)                                   │
│                                                               │
│   📁 .tlo/knowledge/modules/equipment/                        │
│     - MODULE_CONTEXT.md (已更新)                               │
│     - bug_patterns.json (新增: 3 条 Bug 模式)                 │
│                                                               │
│ 操作: [Enter] 继续  [v] 查看沉淀内容  [s] 跳过               │
│ >                                                             │
└──────────────────────────────────────────────────────────────┘
```

## 3. 操作定义

### 3.1 操作列表

| 操作 | 按键 | 含义 | 适用阶段 |
|------|------|------|----------|
| **继续** | `Enter` | 用当前版本进入下一阶段 | 全部 |
| **查看** | `v` | 打开编辑器查看文件内容 | 全部 |
| **修改** | `e` | 打开编辑器修改文件 | 生成文档的阶段 |
| **重新生成** | `r` | 给修改意见，让 AI 重新生成 | 生成文档的阶段 |
| **跳过** | `s` | 不执行/不清理/不生成 | 执行/清理阶段 |

### 3.2 操作流程图

```
暂停点展示
    │
    ├── Enter → 继续 → 下一 Phase
    │
    ├── v → 打开编辑器查看 → 关闭编辑器 → 回到暂停点
    │
    ├── e → 打开编辑器修改 → 关闭编辑器 → 合法性检查
    │       ├── ✅ 通过 → 回到暂停点 (文件已更新)
    │       └── ❌ 不通过 → 提示错误 → 回到暂停点
    │
    ├── r → 输入修改意见 → AI 重新生成 → 合法性检查
    │       ├── ✅ 通过 → 展示新版本 → 回到暂停点
    │       └── ❌ 不通过 → 提示错误 → 回到暂停点
    │
    └── s → 跳过 → 下一 Phase
```

## 4. 合法性检查

### 4.1 检查规则

| Phase | 文件 | 检查项 |
|-------|------|--------|
| 1 | PROJECT_CONTEXT.md | 非空、包含 `#` 标题、包含模块列表 |
| 2 | MODULE_CONTEXT.md | 非空、包含 `#` 标题、包含页面列表 |
| 3 | TEST_DESIGN.md | 非空、包含测试场景、有 BS-XXX 编号 |
| 3 | TEST_CASES.md | 非空、包含测试用例、有 TC-XXX 编号、有 P0/P1 标记 |
| 4 | AUTO_STRATEGY.md | 非空、包含定位器策略、包含等待策略 |
| 4 | PageObject.py | Python 语法正确、能被 import |
| 4 | test_*.py | Python 语法正确、能被 pytest 收集 |
| 6 | Bug 分析报告 | 非空、每个失败用例有原因和修复建议 |

### 4.2 检查失败提示

```
  🔍 验证修改...
    ✅ 文件非空
    ✅ 包含 `#` 标题
    ❌ 缺少模块列表

  ⚠️  修改不合法，请重新编辑。
  缺少: 模块列表 (至少需要列出一个模块)

  操作: [Enter] 继续  [v] 查看  [e] 修改  [r] 重新生成  [s] 跳过
  >
```

## 5. Reject 流程 (重新生成)

### 5.1 流程

```
用户输入 r
    │
    ▼
┌──────────────────────────────────────────┐
│ 请描述修改意见:                           │
│ > 定位器应该优先用 CSS，不要用 XPath      │
└──────────────────────────────────────────┘
    │
    ▼
AI 重新生成 (携带修改意见作为额外上下文)
    │
    ▼
合法性检查
    ├── ✅ 通过 → 展示新版本摘要 → 回到暂停点
    └── ❌ 不通过 → 提示错误 → 回到暂停点
    │
    ▼
用户可以:
  - Enter → 接受新版本，继续
  - v → 查看新版本
  - e → 手动修改新版本
  - r → 再次重新生成 (循环)
```

### 5.2 重新生成时 AI 收到的上下文

```python
# 原始 Skill 提示
skill_prompt = "生成 AUTO_STRATEGY.md..."

# 用户修改意见 (追加到提示末尾)
user_feedback = "定位器应该优先用 CSS，不要用 XPath"

# 完整提示
full_prompt = f"{skill_prompt}\n\n用户修改意见: {user_feedback}"
```

## 6. CLIInterruptHandler 接口

### 6.1 接口定义

```python
class CLIInterruptHandler:
    """CLI 模式下的中断处理器。

    替换 LangGraph 的 interrupt()，在终端中实现 HITL 交互。
    """

    def handle(self, payload: InterruptPayload) -> InterruptDecision:
        """处理中断，返回用户决策。

        Args:
            payload: 中断信息 (Phase 名称、生成的文件、摘要等)

        Returns:
            InterruptDecision: continue / edit / regenerate / skip
        """
        ...

    def validate(self, file_path: Path, phase: str) -> ValidationResult:
        """验证修改后的文件是否合法。

        Args:
            file_path: 文件路径
            phase: 当前 Phase 名称

        Returns:
            ValidationResult: ok / errors
        """
        ...

    def open_editor(self, file_path: Path) -> None:
        """打开编辑器查看/修改文件。"""
        ...
```

### 6.2 数据结构

```python
@dataclass
class InterruptPayload:
    """中断信息。"""
    phase: str                    # Phase 名称
    phase_index: int              # Phase 序号 (1-9)
    total_phases: int             # 总 Phase 数 (9)
    module: str                   # 模块名
    files: list[GeneratedFile]    # 生成的文件列表
    summary: dict                 # 摘要信息
    execution_result: dict = None # 执行结果 (Phase 5 专用)


@dataclass
class GeneratedFile:
    """生成的文件信息。"""
    path: Path                    # 文件路径
    file_type: str                # 文件类型 (md/py/json)
    stats: dict = None            # 统计信息 (用例数、场景数等)


@dataclass
class InterruptDecision:
    """用户决策。"""
    action: str                   # continue / edit / regenerate / skip
    feedback: str = None          # 修改意见 (regenerate 时)


@dataclass
class ValidationResult:
    """合法性检查结果。"""
    ok: bool                      # 是否通过
    errors: list[str] = None      # 错误列表
```

### 6.3 与 Engine 的集成

```python
class Engine:
    def __init__(self, interrupt_handler=None):
        self.interrupt_handler = interrupt_handler or CLIInterruptHandler()

    def run(self, project_path, module, pages=None):
        # ... 构建 SOP Graph ...

        # 在每个 Phase 完成后调用 interrupt handler
        # 替换 LangGraph 的 interrupt()
        ...
```

## 7. 与现有 HITL 的关系

### 7.1 当前 HITL (3 个点)

```python
# sop_graph.py 中的 3 个 interrupt()
automation_strategy_approval_node  → interrupt(...)
testcase_approval_node             → interrupt(...)
testcase_quality_gate_node         → interrupt(...)
```

### 7.2 新设计 (9 个点)

新的 CLIInterruptHandler 替换所有 3 个 interrupt()，并在其他 6 个 Phase 也加入暂停。

### 7.3 迁移策略

```
当前:
  sop_graph.py → interrupt() → Web API 处理

新设计:
  sop_graph.py → CLIInterruptHandler.handle() → CLI 交互

迁移步骤:
  1. 创建 CLIInterruptHandler
  2. 在 Engine 中注入 handler
  3. 修改 sop_graph.py，用 handler 替换 interrupt()
  4. 保留 interrupt() 作为 fallback (Web API 模式)
```

## 8. 演示脚本

```bash
# 完整演示 (带交互)
python demo.py --project-path D:\...\ZJSN_Test-master526 --module equipment

# 预期输出:
#   Phase 1: 生成 PROJECT_CONTEXT.md → 暂停 → 用户确认
#   Phase 2: 生成 MODULE_CONTEXT.md → 暂停 → 用户确认
#   Phase 3: 生成 TEST_DESIGN.md + TEST_CASES.md → 暂停 → 用户确认
#   Phase 4: 生成代码 → 暂停 → 用户确认
#   Phase 5: 执行测试 → 暂停 → 用户确认
#   Phase 6: Bug 分析 → 暂停 → 用户确认
#   Phase 7: 扫描脏数据 → 暂停 → 用户确认清理
#   Phase 8: 生成报告 → 暂停 → 用户确认
#   Phase 9: 沉淀知识 → 暂停 → 用户确认
#   ✅ 全部完成!
```
