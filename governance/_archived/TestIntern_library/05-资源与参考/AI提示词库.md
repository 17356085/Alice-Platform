# ⚠️ DEPRECATED — AI 提示词库（已冻结）

> **本文件已于 2026-06-11 冻结，仅作历史参考。**
>
> **新 Prompt 请使用 `governance/skills/` 目录下的 Skill 文件。**
>
> **映射关系参见 `governance/skills/prompt-library-index.md`。**
>
> 所有 SOP Phase 的提示词已逐条迁移到治理层 Skill 体系：
> - Phase 0-0.8: `project-context-manager` / `module-modeling` / `requirement-analysis`
> - Phase 1-1.5: `page-analysis` / `risk-modeling`
> - Phase 2-2.5: `testcase-design`
> - Phase 3-3.5: `tech-analysis` / `auto-strategy`
> - Phase 4: `page-object-generator` / `test-script-generator` / `conftest-generator`
> - Phase 4.5-5: `bug-analysis`
> - Phase 6-7: `api-testing` / `ci-pipeline-analysis`
> - Phase 8-9: `test-summary` / `knowledge-precipitation`
> - 跨场景: `context-sync` / `element-plus-locator` / `test-data-generation` / `miniapp-testing`
>
> **请勿在本文件中新增或修改任何提示词。**
>
> ---
>
> 以下为原内容（仅供参考）：

# AI 提示词库（历史版本）

> ~~面向鞍集涂源管理系统测试开发的完整提示词集合，严格对齐 SOP 工作流。~~
> ~~每个提示词可直接复制到 Claude Code / AI 对话中使用，替换 `{{ }}` 占位符即可。~~

---

## 使用说明

- **新模块开发**：从 Phase 0.5 开始，按顺序执行
- **已有模块补充**：从 Phase 1 开始
- **Bug 分析**：直接用 Phase 4.5
- **自动化失败**：直接用 Phase 5

每个提示词区分为：
- 📥 **前置输入**：使用前需要准备的材料
- 💬 **提示词**：可直接复制到 AI 对话
- 📤 **预期产出**：AI 应该输出的文档/代码

---

# 一、SOP 工作流提示词（按 Phase 编排）

---

## Phase 0 — 项目初始化

### P0-01 建立项目全局上下文

📥 **前置输入**：项目URL、测试账号、技术栈说明

💬 **提示词**：

```text
你是一个高级软件测试架构师。你需要为一个新项目建立完整的项目级测试上下文文档。

## 项目信息
- 项目名称：{{鞍集涂源管理系统}}
- Web端地址：{{http://8.136.215.171:8081/}}
- 前端技术栈：{{Vue 3 + Element Plus}}
- 测试账号：{{admin / 密码}}
- 平台类型：Web管理端 + 微信小程序端

## 任务
请输出 PROJECT_CONTEXT.md，包含以下章节：

1. **项目概述**：系统定位、业务领域、用户群体
2. **技术架构**：前端/后端/数据库/部署方式
3. **用户角色与权限模型**：列出所有角色及其权限边界
4. **功能模块树**：一级菜单→二级菜单→页面，完整层级
5. **核心业务流程**：最重要的3-5条业务链路（如：用户创建→角色分配→权限生效）
6. **测试风险矩阵**：按模块评估测试风险（高/中/低），说明原因
7. **自动化优先级建议**：P0（必须自动化）/ P1（建议）/ P2（手工即可）
8. **已完成的测试工作**：列出已覆盖的模块及用例数
9. **踩坑经验**：已知的技术难点和解决方案

## 约束
- 使用中文
- 表格优于纯文字列表
- 模块树要完整，不要遗漏
- 每个风险项给出缓解措施
```

📤 **预期产出**：`PROJECT_KNOWLEDGE.md`

---

## Phase 0.5 — 模块建模

### P0.5-01 建立模块级上下文

📥 **前置输入**：PROJECT_KNOWLEDGE.md、模块入口URL

💬 **提示词**：

```text
你是一个熟悉 {{鞍集涂源管理系统}} 的测试工程师。请为以下模块建立 {MODULE_NAME}_CONTEXT.md。

## 模块信息
- 模块名称：{{设备管理}}
- 模块入口URL：{{https://aiwechatminidemo.cimc-digital.com/#/{页面名}}}
- 所属一级菜单：{{设备管理}}
- 参考项目知识库：{{粘贴 PROJECT_KNOWLEDGE.md 中该模块相关内容}}

## 任务
输出 MODULE_CONTEXT.md，包含：

1. **模块概述**：模块名称、路径、权限要求
2. **子页面清单**：列出所有子页面（页面名称、路由、状态）
3. **页面关系图**：页面之间的导航/依赖关系（用文字或ASCII图）
4. **核心业务流程**：该模块最重要的2-3条操作链路
5. **数据对象**：该模块涉及的主要数据实体（如：设备、装置、报警规则）
6. **权限矩阵**：不同角色对该模块各页面的访问/操作权限
7. **模块级风险点**：列出风险ID、描述、影响范围、优先级（P0/P1/P2）
8. **自动化价值评估**：该模块自动化的ROI分析

## 格式要求
- 表格优先，层级清晰
- 每个风险给出缓解措施
- 页面状态用 ✅（已完成）/🔄（进行中）/⏳（待开始）
```

📤 **预期产出**：`contexts/{模块}/{MODULE_NAME}_CONTEXT.md`

### P0.5-02 批量模块建模

📥 **前置输入**：PROJECT_KNOWLEDGE.md、模块清单

💬 **提示词**：

