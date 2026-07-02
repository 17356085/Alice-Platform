## 组件职责表

| 组件名 | 类型 | 职责 | Props (in) | Events (out) | 父组件 |
|--------|------|------|------------|--------------|--------|
| **App** | root | 应用根组件，挂载全局 Provider | - | - | - |
| **Layout** | layout | 页面整体布局框架（Header+Sidebar+内容区） | - | - | App |
| **Header** | shared | 顶部导航栏，含用户信息和登出 | `username:string` | `logout` | Layout |
| **Sidebar** | shared | 侧边导航菜单，按模块/功能分组 | `menuItems:MenuItem[]`, `collapsed:boolean` | `navigate:path` | Layout |
| **RouterView** | layout | 路由占位，渲染匹配的页面组件 | - | - | Layout |
| **DashboardPage** | page | 首页仪表盘：概览统计 + 最近执行记录 | - | - | RouterView |
| **StatCard** | shared | 统计指标卡片 | `label:string`, `value:number`, `trend?:'up'\|'down'`, `icon?:string` | - | DashboardPage |
| **RecentExecutions** | component | 最近测试执行记录列表 | `executions:Execution[]`, `loading:boolean` | `view:executionId`, `rerun:executionId` | DashboardPage |
| **ModuleListPage** | page | 业务模块列表页（equipment/personnel/warehouse/tank） | - | - | RouterView |
| **ModuleTable** | component | 模块数据表格 | `modules:Module[]`, `loading:boolean` | `select:moduleId`, `create`, `delete:moduleId` | ModuleListPage |
| **ModuleRow** | component | 单个模块行 | `module:Module` | `edit`, `delete`, `navigate` | ModuleTable |
| **StatusBadge** | shared | 状态标签（Activated/Draft/Archived等） | `status:string`, `type?:"success"\|"warning"\|"danger"` | - | ModuleTable / SkillCard |
| **SearchBar** | shared | 通用搜索输入框 | `placeholder:string`, `debounce?:number` | `search:query` | ModuleListPage / RAGKnowledgePage |
| **ModuleDetailPage** | page | 模块详情页，含 PageObject 和 TestScript 列表 | - | - | RouterView |
| **PageObjectList** | component | 页面对象文件列表 | `pos:PageObject[]`, `moduleId:string` | `select:poId`, `generate`, `delete:poId` | ModuleDetailPage |
| **PageObjectCard** | component | 单个 PageObject 摘要卡片 | `po:PageObject` | `edit`, `delete`, `preview` | PageObjectList |
| **TestScriptList** | component | 测试脚本文件列表 | `scripts:TestScript[]`, `moduleId:string` | `select:scriptId`, `generate`, `run:scriptId`, `delete:scriptId` | ModuleDetailPage |
| **TestScriptCard** | component | 单个 TestScript 摘要卡片 | `script:TestScript` | `edit`, `run`, `delete`, `preview` | TestScriptList |
| **PageObjectEditorPage** | page | Page Object 编辑/生成页面 | - | - | RouterView |
| **LocatorForm** | component | 元素定位器表单（By策略+选择器） | `locators:Locator[]`, `moduleId:string` | `add`, `remove:index`, `update:Locator` | PageObjectEditorPage |
| **CodePreview** | shared | 代码预览/高亮显示组件 | `code:string`, `language:string`, `readonly:boolean` | - | PageObjectEditorPage / TestScriptEditorPage |
| **TestScriptEditorPage** | page | 测试脚本编辑/生成页面 | - | - | RouterView |
| **TestCaseForm** | component | 测试用例表单 | `testcases:TestCase[]`, `fixtures:Fixture[]` | `add`, `remove:index`, `update:TestCase` | TestScriptEditorPage |
| **FixtureSelector** | component | pytest fixture 选择器 | `availableFixtures:Fixture[]`, `selected:string[]` | `toggle:fixtureName` | TestScriptEditorPage |
| **SopPhasePage** | page | SOP 流程阶段管理页（Phase 0-9） | - | - | RouterView |
| **PhaseTimeline** | component | Phase 时间线可视化 | `phases:Phase[]`, `currentPhase:number` | `select:phaseIndex` | SopPhasePage |
| **PhaseNode** | component | 单个 Phase 节点 | `phase:Phase`, `active:boolean`, `completed:boolean` | `click` | PhaseTimeline |
| **PhaseGatePanel** | component | 门禁检查面板（SOP Gate） | `phase:Phase`, `gates:Gate[]`, `results:GateResult[]` | `check:gateId`, `override:gateId` | SopPhasePage |
| **AgentSkillPage** | page | Agent 与 Skill 绑定管理页 | - | - | RouterView |
| **SkillCard** | component | 单个 Skill 信息卡片 | `skill:Skill` | `view`, `bind:agentId`, `unbind` | AgentSkillPage |
| **SkillVersionBadge** | shared | Skill 版本号标签 | `version:string`, `status:"active"\|"deprecated"` | - | SkillCard |
| **AgentBindingPanel** | component | Agent-Skill 绑定/解绑面板 | `agents:Agent[]`, `skill:Skill`, `bindings:Binding[]` | `bind:bindingInfo`, `unbind:bindingId` | AgentSkillPage |
| **ExecutionPage** | page | 测试执行页面（运行+查看结果） | - | - | RouterView |
| **ExecutionForm** | component | 执行参数表单（选择 Module/TestScript/marker） | `modules:Module[]`, `markers:string[]` | `execute:ExecutionConfig` | ExecutionPage |
| **ExecutionResultPanel** | component | 执行结果展示面板（passed/failed/errors/skipped） | `result:ExecutionResult`, `loading:boolean` | `viewLog:logId`, `export` | ExecutionPage |
| **ResultLog** | component | 单条执行日志行 | `log:LogEntry` | `expand` | ExecutionResultPanel |
| **RAGKnowledgePage** | page | RAG 知识库管理页 | - | - | RouterView |
| **CollectionTabs** | component | 知识库集合标签页（known_issues/ui_patterns等） | `collections:Collection[]`, `active:string` | `switch:collectionName` | RAGKnowledgePage |
| **KnowledgeSearchBar** | component | 知识库搜索（含 collection 过滤） | `collections:string[]`, `placeholder:string` | `search:query, collection:string` | RAGKnowledgePage |
| **KnowledgeEntryList** | component | 知识条目列表 | `entries:KnowledgeEntry[]`, `loading:boolean` | `select:entryId` | RAGKnowledgePage |
| **KnowledgeEntryCard** | component | 单条知识条目卡片 | `entry:KnowledgeEntry` | `view`, `edit`, `delete` | KnowledgeEntryList |

