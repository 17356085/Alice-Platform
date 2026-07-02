# CLI 实施方案

> 审查通过后方可开始编码

## 1. 目标

将 Engine 封装为 CLI 工具，实现:

```bash
# 执行测试
alice run --project-path D:\...\ZJSN_Test-master526 --module equipment

# 检查配置
alice validate --project-path D:\...\ZJSN_Test-master526

# 查看状态
alice status --project-path D:\...\ZJSN_Test-master526 --module equipment

# 继续中断
alice resume --project-path D:\...\ZJSN_Test-master526 --module equipment

# 列出项目
alice list-projects --workspace D:\...\WorkStudy2

# 列出模块
alice list-modules --project-path D:\...\ZJSN_Test-master526
```

## 2. 实施阶段

### Phase 1: 基础框架 (优先级: P0)

| 任务 | 说明 | 依赖 | 风险 |
|------|------|------|------|
| 1.1 安装依赖 | typer, rich | 无 | 低 |
| 1.2 创建 CLI 入口 | `aitest/cli/main.py` | 1.1 | 低 |
| 1.3 实现 `run` 命令 | 调用 Engine.run() | 1.2, Engine | 中 |
| 1.4 实现 `validate` 命令 | 检查 project.yaml | 1.2 | 低 |
| 1.5 基础输出 | rich 彩色文本 | 1.1 | 低 |

**交付物**: 可以执行 `alice run --project-path ... --module equipment`

### Phase 2: 事件总线 (优先级: P0)

| 任务 | 说明 | 依赖 | 风险 |
|------|------|------|------|
| 2.1 实现 EventBus | 发布/订阅模式 | 无 | 中 |
| 2.2 Engine 集成 EventBus | Phase 完成时发事件 | 2.1, Engine | 中 |
| 2.3 CLI 订阅事件 | 接收事件并展示 | 2.1, 2.2 | 低 |

### 事件类型

| 事件 | 触发时机 | 数据 |
|------|----------|------|
| `phase_start` | Phase 开始 | phase, index, total |
| `phase_complete` | Phase 完成 | phase, files, summary, elapsed |
| `phase_skip` | Phase 跳过 | phase, reason |
| `interrupt` | HITL 中断 | phase, type, files, options |
| `test_result` | 测试执行完成 | passed, failed, errors, skipped |
| `gate_result` | 门禁判定 | pass_rate, status |
| `error` | 错误 | error_type, message |
| `complete` | 全部完成 | status, elapsed, report_path |

## 2. 任务分解

### Phase A: 基础框架 (优先级: P0)

| # | 任务 | 描述 | 依赖 | 风险 |
|---|------|------|------|------|
| A1 | 安装依赖 | 添加 typer, rich 到 requirements | 无 | 低 |
| A2 | CLI 入口 | 创建 `cli/main.py`，注册命令 | A1 | 低 |
| A3 | `run` 命令 | 基本执行流程，无中断处理 | A2 | 中 |
| A4 | 输出美化 | 用 rich 格式化终端输出 | A2 | 低 |

### Phase B: 事件总线 (优先级: P0)

| # | 任务 | 描述 | 依赖 | 风险 |
|---|------|------|------|------|
| B1 | EventBus 实现 | 发布/订阅/等待机制 | 无 | 中 |
| B2 | Engine 集成 | Engine 内部发事件 | B1 | 中 |
| B3 | CLI 订阅 | CLIEventHandler 处理事件 | B1, B2 | 低 |

### Phase C: Interrupt Handler (优先级: P0)

| # | 任务 | 描述 | 依赖 | 风险 |
|---|------|------|------|------|
| C1 | CLIInterruptHandler | 终端交互: v/e/r/s 操作 | B1 | 中 |
| C2 | 合法性检查 | 文件验证逻辑 | C1 | 中 |
| C3 | 编辑器集成 | 打开 notepad/vim | C1 | 低 |

### Phase D: 辅助命令 (优先级: P1)

| # | 任务 | 描述 | 依赖 | 风险 |
|---|------|------|------|------|
| D1 | `validate` 命令 | 检查 project.yaml + 目录结构 | A2 | 低 |
| D2 | `status` 命令 | 查看 SOP_STATUS_*.json | A2 | 低 |
| D3 | `resume` 命令 | mode="resume" 执行 | A3 | 中 |
| D4 | `list-projects` 命令 | 扫描 workspace | A2 | 低 |
| D5 | `list-modules` 命令 | 扫描 .tlo/knowledge/modules/ | A2 | 低 |

### Phase E: Phase 0 交互 (优先级: P1)

| # | 任务 | 描述 | 依赖 | 风险 |
|---|------|------|------|------|
| E1 | Phase 0 交互流程 | 收集项目配置 | A2, C1 | 中 |
| E2 | 技术栈分类输入 | 前端/后端/移动端选择 | E1 | 低 |
| E3 | 账号输入 | 多账号输入+验证 | E1 | 低 |
| E4 | API 文档导入 | Swagger/Postman/文件导入 | E1 | 中 |
| E5 | 输入验证 | URL 可访问性、格式检查 | E1 | 中 |
| E6 | 配置生成 | 生成 project.yaml + test_accounts.yaml | E1 | 低 |

### Phase F: Extension 集成 (优先级: P2)