```text
基于以下 PROJECT_KNOWLEDGE.md 中的模块树，请分别为每个未建立上下文的模块生成 MODULE_CONTEXT.md 框架。

## 已完成模块
{{粘贴 测试进度追踪.md 中已完成模块列表}}

## 待建模模块
{{粘贴 待建模模块列表，如：储罐管理、DCS数据、化验室取样、人员管理、生产管理、销仓管理}}

## 任务
对每个待建模模块，输出：
1. MODULE_CONTEXT.md 骨架（标注 ⏳ 待填充的章节）
2. 子页面清单（基于 PROJECT_KNOWLEDGE 中的菜单结构推断）
3. 预估测试工作量（人天）

## 注意
- 一次只处理一个模块，处理完等我确认再继续下一个
- 不确定的页面/功能标注"待确认"
```

📤 **预期产出**：各模块 MODULE_CONTEXT.md 骨架

---

## Phase 0.8 — 需求分析

### P0.8-01 需求分析与测试计划

📥 **前置输入**：PRD/原型图/产品说明

💬 **提示词**：

```text
你是一个测试分析师。请对以下需求进行测试视角的分析。

## 需求材料
{{粘贴 PRD 内容或原型图描述}}

## 项目背景
- 项目：{{鞍集涂源管理系统}}
- 模块：{{人员管理-培训管理}}
- 平台：{{Web管理端 / 微信小程序端}}

## 任务
输出需求分析文档，包含：

1. **需求理解**：用一句话概括需求目标
2. **业务规则提取**：列出所有显式和隐式的业务规则
3. **测试范围界定**
   - ✅ 纳入测试：{{明确要测的功能}}
   - ❌ 不纳入测试：{{明确不测的功能及原因}}
4. **风险识别**：
   - 需求模糊点
   - 逻辑矛盾/遗漏
   - 与技术架构的冲突
5. **测试策略建议**：手工/自动化/混合？原因？
6. **测试计划**：分几个迭代？每个迭代测什么？
7. **自动化机会**：哪些功能点适合自动化？优先级？
```

📤 **预期产出**：`contexts/{模块}/REQUIREMENT_ANALYSIS.md`

---

## Phase 1 — 页面分析

### P1-01 基于截图分析页面

📥 **前置输入**：页面截图（1-3张）、MODULE_CONTEXT.md

💬 **提示词**：

```text
你是一个Web端测试工程师，擅长通过截图分析页面结构。请分析以下页面截图。

## 页面信息
- 页面名称：{{设备报警配置}}
- 所属模块：{{设备管理}}
- 页面URL：{{http://8.136.215.171:8081/equipment/alarm-config}}

## 截图
{{上传截图}}

## 任务
请逐区域分析页面，输出 PAGE_CONTEXT.md：

1. **页面整体结构**：顶部/左侧/主内容区的布局描述
2. **搜索/筛选区**：
   - 每个输入控件的类型（input/select/date-picker）
   - 每个控件的标签文字
   - 按钮（搜索/重置/新增等）
3. **表格/列表区**：
   - 所有列标题
   - 每列的数据类型（文本/数字/日期/标签/操作按钮）
   - 操作列中的按钮（编辑/删除/详情等）
4. **分页区**：分页组件位置、每页条数选项
5. **弹窗/对话框**：
   - 弹窗标题
   - 弹窗内表单字段（标签+控件类型）
   - 弹窗按钮（确认/取消）
6. **页面状态**：加载中、空数据、错误状态的表现
7. **权限点**：哪些元素可能受权限控制

## 输出格式
使用表格呈现元素清单：
| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
```

📤 **预期产出**：`contexts/{模块}/pages/{页面}/PAGE_CONTEXT.md`

### P1-02 基于HTML源码分析页面元素定位

📥 **前置输入**：页面HTML源码（浏览器F12复制）、PAGE_CONTEXT.md

💬 **提示词**：

```text
你是一个Selenium自动化测试专家，擅长从HTML源码中提取稳定的元素定位器。
被测系统是 Vue 3 + Element Plus。

## HTML源码
```html
{{粘贴页面关键区域的HTML源码}}
```

## 已识别的页面元素（来自 PAGE_CONTEXT.md）
{{粘贴 PAGE_CONTEXT.md 中的元素清单}}

## 任务
为每个元素设计定位器，按优先级输出：

1. **A级定位器**（优先使用）：
   - `data-testid` 属性
   - 稳定的 `id` 属性
   - 唯一的 `name` 属性
   - 唯一的 `placeholder` 文本

2. **B级定位器**（A级不可用时使用）：
   - 稳定的 CSS Selector（基于类名组合）
   - 注意：Element Plus 的 class 名称可能随版本变化

3. **C级定位器**（保底方案）：
   - XPath（相对路径，避免绝对路径）
   - 使用 `contains()` 处理动态class
   - 使用 `text()` 匹配按钮文字

## 特别注意
- Element Plus 组件的动态 class（如 el-xxx--active）
- Vue 的 v-if 导致元素可能不在 DOM 中
- 表格行的动态索引问题
- 下拉框选项的动态渲染

## 输出格式
| 元素ID | 定位策略 | 定位值 | 稳定性评级 | 备用方案 |
```

📤 **预期产出**：`PAGE_ELEMENT_POSITION.md`（合并到 TECH_ANALYSIS.md 中）

---

## Phase 1.5 — 风险建模

### P1.5-01 页面级风险建模

📥 **前置输入**：PAGE_CONTEXT.md、MODULE_CONTEXT.md

💬 **提示词**：