## 路由映射

| Path | Page Component | Auth Required | Lazy Load | 说明 |
|------|---------------|---------------|-----------|------|
| `/` | DashboardPage | Yes | Yes | 首页仪表盘 |
| `/modules` | ModuleListPage | Yes | Yes | 业务模块列表 |
| `/modules/:moduleId` | ModuleDetailPage | Yes | Yes | 模块详情（PO/TestScript列表） |
| `/modules/:moduleId/page-objects/new` | PageObjectEditorPage | Yes | Yes | 新建/编辑 PageObject |
| `/modules/:moduleId/page-objects/:poId` | PageObjectEditorPage | Yes | Yes | 编辑已有 PageObject |
| `/modules/:moduleId/test-scripts/new` | TestScriptEditorPage | Yes | Yes | 新建/编辑 TestScript |
| `/modules/:moduleId/test-scripts/:scriptId` | TestScriptEditorPage | Yes | Yes | 编辑已有 TestScript |
| `/sop-phases` | SopPhasePage | Yes | Yes | SOP Phase 管理 |
| `/agents-skills` | AgentSkillPage | Yes | Yes | Agent-Skill 绑定管理 |
| `/execution` | ExecutionPage | Yes | Yes | 测试执行 & 结果查看 |
| `/knowledge` | RAGKnowledgePage | Yes | Yes | RAG 知识库管理 |
| `/login` | LoginPage (implied) | No | No | 登录页 |

## 数据流向