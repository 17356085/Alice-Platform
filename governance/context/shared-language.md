# Shared Language — AITest Platform 领域术语表

> 灵感来源: [mattpocock/skills — CONTEXT.md](https://github.com/mattpocock/skills)
> 目标: Agent 与开发者使用同一套词汇，减少解释性啰嗦。每个术语一项精确定义，标注避免用语。

## 平台术语（AITest Platform）

**Agent**:
AI 驱动的自动化角色，执行 SOP 图中的特定 Phase。有明确的 Primary/Secondary Owner 关系绑定到 Skill。
_避免_: 机器人、AI、助手（Agent 是特定治理概念的专有名词）

**Skill**:
单个可复用的提示/能力单元，由 `.md` 文件定义，注册在 `skill-registry.yaml`。每个 Skill 有版本号、分类、依赖声明。
_避免_: prompt、命令、脚本（Skill 是治理层的一等公民）

**Phase**:
SOP 流程中的标准化步骤（Phase 0-9），由 `CANONICAL_PHASES` 定义。每个 Phase 产出特定文档类型。
_避免_: 步骤、阶段（Phase 是带编号的治理节点，不可跳过）

**Module**:
被测系统中按业务领域划分的组织单元（如 equipment、personnel、warehouse、tank）。每个 Module 对应一组 pages 和测试脚本。
_避免_: 模块直接用中文"模块"可能引起歧义（是代码模块还是业务模块）。英文 Module 专指业务模块。

**Page Object (PO)**:
继承 `BasePage` 的类，封装单个页面的元素定位器和操作方法。定位器声明为类属性元组，操作方法返回 `self` 支持链式调用。
_避免_: 页面类、页面模型（PO 在代码规范中有确切签名要求）

**Locator**:
Selenium `By` 策略 + 选择器字符串的元组，如 `(By.CSS_SELECTOR, ".el-table")`。选择优先级：CSS > 相对 XPath > 绝对 XPath（禁止）。
_避免_: 定位器、selector（Locator 特指 `(By.*, str)` 元组格式）

**Fixture**:
pytest fixture，通过 `conftest.py` 注入到测试用例。负责 driver/PageObject 初始化、登录状态、数据清理（yield 后 teardown）。
_避免_: 夹具、前置条件（Fixture 是 pytest 框架术语，有 yield teardown 语义）

**SOP Gate (门禁)**:
`check_sop_gate.py` 执行的前置检查，验证模块在进入下一 Phase 前文档/代码完整性满足最低标准。
_避免_: 检查点、关卡（Gate 是不可绕过的硬性约束）

**Cleanup Tracker**:
CRUD 测试中注册清理任务的机制。`get_cleanup_tracker().register(entity_type=..., entity_id=..., api_delete_url=...)` 在 teardown 阶段批量清理。
_避免_: 清理器、回收机制

**RAG**:
ChromaDB 向量检索系统，5 集合 235 文档。bug-analysis Skill 的 L0 步骤强制调用 `rag_search_known_issues` 匹配已知坑位。
_避免_: 向量搜索、语义检索（RAG 在本项目中是具体实现，不是泛指）

**Event Bus**:
文件持久化事件系统（`aitest/event_bus.py`），发出 AgentCompleted/BugClosed/CycleEnd/ContextUpdated 事件供 Knowledge Agent 消费。
_避免_: 消息队列、通知系统

---

## 测试自动化术语

**Smoke Test (冒烟)**:
验证页面基本可用的最小测试集，标记 `@pytest.mark.smoke`。每个模块必须有冒烟用例。
_避免_: 冒烟不做为"简单测试"的同义词

**CRUD Test**:
创建-读取-更新-删除完整流程测试。必须注册 Cleanup Tracker。
_避免_: 增删改查（用 CRUD 缩写更精确，且与编码规范中的 9 条红线对齐）

**Rerun (重跑)**:
pytest-rerunfailures 插件的自动重试机制。flaky 测试通过 `--reruns N` 自动重试。重跑成功的用例标记为 RERUN。
_避免_: 重试、再跑（Rerun 指 pytest 插件的特定行为）

**Allure**:
测试报告框架。`--alluredir=allure-results` 产出 JSON 结果，经 `allure generate` 生成 HTML 报告。
_避免_: 报告（Allure 是具体工具名）

**KPI Reports**:
SOP Phase 9 产出的综合测试报告，Excel 格式。写入 `governance/kpi/reports/{模块}/测试报告-{模块}.xlsx`，覆盖式（重跑 SOP 直接覆写，无日期后缀）。`governance/kpi/README.md` 定义完整目录标准。
_避免_: `reports/`、`ZJSN_Test-master526/reports/`（旧路径，已废弃）

---

## 被测系统业务术语（鞍集涂源管理系统）

**设备管理 (equipment)**:
包含报警配置、单位管理、维保管理、摄像头管理、关键参数管理的 Module。使用 Element Plus UI。
_Agent 注意_: 与"设备台账"是不同概念。

**储罐管理 (tank)**:
储罐监控与报警报告的 Module。**使用自定义 UI 框架**，BasePage 通用定位器不可用。
_Agent 注意_: 生成此模块的 Page Object 前必须读取 `project-profile.md` § UI 框架差异。

**承包商管理 (contractor)**:
入场审批、人员管理、单位管理、入场记录的 Module。路由使用 `nest-menu` 导航模式，不可跳治理层。
_Agent 注意_: 导航路径经过多层嵌套菜单，不可直接用 URL 跳转。

**仓库管理 (warehouse)**:
备件/试剂/危废品的入库、出库、库存、盘点、领用 Module。包含 12+ 页面，测试量最大。
_Agent 注意_: warehousing（仓库）在本系统中包含备件(spare)、试剂(reagent)、危废品(hazard) 三个子领域。

**生产管理 (production)**:
排班配置、业务类型配置、日报、月报。与 tanks 模块有数据关联。
_Agent 注意_: 日报和月报页面涉及跨模块数据聚合。

**工作流 (workflow)**:
审批链、审批历史、待办审批、我的申请、SAP 推送日志的 Module。跨模块审批引擎，5 页面 38 测试用例。
_Agent 注意_: 审批链涉及多角色流转，测试需准备不同权限账号。

**DCS 数据监控 (dcs)**:
关键参数监控、全部/常用点位查看、点位配置、上传日志的 Module。工业数据监控场景，5 页面。
_Agent 注意_: 当前 Phase 1-2.5 缺失 (PAGE_CONTEXT/RISK_MODEL/TEST_DESIGN/TEST_CASES)，仅 TECH_ANALYSIS + AUTO_STRATEGY 骨架存在。

**系统角色 (system-role)**:
RBAC 角色管理的 Module。角色 CRUD + 权限矩阵配置，1 页面。
_Agent 注意_: 角色删除需验证关联用户提示，权限变更需验证菜单动态渲染。

---

## Element Plus 专用术语

**Teleport**:
Vue 3 Teleport 特性导致弹窗/下拉选项渲染到 `<body>` 末尾，脱离组件 DOM 树。EP-001 已知坑位。
_避免_: 弹出层、传送门（用英文 Teleport 指向具体的 Vue 3 API）

**el-cascader**:
Element Plus 级联选择器。选项通过 Teleport 渲染，定位需 `el-cascader` 相关 class。
_Agent 注意_: 此为 Element Plus 中最常出问题的组件之一。

**loading 遮罩**:
`el-loading-mask` 全局覆盖层，阻止元素交互。EP-003 已知坑位。需用 `wait_vue_stable()` 等待消失。
_避免_: 加载中、loading（遮罩特指阻止交互的覆盖层，不是所有 loading 状态）

**dialog**:
`el-dialog` 弹窗组件。EP-011 记录 2.x 结构变化。`BasePage.dialog` 方法提供通用弹窗操作。
_Agent 注意_: 区分 el-dialog（弹窗组件）和 el-drawer（抽屉组件），两者定位策略不同。

**fixed-right 列**:
el-table 固定右侧列时 Element Plus 会克隆一份 DOM 节点（`el-table__fixed-right`），EP-006 已知坑位。
_Agent 注意_: 定位 fixed 列内元素时必须用 `el-table__fixed-right` 前缀，避免匹配到原列。

---

## 关系图

```
Agent ──owns──▶ Skill ──produces──▶ Phase 文档
  │                                     │
  └──consumes──▶ Event Bus ──triggers──▶ Knowledge Agent
                     │
                     └──writes──▶ artifacts/ + kpi/reports/ + kpi/timeseries/
                                    │
Module ──contains──▶ Page ──has──▶ Page Object (.py)
  │                    │
  │                    └──has──▶ PAGE_CONTEXT.md
  │
  └──has──▶ conftest.py ──provides──▶ Fixtures
                │
                └──registers──▶ Cleanup Tracker

Bug ──matched via──▶ RAG (known_issues) ──returns──▶ EP-001~EP-011
```

## 歧义消除

| 曾用词 | 问题 | 统一为 |
|--------|------|--------|
| "提示词" / "prompt" | 歧义：是 Skill 定义还是 LLM 输入 | **Skill**（指治理层能力单元），**Prompt 模板**（指 Skill 内的 LLM 输入文本） |
| "上下文" / "context" | 歧义：项目文档 vs AI 会话上下文 | **PROJECT_CONTEXT**（治理文档），**会话上下文**（AI 对话窗口内容） |
| "定位器" / "selector" | 歧义：By 策略+字符串 vs CSS Selector | **Locator**（特指 `(By.*, str)` 元组），**CSS Selector**（字符串） |
| "弹窗" | 歧义：el-dialog / el-drawer / 浏览器 alert | 用具体组件名：**el-dialog** / **el-drawer** / **浏览器弹窗** |
| "表格" | 歧义：el-table / 原生 table / 数据列表 | 用具体组件名：**el-table** / **data-table** |
| "清理" | 歧义：测试数据清理 vs 代码清理 vs 进程清理 | **Cleanup Tracker**（测试数据），**teardown**（fixture 清理），**kill**（进程终止） |
| "模块" | 歧义：业务模块 vs 代码模块 | **Module**（业务模块，如 equipment），**代码模块**（Python module） |
| "页面" | 歧义：业务页面 vs HTML 页面 | **Page**（业务页面，如 alarm-config），**网页/HTML**（浏览器端） |
<!-- ⚠️ AUTO-GENERATED SECTION BEGIN: module-list -->
<!-- Source: tools/sync_progress.py -->
## 模块清单 (自动生成 — 更新于 2026-06-17 16:53)

- **system-user** (系统-用户): 5 pages, 16 tests, SOP: completed
- **system-role** (角色管理): 1 pages, 6 tests, SOP: completed
- **system-management** (系统管理(重置)): 8 pages, 1 tests, SOP: pending
- **equipment** (设备管理): 4 pages, 8 tests, SOP: completed
- **tank** (储罐管理): 3 pages, 6 tests, SOP: completed
- **personnel** (人员管理): 16 pages, 18 tests, SOP: completed
- **sales** (销售管理): 4 pages, 20 tests, SOP: completed
- **lab** (化验室取样): 6 pages, 9 tests, SOP: completed
- **production** (生产管理): 4 pages, 5 tests, SOP: completed
- **dcs** (DCS数据管理): 5 pages, 5 tests, SOP: partial
- **warehouse** (库管管理): 17 pages, 16 tests, SOP: completed
- **workflow** (工作流管理): 5 pages, 6 tests, SOP: completed

> 共 12 模块。此段由 sync_progress.py 自动更新。
<!-- ⚠️ AUTO-GENERATED SECTION END: module-list -->