```text
基于以下页面上下文，进行全面的风险建模。

## 页面信息
- 页面：{{用户列表页}}
- 模块：{{系统管理-用户管理}}
- PAGE_CONTEXT：{{粘贴 PAGE_CONTEXT.md 核心内容}}

## 任务
从以下维度识别风险，输出 RISK_MODEL.md：

1. **业务风险**：
   - 误操作导致的数据丢失（如：误删用户）
   - 权限越权（如：普通用户看到管理功能）
   - 业务规则冲突

2. **权限风险**：
   - 不同角色看到不该看的数据
   - 无权限用户通过URL直接访问
   - 接口未校验权限

3. **数据风险**：
   - 数据边界（空值、超长、特殊字符、SQL注入）
   - 数据一致性（删除关联数据时的级联处理）
   - 并发操作（两人同时编辑同一记录）

4. **接口风险**：
   - 接口超时/失败时的前端表现
   - 接口返回异常数据格式
   - Token过期处理

5. **UI/UX风险**：
   - 不同分辨率下的布局问题
   - 加载状态的用户体验
   - 错误提示是否友好

6. **性能风险**：
   - 大数据量下的表格渲染
   - 频繁搜索时的请求频率

## 输出要求
- 每个风险标注等级（P0/P1/P2）
- P0 = 阻塞上线，P1 = 影响核心体验，P2 = 边缘场景
- 每个P0风险必须给出缓解措施
```

📤 **预期产出**：`contexts/{模块}/pages/{页面}/RISK_MODEL.md`

---

## Phase 2 — 测试设计

### P2-01 页面级测试设计

📥 **前置输入**：PAGE_CONTEXT.md、RISK_MODEL.md

💬 **提示词**：

```text
基于以下页面上下文和风险模型，设计完整的测试方案。

## 输入
- PAGE_CONTEXT：{{粘贴核心内容}}
- RISK_MODEL：{{粘贴核心内容}}

## 任务
输出 TEST_DESIGN.md，按以下维度设计测试：

### 1. 页面加载与显示
- 正常加载、空数据状态、权限受限状态
- 各区域元素完整性校验

### 2. 搜索与筛选
- 单条件搜索、组合搜索、模糊搜索
- 重置筛选、切换筛选条件
- 特殊字符/超长文本搜索

### 3. 表格操作
- 排序、列宽调整、数据格式化
- 行选中、批量操作
- 分页：首页/末页/跳转/改变每页条数

### 4. 新增操作
- 打开弹窗、表单校验（必填项/格式/边界值）
- 提交成功/失败、取消操作
- 重复提交、网络异常时的处理

### 5. 编辑操作
- 数据回显完整性
- 修改后保存、取消修改
- 并发编辑冲突

### 6. 删除操作
- 单个删除、批量删除
- 删除确认弹窗、取消删除
- 删除关联数据时的处理

### 7. 权限测试
- 不同角色看到的功能差异
- 无权限操作的拦截

### 8. 异常场景
- 网络断开、接口超时、500错误
- Token过期、会话超时

## 输出格式
每个测试点格式：
| 编号 | 测试场景 | 优先级 | 前置条件 | 测试步骤 | 预期结果 |
```

📤 **预期产出**：`contexts/{模块}/pages/{页面}/TEST_DESIGN.md`

---

## Phase 2.5 — 测试执行表

### P2.5-01 生成详细测试用例表

📥 **前置输入**：TEST_DESIGN.md

💬 **提示词**：

```text
基于以下测试设计方案，生成可执行的详细测试用例表。

## 输入
TEST_DESIGN：{{粘贴 TEST_DESIGN.md}}

## 任务
将每个测试场景展开为可执行用例，输出 TEST_CASES.md：

| 字段 | 说明 |
|------|------|
| 用例编号 | TC-{模块缩写}-{序号}，如 TC-USER-001 |
| 用例标题 | 简洁描述测试目标 |
| 所属模块 | {{模块名}} |
| 所属页面 | {{页面名}} |
| 优先级 | P0/P1/P2 |
| 前置条件 | 数据准备、账号、环境要求 |
| 测试步骤 | 编号的详细操作步骤（可被另一个人复现） |
| 测试数据 | 具体的输入值（不要写"输入用户名"，写"输入 admin"） |
| 预期结果 | 精确的预期行为描述 |
| 实际结果 | （留空，执行时填写） |
| 自动化 | ✅ 已自动化 / 🔄 待开发 / ❌ 不适合 |

## 格式要求
- 与已有用例格式完全一致（参考 {{testcases/合同管理--测试用例表.md}}）
- 用例编号连续
- 覆盖 P0 100%，P1 ≥80%，P2 ≥50%
```

📤 **预期产出**：`contexts/{模块}/pages/{页面}/TEST_CASES.md`

---

## Phase 3 — 技术实现分析

### P3-01 Element Plus 组件识别与定位器设计

📥 **前置输入**：HTML源码、页面截图

💬 **提示词**：

```text
你是Vue3 + Element Plus自动化测试专家。请分析以下页面HTML，输出技术实现分析。

## HTML源码
```html
{{粘贴页面HTML}}
```

## 已知框架
- 前端：Vue 3 + Element Plus
- 测试框架：Selenium 4.15.2 + pytest 7.4.4
- BasePage 已封装：wait_table_loaded / wait_dialog_visible / wait_loading_disappear

## 任务
输出 TECH_ANALYSIS.md（同时也是 PAGE_ELEMENT_POSITION）：

### 1. Element Plus 组件识别
识别并列出所有 Element Plus 组件及其用途：
- el-input、el-select、el-date-picker
- el-table、el-table-column
- el-dialog、el-drawer
- el-tree、el-upload
- el-pagination、el-button

### 2. DOM 结构分析
- 关键节点的层级结构
- 稳定属性（id/name/data-*）
- 动态属性（Vue生成的哈希class、v-if控制的元素）

### 3. 定位器设计表
| 元素 | 推荐定位策略 | 定位值 | 稳定性 | 备注 |
|------|-------------|--------|--------|------|
| 搜索输入框 | CSS | `.search-area input[placeholder*='{{关键词}}']` | A | |
| 搜索按钮 | XPATH | `//button[.//span[text()='搜索']]` | A | |
| 表格容器 | CSS | `.el-table` | A | |
| 表格行 | CSS | `.el-table__body-wrapper .el-table__row` | B | 动态行 |
| 新增按钮 | XPATH | `//button[.//span[text()='新增']]` | A | |
| 弹窗 | CSS | `.el-dialog` | A | |
| 弹窗确认 | XPATH | `//div[contains(@class,'el-dialog')]//button[.//span[text()='确定']]` | A | |
| 分页器 | CSS | `.el-pagination` | A | |