| # | 任务 | 描述 | 依赖 | 风险 |
|---|------|------|------|------|
| F1 | `--extensions` 参数 | CLI 支持加载 Extension | A3 | 低 |
| F2 | Extension 注册 | 动态加载 Extension 类 | F1 | 低 |

## 3. 文件结构

```
aitest/
├── cli/
│   ├── __init__.py
│   ├── main.py              ← Typer 入口 + 命令注册
│   ├── commands/
│   │   ├── __init__.py
│   │   ├── run.py           ← run 命令
│   │   ├── validate.py      ← validate 命令
│   │   ├── status.py        ← status 命令
│   │   ├── resume.py        ← resume 命令
│   │   ├── list_projects.py ← list-projects 命令
│   │   └── list_modules.py  ← list-modules 命令
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── interrupt.py     ← CLIInterruptHandler
│   │   ├── event_handler.py ← CLIEventHandler (订阅事件)
│   │   └── validator.py     ← 合法性检查
│   └── output/
│       ├── __init__.py
│       ├── formatter.py     ← rich 格式化
│       └── progress.py      ← 进度条
├── engine/
│   ├── __init__.py          ← Engine 类 (需更新: 加入事件总线)
│   ├── event_bus.py         ← EventBus 实现 (新建)
│   └── ... (现有文件)
└── demo.py                  ← 快速演示入口 (调用 CLI)
```

## 4. 依赖

```
# 新增依赖
typer>=0.9.0
rich>=13.0.0

# 现有依赖 (不需要新增)
langgraph>=0.2.0
langchain-core>=0.3.0
anthropic>=0.40.0
pyyaml>=6.0
python-dotenv>=1.0.0
```

## 5. 风险评估

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| Engine.run() 阻塞导致 CLI 无响应 | 高 | 中 | 用 Progress 显示进度，支持 Ctrl+C 中断 |
| 事件总线和 LangGraph interrupt 冲突 | 高 | 中 | EventBus 作为 interrupt 的 wrapper，不替换底层 |
| 编辑器打开后 CLI 挂起 | 中 | 低 | 用 subprocess 打开编辑器，等待关闭 |
| rich 在 Windows 终端兼容性 | 中 | 低 | 测试 Windows Terminal + PowerShell + CMD |
| Phase 0 交互流程复杂 | 中 | 中 | 先做最简版，后续迭代 |
| 现有 Engine 代码改动影响稳定性 | 高 | 低 | 最小改动原则，不重构现有逻辑 |

## 6. 里程碑

| 里程碑 | 内容 | 验收标准 | 预计耗时 |
|--------|------|----------|----------|
| **M1: CLI 能跑** | A1-A4 | `alice run --module equipment --mock-llm` 能执行 | 2h |
| **M2: 事件驱动** | B1-B3 | CLI 能收到 Phase 事件并展示 | 2h |
| **M3: HITL 交互** | C1-C3 | 每个 Phase 暂停，用户可 v/e/r/s | 3h |
| **M4: 辅助命令** | D1-D5 | validate/status/resume/list 都能用 | 2h |
| **M5: Phase 0** | E1-E6 | 新项目交互式配置 | 3h |
| **M6: Extension** | F1-F2 | --extensions 参数可用 | 1h |

**总计: ~13h**

## 7. 实施顺序

```
M1 (CLI 能跑)
  │
  ├── M2 (事件驱动)
  │     │
  │     └── M3 (HITL 交互)
  │
  ├── M4 (辅助命令)
  │
  └── M5 (Phase 0)
        │
        └── M6 (Extension)
```

**M1 → M2 → M3** 是关键路径 (串行)。
**M4 和 M5** 可以和 M2/M3 并行。
**M6** 最后做。

## 8. 验收场景

### 场景 1: Mock LLM 快速验证

```bash
alice run --project-path D:\...\ZJSN_Test-master526 --module equipment --mock-llm

# 预期: 走完 9 个 Phase，每个 Phase 暂停，用户可交互
```

### 场景 2: 真实 LLM 执行

```bash
alice run --project-path D:\...\ZJSN_Test-master526 --module equipment --pages alarm-config

# 预期: 调用真实 LLM，生成文档，执行测试
```

### 场景 3: Phase 0 新项目

```bash
alice run --project-path D:\...\NewProject

# 预期: 检测到无 project.yaml，进入 Phase 0 交互式配置
```

### 场景 4: 继续中断

```bash
alice resume --project-path D:\...\ZJSN_Test-master526 --module equipment

# 预期: 从上次中断的 Phase 继续
```

### 场景 5: 检查配置

```bash
alice validate --project-path D:\...\ZJSN_Test-master526

# 预期: 检查 project.yaml、目录结构、账号配置，输出报告
```

## 9. 不做的事

| 不做 | 原因 |
|------|------|
| 重构 Engine 内部代码 | 最小改动原则 |
| 添加新 Phase | 当前 9 个 Phase 够用 |
| 多语言 SDK | 现在不需要 |
| Web API | 另一个会话做 |
| 数据库支持 | 文件系统够用 |
| 并发执行 | 单次执行设计 |

## 10. 审查清单

- [ ] 任务分解是否完整?
- [ ] 优先级是否合理?
- [ ] 风险是否识别充分?
- [ ] 文件结构是否清晰?
- [ ] 依赖是否最小化?
- [ ] 里程碑是否可验收?
- [ ] 实施顺序是否合理?
- [ ] 验收场景是否覆盖?
- [ ] "不做的事"是否正确?