### 4. Vue 异步等待策略
| 场景 | 等待条件 | WebDriverWait 示例 |
|------|---------|-------------------|
| 页面加载 | 表格出现 | `wait.until(EC.presence_of_element_located(TABLE))` |
| 搜索完成 | loading消失 | `wait.until(EC.invisibility_of_element_located(LOADING))` |
| 弹窗打开 | 弹窗可见 | `wait.until(EC.visibility_of_element_located(DIALOG))` |
| 弹窗关闭 | 弹窗不可见 | `wait.until(EC.invisibility_of_element_located(DIALOG))` |
| 表格刷新 | 行数变化 | 自定义等待逻辑 |

### 5. 自动化风险点
- 动态ID/Class
- iframe嵌套
- 虚拟列表/懒加载
- 权限控制导致的元素缺失
```

📤 **预期产出**：`contexts/{模块}/pages/{页面}/TECH_ANALYSIS.md`

---

## Phase 3.5 — 自动化策略

### P3.5-01 自动化覆盖策略设计

📥 **前置输入**：TEST_CASES.md、TECH_ANALYSIS.md

💬 **提示词**：

```text
基于以下测试用例和技术分析，制定自动化测试策略。

## 输入
- TEST_CASES：{{粘贴 TEST_CASES 用例编号和标题}}
- TECH_ANALYSIS：{{粘贴 TECH_ANALYSIS 定位器设计表}}
- 已有 BasePage 能力：{{粘贴 AUTOMATION_ARCHITECTURE.md 中 BasePage 能力描述}}

## 任务
输出 AUTO_STRATEGY.md：

### 1. 自动化覆盖矩阵
| 用例编号 | 标题 | 优先级 | 是否自动化 | 理由 |
|---------|------|--------|----------|------|
| TC-001 | 页面正常加载 | P0 | ✅ | 基础冒烟，定位器稳定 |
| TC-xxx | ... | P2 | ❌ | 需要人工判断UI美观度 |

### 2. PageObject 拆分方案
```
建议的 Page 类及职责：
- {{AlarmConfigPage}}：报警配置页的搜索/表格/分页操作
- {{AlarmConfigDialog}}：报警配置弹窗的CRUD操作
```

### 3. 公共组件复用分析
- 哪些操作可以复用 BasePage 已有方法
- 是否需要扩展 ElementPlusHelper

### 4. 等待策略建议
- 该页面特有的异步行为
- 建议的等待封装

### 5. ROI 分析
- 预估开发时间：{{X}} 小时
- 预估维护成本：{{Y}} 小时/月
- 手工执行时间：{{Z}} 分钟/次
- ROI = {{Z × 执行频率 - X - Y × 月数}}

## 注意
- P0 用例必须自动化
- 定位器不稳定的用例标注风险
- 一次性操作（如仅上线前执行）不自动化
```

📤 **预期产出**：`contexts/{模块}/pages/{页面}/AUTO_STRATEGY.md`

---

## Phase 4 — 自动化代码生成

### P4-01 生成 Page Object

📥 **前置输入**：TECH_ANALYSIS.md、AUTO_STRATEGY.md、现有 BasePage 代码

💬 **提示词**：

```text
你是Selenium + pytest自动化测试开发专家。请为以下页面生成 Page Object。

## 技术背景
- 被测系统：Vue 3 + Element Plus
- 基类：BasePage（位于 base/base_page.py）
  - 已封装：wait_element / wait_table_loaded / wait_dialog_visible / wait_loading_disappear
  - 导航方法：navigate_to(一级菜单, 二级菜单)
  - 点击方法：click_element（含多级降级：标准点击 → JS点击 → ActionChains点击）
  - 输入方法：input_text（先清空再输入）
- 工具类：ElementPlusHelper（位于 base/element_plus_helper.py）
  - select_option / get_select_value / get_table_data / get_pagination_info

## 页面信息
- 页面名称：{{设备报警配置}}
- TECH_ANALYSIS：{{粘贴定位器设计表}}
- AUTO_STRATEGY：{{粘贴 PageObject 拆分方案}}

## 任务
生成 `{{AlarmConfigPage}}.py`，要求：

### 代码规范
```python
class AlarmConfigPage(BasePage):
    # 1. 所有 Locator 定义为类属性元组
    #    格式：(By.XXX, "selector")
    SEARCH_INPUT = (By.CSS_SELECTOR, ".search-area input[placeholder*='报警']")
    SEARCH_BTN = (By.XPATH, "//button[.//span[text()='搜索']]")
    RESET_BTN = (By.XPATH, "//button[.//span[text()='重置']]")
    ADD_BTN = (By.XPATH, "//button[.//span[text()='新增']]")
    TABLE = (By.CSS_SELECTOR, ".el-table")
    TABLE_ROWS = (By.CSS_SELECTOR, ".el-table__body-wrapper .el-table__row")
    DIALOG = (By.CSS_SELECTOR, ".el-dialog")
    DIALOG_CONFIRM = (By.XPATH, "//div[contains(@class,'el-dialog')]//button[.//span[text()='确定']]")
    
    # 2. navigate() 是唯一页面入口
    def navigate(self):
        self.navigate_to("设备管理", "设备报警配置")
        self.wait_table_loaded()
        return self
    
    # 3. 操作方法不含 assert
    # 4. 操作方法不含 time.sleep > 0.5s
    # 5. 操作方法 return self 支持链式调用
    # 6. 使用 self.logger 记录日志
```

### 必须实现的方法
- navigate() — 导航到页面
- search(keyword) — 搜索
- reset_search() — 重置搜索
- get_table_data() — 获取表格数据
- click_add() — 点击新增
- fill_form(data_dict) — 填写弹窗表单
- confirm_dialog() — 确认弹窗
- cancel_dialog() — 取消弹窗
- click_edit(row_index) — 点击某行的编辑
- click_delete(row_index) — 点击某行的删除
- get_pagination_info() — 获取分页信息

## 约束
- 一次只生成一个 Page Object 文件
- 定位器值从 TECH_ANALYSIS 中取，不要编造
- 操作前确保元素可交互（等待可见+可点击）
```

📤 **预期产出**：`ZJSN_Test-master526/page/{模块}_page/{PageName}.py`

### P4-02 生成测试脚本

📥 **前置输入**：PageObject 代码、TEST_CASES.md、现有 conftest.py

💬 **提示词**：

```text
基于以下 Page Object 和测试用例，生成 pytest 测试脚本。

## 输入
- PageObject：{{粘贴 PageObject 类定义}}
- TEST_CASES：{{粘贴自动化覆盖范围内的用例}}
- 现有 conftest.py：{{粘贴模块级 conftest.py}}

## 任务
生成 `test_{{模块}}.py`，要求：

### 测试类结构
```python
import pytest
import allure

@allure.epic("{{设备管理}}")
@allure.feature("{{设备报警配置}}")
class TestAlarmConfig:
    
    @allure.story("{{页面加载}}")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.smoke
    def test_001_page_load(self, {{alarm_config_page}}):
        """TC-ALARM-001: 页面正常加载"""
        with allure.step("导航到报警配置页"):
            {{alarm_config_page}}.navigate()
        with allure.step("验证页面核心元素"):
            assert {{alarm_config_page}}.is_table_visible(), "表格未加载"
    
    @allure.story("{{搜索功能}}")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_002_search_by_name(self, {{alarm_config_page}}):
        """TC-ALARM-002: 按报警名称搜索"""
        with allure.step("输入搜索关键词"):
            {{alarm_config_page}}.search("{{温度报警}}")
        with allure.step("验证搜索结果"):
            data = {{alarm_config_page}}.get_table_data()
            assert len(data) > 0, "搜索结果为空"
            # 验证所有结果包含搜索关键词
```

### Fixture 使用
- module scope：浏览器驱动（已有，见 conftest.py）
- function scope：Page Object 实例

### 必须遵循的规范
- `@allure.epic/feature/story/severity` 注解完整
- `with allure.step()` 标记关键步骤
- `@pytest.mark.smoke` 标记冒烟用例
- 断言包含失败时的描述信息
- 测试方法独立，不依赖执行顺序
- 数据清理在 fixture teardown 中完成

### 禁止事项
- 不要在测试用例中直接写 Selenium 代码
- 不要使用 time.sleep
- 不要硬编码敏感信息
```

📤 **预期产出**：`ZJSN_Test-master526/script/{模块}/test_{模块}.py`

### P4-03 生成 conftest.py

📥 **前置输入**：PageObject 代码、现有参考 conftest.py

💬 **提示词**：

```text
为 {{设备管理}} 模块生成 conftest.py。

## 参考
{{粘贴 script/system/conftest.py 作为参考模板}}

## 新模块信息
- 模块名称：{{设备管理}}
- 页面列表：
  - {{AlarmConfigPage}} → page/equipment_page/AlarmConfigPage.py
  - {{MaintenancePage}} → page/equipment_page/MaintenancePage.py

## 任务
生成 `script/equipment/conftest.py`：

### 必须包含
```python
@pytest.fixture(scope="module")
def driver_setup():
    """模块级浏览器驱动"""
    # 参考 system/conftest.py 的 pattern
    pass

@pytest.fixture(scope="function")
def alarm_config_page(driver_setup):
    """AlarmConfigPage 实例"""
    page = AlarmConfigPage(driver_setup)
    page.navigate()
    yield page
    # teardown 清理

@pytest.fixture(scope="function")
def maintenance_page(driver_setup):
    """MaintenancePage 实例"""
    pass
```

### 注意事项
- module scope driver 确保同一模块共享浏览器
- fixture 中的 navigate() 保证页面就绪
- 数据清理在 teardown 中，清理失败只发 warning
- 复用 BaseDriver.ensure_logged_in() 保障登录状态
```

📤 **预期产出**：`conftest.py`

### P4-04 按现有规范审查/修正代码

📥 **前置输入**：已生成的 Page Object 或测试脚本

💬 **提示词**：

```text
请审查以下自动化测试代码，对照项目规范找出问题并修正。

## 代码
```python
{{粘贴待审查的代码}}
```

## 审查标准（来自 AUTOMATION_ARCHITECTURE.md 和 REFACTOR_PLAN.md）

### Page Object 规范
- [ ] 继承 BasePage
- [ ] Locator 声明为类属性常量 (By.XXX, "selector")
- [ ] 有 navigate() 方法
- [ ] 操作方法不含 assert
- [ ] 操作方法不含 time.sleep > 0.5s
- [ ] 使用 self.logger 记录日志
- [ ] CSS Selector 优先，XPath 保底

### 测试脚本规范
- [ ] @allure.epic/feature/story/severity 注解完整
- [ ] with allure.step() 标记关键步骤
- [ ] @pytest.mark.smoke 标记冒烟用例
- [ ] 断言含失败描述
- [ ] 测试方法独立
- [ ] 无硬编码敏感信息

### 禁止模式
- [ ] 测试用例中直接使用 driver.find_element
- [ ] time.sleep 硬等待
- [ ] 硬编码URL和密码
- [ ] 无清理逻辑

## 任务
1. 逐项标注通过/不通过
2. 对不通过项给出具体修改建议
3. 输出修正后的完整代码
```

📤 **预期产出**：审查报告 + 修正代码

---

## Phase 4.5 — Bug 分析

### P4.5-01 自动化失败根因分析

📥 **前置输入**：失败截图、HTML、Console日志、代码

💬 **提示词**：

```text
你是一个测试自动化失败分析专家。请分析以下自动化用例失败的原因。

## 失败信息
- 用例名称：{{test_search_by_name}}
- 失败阶段：{{搜索操作 / 断言验证}}
- 错误信息：
```
{{粘贴 pytest 错误输出}}
```

## 附件
- 失败截图：{{上传截图}}
- 页面HTML（失败时）：{{粘贴 HTML 片段}}
- Console日志：{{粘贴浏览器Console日志}}
- 测试代码：
```python
{{粘贴失败用例代码}}
```

## 任务
按以下结构分析，输出 BUG_ANALYSIS.md：

1. **现象描述**：发生了什么
2. **复现分析**：
   - 是否可稳定复现？（复现率：X/5）
   - 什么条件下触发？
3. **根因定位**（从高到低排查）：
   - [ ] 元素定位器失效？（页面结构变化/动态ID）
   - [ ] 等待时间不足？（Vue异步渲染未完成）
   - [ ] 测试数据问题？（数据被删除/数据冲突）
   - [ ] 环境问题？（服务不可用/网络波动）
   - [ ] 产品Bug？（实际是功能缺陷）
4. **责任归属**：
   - 🐛 产品Bug → 提交禅道
   - 🔧 脚本问题 → 修复定位器/等待策略
   - 🌐 环境问题 → 联系运维
   - 📊 数据问题 → 更新测试数据
5. **修复建议**：具体代码修改
6. **回归影响**：其他哪些用例可能受影响？
```

📤 **预期产出**：`04-测试报告/缺陷分析报告/BUG-{编号}_{标题}.md`

---

## Phase 5 — 自动化失败分析

### P5-01 批量失败分析

📥 **前置输入**：Allure报告、test_results.log

💬 **提示词**：

```text
分析以下批量自动化执行结果，找出系统性失败原因。

## 执行结果
```
{{粘贴 pytest 执行摘要 或 Allure 报告概览}}
总用例：{{N}} | 通过：{{N}} | 失败：{{N}} | 跳过：{{N}}
```

## 失败用例列表
{{粘贴所有失败用例的名称和错误信息}}

## 任务
1. **失败分类**：按失败原因将用例分组
   - 同类定位器失效：{{N}} 条
   - 同类等待不足：{{N}} 条
   - 同类数据问题：{{N}} 条
   - 环境问题：{{N}} 条
2. **模式识别**：
   - 是否集中在某个模块？
   - 是否集中在某个时间点（如某次部署后）？
   - 是否有共同的根因？
3. **优先级排序**：按影响面排列修复顺序
4. **修复计划**：逐类给出修复方案和预估工作量
```

📤 **预期产出**：`04-测试报告/测试执行报告/FAIL-{日期}_批量分析.md`

---

## Phase 6 — 接口测试

### P6-01 接口测试设计

📥 **前置输入**：API文档/Network抓包、PAGE_CONTEXT.md中的接口依赖

💬 **提示词**：

```text
基于以下接口信息，设计接口测试方案。

## 接口信息
{{粘贴接口列表（从浏览器Network面板或API文档获取）}}

示例格式：
| 接口 | 方法 | URL | 参数 | 触发时机 |
|------|------|-----|------|---------|
| 获取报警列表 | GET | /api/alarm/list | page, size, keyword | 页面加载/搜索 |
| 新增报警 | POST | /api/alarm/add | {name, type, threshold} | 弹窗确认 |
| 删除报警 | DELETE | /api/alarm/{id} | id | 删除确认 |

## 任务
输出 API_TEST_DESIGN.md，覆盖：

1. **参数边界测试**：
   - 必填参数缺失
   - 参数类型错误（如传字符串给数字字段）
   - 参数超长/特殊字符
   - 分页参数边界（page=0, page=-1, size=0, size=10000）

2. **Token校验**：
   - 无Token请求
   - 过期Token请求
   - 伪造Token请求

3. **权限校验**：
   - 低权限用户调用高权限接口
   - 跨租户数据访问

4. **异常测试**：
   - 请求不存在的资源ID
   - 重复提交（幂等性）
   - 并发请求

5. **安全测试**：
   - SQL注入字符
   - XSS字符
   - 敏感信息是否在响应中泄露

## 自动化实现（可选）
需要时生成 pytest + requests 脚本：
```python
import requests
import pytest

class TestAlarmAPI:
    BASE_URL = "http://8.136.215.171:8081/api"
    
    def test_get_alarm_list_unauthorized(self):
        """无Token请求应返回401"""
        resp = requests.get(f"{self.BASE_URL}/alarm/list")
        assert resp.status_code == 401
```
```

📤 **预期产出**：`contexts/{模块}/API_TEST_DESIGN.md`

---

## Phase 7 — 持续集成分析

### P7-01 Jenkins/CI 分析

📥 **前置输入**：Jenkins构建日志、Allure报告链接

💬 **提示词**：

```text
分析以下CI构建结果，诊断问题。

## 构建信息
- Jenkins Job：{{ZJSN_Test}}
- 构建编号：{{#123}}
- 构建状态：{{失败}}
- 构建日志：
```
{{粘贴关键日志片段}}
```

## 任务
1. **构建失败原因**：快速定位
2. **与上次成功构建的差异**：
   - 代码变更？
   - 环境变更？
   - 数据变更？
3. **失败类型判断**：
   - 编译/依赖问题（环境问题）
   - 用例失败（测试问题）
   - 超时（性能/环境问题）
4. **修复建议**
5. **CI配置优化建议**：
   - 是否需要添加重试？
   - 是否需要调整超时时间？
   - 是否需要增加前置检查步骤？
```

📤 **预期产出**：`02-项目文档/CI_ANALYSIS.md`

---

## Phase 8 — 测试总结

### P8-01 测试周期总结

📥 **前置输入**：多个测试执行报告、Bug统计

💬 **提示词**：

```text
基于以下测试执行数据，生成测试周期总结报告。

## 输入数据
- 测试周期：{{2026-06-01 ~ 2026-06-09}}
- 测试范围：{{设备管理模块}}
- 执行报告汇总：
  - 总用例数：{{N}}
  - 通过：{{N}} / 失败：{{N}} / 阻塞：{{N}}
  - 通过率：{{%}}
- Bug统计：
  - Blocker：{{N}} / Critical：{{N}} / Major：{{N}} / Minor：{{N}}
- 自动化覆盖：{{%}}

## 任务
输出 TEST_SUMMARY.md，包含：

1. **测试概况**
2. **用例执行统计**（总表+按模块分表）
3. **Bug统计**（按严重程度+按模块）
4. **遗留Bug清单与风险评估**
5. **自动化覆盖情况**
6. **测试结论**：
   - [ ] ✅ 建议上线
   - [ ] ⚠️ 有条件上线
   - [ ] ❌ 不建议上线
7. **后续建议**

## 格式
参考 `contexts/summaries/TEST_SUMMARY_template.md`
```

📤 **预期产出**：`04-测试报告/测试总结报告/{周期}_测试总结.md`

---

## Phase 9 — 知识沉淀

### P9-01 项目知识更新

📥 **前置输入**：本轮测试的所有产出文档

💬 **提示词**：

```text
本轮测试已完成，请更新 PROJECT_KNOWLEDGE.md。

## 本轮新增
- 新增模块上下文：{{列表}}
- 新增测试用例：{{N}} 条
- 新增自动化用例：{{N}} 条
- 新发现的高频Bug：{{列表}}
- 新的踩坑经验：{{列表}}

## 任务
更新 PROJECT_KNOWLEDGE.md 以下章节：
1. **已完成测试工作**：添加本轮新增的模块和用例数
2. **测试用例规范**：如有新的规范补充
3. **踩坑经验**：添加本轮新发现的坑
4. **当前推进**：更新进度状态
5. **风险模块**：更新高风险模块列表

## 同步要求
同步更新以下文件：
- `测试进度追踪.md`
- 各模块 `MODULE_CONTEXT.md` 中的状态标记
```

📤 **预期产出**：更新后的 `PROJECT_KNOWLEDGE.md`、`测试进度追踪.md`

---

# 二、跨场景通用提示词

---

## S-01 上下文恢复（新会话开始）

📥 **前置输入**：上次会话的MODULE_CONTEXT、PAGE_CONTEXT

💬 **提示词**：

```text
我正在继续 {{设备管理-报警配置页}} 的测试工作。请先阅读以下上下文文档，确认你理解了当前状态后再继续。

## 上下文文档
1. PROJECT_KNOWLEDGE：{{粘贴 02-项目文档/PROJECT_KNOWLEDGE.md}}
2. MODULE_CONTEXT：{{粘贴 contexts/equipment/MODULE_CONTEXT.md}}
3. PAGE_CONTEXT：{{粘贴 contexts/equipment/pages/alarm-config/PAGE_CONTEXT.md}}
4. 当前进度：Phase {{3}} — {{技术实现分析}}，已完成 Phase 0.5/1/1.5/2

## 任务
1. 阅读并总结你对当前模块/页面的理解（确认理解正确）
2. 列出已完成的 Phase 和产出文档
3. 告诉我下一个 Phase 的建议入口
4. 等我确认后继续
```

---

## S-02 上下文同步（会话结束）

📥 **前置输入**：本次会话的所有变更摘要

💬 **提示词**：

```text
本次会话即将结束，请帮我做上下文同步。

## 本次变更摘要
- 新增/修改文件：
  - {{contexts/equipment/pages/alarm-config/PAGE_CONTEXT.md}} — 补充了搜索区元素
  - {{contexts/equipment/pages/alarm-config/TEST_DESIGN.md}} — 新增15条测试设计
- Phase 进展：{{Phase 1 → Phase 2 完成}}
- 关键决策：{{如：搜索区使用模糊匹配而非精确匹配}}
- 遗留问题：{{如：弹窗中的动态下拉框定位器待确认}}

## 任务
1. 更新 `测试进度追踪.md` 中对应模块的状态
2. 更新 `contexts/{模块}/MODULE_CONTEXT.md` 中的状态标记
3. 生成本次会话的上下文摘要（用于下次会话恢复）
4. 列出建议下次会话继续的任务
```

---

## S-03 代码审查（测试脚本）

📥 **前置输入**：测试脚本代码

💬 **提示词**：

```text
审查以下自动化测试脚本，对照项目规范找出问题。

## 代码
```python
{{粘贴完整代码}}
```

## 审查维度
1. **PageObject 规范**：Locator声明、navigate方法、无assert、无sleep
2. **测试脚本规范**：Allure注解、step标记、断言描述
3. **代码质量**：重复代码、命名、注释、异常处理
4. **稳定性风险**：硬等待、脆弱定位器、无重试机制
5. **安全性**：敏感信息、环境变量

## 输出
- 问题清单（严重/建议）
- 每个问题的修复代码
- 整体评分
```

---

## S-04 测试数据生成

📥 **前置输入**：TEST_CASES.md 中的测试数据列

💬 **提示词**：

```text
请为以下测试场景生成测试数据。

## 数据需求
- 模块：{{设备管理}}
- 场景：
  1. {{新增报警配置}} — 需要合法数据 3 组
  2. {{搜索报警}} — 需要覆盖：精确匹配、模糊匹配、无结果
  3. {{边界值测试}} — 需要：最小值、最大值、超限值

## 数据约束
- 名称：{{不超过50字符，不能重复}}
- 阈值：{{0-1000 之间的数字}}
- 类型：{{温度/压力/流量}}

## 输出格式
| 场景 | 输入数据 | 预期结果 |
|------|---------|---------|
| 合法新增1 | name=温度报警 type=温度 threshold=80 | 新增成功 |
```

---

## S-05 Element Plus 疑难定位

📥 **前置输入**：具体疑难元素的HTML片段

💬 **提示词**：

```text
我在定位以下 Element Plus 组件时遇到困难，请帮我设计定位策略。

## 问题组件
```html
{{粘贴具体的HTML片段}}
```

## 已尝试的定位方式
1. {{CSS Selector 尝试}} → 失败原因：{{动态class}}
2. {{XPath 尝试}} → 失败原因：{{元素未找到}}

## 组件特征
- 组件类型：{{el-select 远程搜索下拉框 / el-date-picker 日期范围 / el-cascader 级联选择器 / ...}}
- 特殊行为：{{下拉选项动态加载 / 选项在 body 层 / 需要先触发才渲染}}

## 任务
1. 分析为什么现有定位方式失败
2. 给出 2-3 种替代定位策略（从A级到C级）
3. 给出完整的等待+操作代码
4. 建议是否需要扩展 ElementPlusHelper
```

---

## S-06 微信小程序测试设计

📥 **前置输入**：小程序页面截图、操作手册

💬 **提示词**：

```text
你是一个微信小程序测试工程师。请为以下小程序页面设计测试用例。

## 页面信息
- 页面名称：{{在线学习-课程列表}}
- 所属Tab：{{首页 → 人员培训 → 在线学习}}
- 参考手册：{{粘贴 鞍集涂源管理系统_微信小程序用户操作手册_V1.0.4.md 相关章节}}

## 小程序特有测试点
请特别关注：
- 微信登录态（一键登录/手机号登录/多角色切换）
- 不同微信版本兼容性
- 网络切换（WiFi ↔ 4G/5G）
- 小程序前后台切换
- 分享/转发功能
- 微信支付（如涉及）
- 缓存策略（本地数据 vs 服务端数据）
- 授权弹窗（位置/相机/存储等权限）

## 输出格式
与Web端用例格式一致：编号 | 标题 | 模块 | 优先级 | 前置条件 | 步骤 | 数据 | 预期结果 | 实际结果
```

---

## S-07 测试进度报告生成

📥 **前置输入**：本周工作日志

💬 **提示词**：

```text
基于我本周的日报和当前测试进度，生成一份进度报告。

## 输入
- 本周日报：
{{粘贴 03-工作日志/日报/2026-06/ 下的日报内容}}
- 当前进度追踪：
{{粘贴 测试进度追踪.md}}

## 任务
1. 计算本周完成的工作量（用例数、自动化数、Bug数）
2. 与上周对比
3. 更新 `测试进度追踪.md` 中的状态
4. 识别进度偏差（哪些模块落后计划）
5. 生成周报草稿
```

---

## S-08 模块上下文完整性检查

📥 **前置输入**：contexts/ 目录

💬 **提示词**：

```text
检查 contexts/ 下各模块的文档完整性。

## 检查标准
对每个模块/页面，检查是否具备以下文档：
- [ ] MODULE_CONTEXT.md（Phase 0.5）
- [ ] 每个页面有 PAGE_CONTEXT.md（Phase 1）
- [ ] 每个页面有 RISK_MODEL.md（Phase 1.5）
- [ ] 每个页面有 TEST_DESIGN.md（Phase 2）
- [ ] 每个页面有 TEST_CASES.md（Phase 2.5）
- [ ] 每个页面有 TECH_ANALYSIS.md（Phase 3）
- [ ] 每个页面有 PAGE_ELEMENT_POSITION.md（Phase 3）
- [ ] 每个页面有 AUTO_STRATEGY.md（Phase 3.5）

## 任务
1. 逐模块输出缺失文档清单
2. 标注优先级：P0（阻塞测试执行）/ P1（影响质量）/ P2（锦上添花）
3. 给出补充建议（哪些可以基于现有信息推断，哪些需要实际访问页面）
```

---

# 三、提示词使用速查

| 场景 | 使用哪个提示词 | 入口 |
|------|-------------|------|
| 新项目启动 | P0-01 | 新会话 |
| 新模块分析 | P0.5-01 | 新会话 |
| 拿到原型图/PRD | P0.8-01 | 新会话 |
| 拿到页面截图 | P1-01 | 会话A2 |
| 拿到HTML源码 | P1-02、P3-01 | 会话A2/B |
| 开始设计测试 | P2-01 | 会话A3 |
| 生成执行用例 | P2.5-01 | 会话A3（同会话） |
| 准备写自动化 | P3-01 → P3.5-01 | 会话B |
| 写PageObject | P4-01 | 会话C |
| 写测试脚本 | P4-02 | 会话C |
| 写conftest | P4-03 | 会话C |
| 代码Review | P4-04、S-03 | 任何会话 |
| 用例失败了 | P4.5-01 | 会话D |
| 批量失败 | P5-01 | 会话E |
| 做接口测试 | P6-01 | 会话F |
| CI构建失败 | P7-01 | 会话G |
| 测试周期结束 | P8-01 | 会话H |
| 项目归档 | P9-01 | 会话I |
| 第二天继续工作 | S-01 | 任意会话开始 |
| 结束今天工作 | S-02 | 任意会话结束 |
| 遇到Element Plus定位难题 | S-05 | 随时 |
| 需要造测试数据 | S-04 | 随时 |
| 测小程序页面 | S-06 | 新会话 |
| 生成进度报告 | S-07 | 周末/周五 |
| 文档完整性审计 | S-08 | 定期 |

---

> **维护说明**：新场景出现时补充新提示词。每个提示词使用后如有改进，及时更新本文件。
> 所有提示词中的 `{{ }}` 占位符使用前替换为实际内容。
