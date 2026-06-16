# AI辅助测试开发_标准作业流程（SOP）

------

# 1. 文档目标

本SOP用于规范AI在测试开发工作中的使用方式。

目标：

- 提高测试分析效率
- 提高测试设计质量
- 提高自动化开发效率
- 降低上下文污染
- 建立项目知识沉淀体系
- 建立可复用测试开发工作流

适用对象：

- 测试开发工程师
- 自动化测试工程师
- 测试实习生
- QA工程师

适用技术栈：

- Vue
- Element Plus
- Selenium
- pytest
- Jenkins
- Allure
- GitLab CI/CD

------

# 2. AI模型使用规范

## 2.1 通用模型推荐

| 场景           | 推荐模型 |
| -------------- | -------- |
| 项目初始化     | Opus / DeepSeek V4 Pro |
| 模块建模       | Sonnet / DeepSeek V4 Pro |
| 需求分析       | Sonnet / DeepSeek V4 Pro |
| 页面分析       | Sonnet / DeepSeek V4 Pro |
| 风险建模       | Sonnet / DeepSeek V4 Pro |
| 测试设计       | Sonnet / DeepSeek V4 Pro |
| 测试执行表生成 | Haiku |
| 技术实现分析   | Sonnet / DeepSeek V4 Pro |
| 自动化策略设计 | Sonnet / DeepSeek V4 Pro |
| 自动化代码生成 | Sonnet / DeepSeek V4 Pro |
| 普通Bug分析    | Sonnet / DeepSeek V4 Pro |
| 疑难Bug分析    | Opus / DeepSeek V4 Pro |
| 接口测试       | Sonnet / DeepSeek V4 Pro |
| 测试总结       | Haiku |
| 项目沉淀       | Sonnet / DeepSeek V4 Pro |
| 上下文同步更新 | Sonnet / DeepSeek V4 Pro |

## 2.2 Claude Code 环境说明

当前测试开发环境使用 **Claude Code**（Claude Agent SDK），具备以下增强能力：

| 能力 | 说明 | 适用阶段 |
|------|------|---------|
| **Plan Mode** (`/plan`) | 复杂任务先出计划、审批后再执行 | Phase 0, 3.5, 4, 7 |
| **Agent 工具** | 并行探索多个文件/模块 | Phase 0, 0.5, 1, 3 |
| **Skill 系统** | 领域专用能力（code-review, security-review, verify） | Phase 5, 7 |
| **Workflow** | 多 Agent 编排（ultracode 模式） | Phase 0, 4 |
| **TodoWrite** | 任务追踪与进度可视化 | 所有阶段 |
| **Memory** | 持久化知识存储 | Phase 9 |

> **模型选择原则**：DeepSeek V4 Pro 是当前环境默认模型，复杂架构决策可切换到 Opus。Haiku 仅用于轻量级格式化/整理任务。

------

# 3. 会话管理规范

## 3.1 项目级会话

项目初始化仅执行一次。

生成：

PROJECT_CONTEXT.md

保存至本地。

后续所有分析均引用该文档。

------

## 3.2 模块级会话

每个模块独立会话。

例如：

- 用户管理
- 角色管理
- 菜单管理
- 工单管理

禁止多个模块混入同一会话。

------

## 3.3 自动化会话

自动化设计与代码生成独立会话。

不要混入测试设计。

------

## 3.4 Bug会话

建议：

一个Bug一个会话。

或：

一个模块一个Bug分析会话。

------

## 3.5 上下文规范

禁止：

一个项目持续对话100轮以上。

推荐：

PROJECT_CONTEXT.md

↓

MODULE_CONTEXT.md

↓

PAGE_CONTEXT.md

通过文档进行上下文传递。

------

# 4. 工作流总览

项目初始化

↓

模块建模

↓

需求分析

↓

页面分析

↓

风险建模

↓

测试设计

↓

测试执行表生成

↓

测试执行

↓

技术实现分析

↓

自动化策略设计

↓

自动化代码生成

↓

缺陷分析

↓

接口测试

↓

持续集成分析

↓

测试总结

↓

项目沉淀

------

## 4.1 Phase ↔ 会话 ↔ Prompt 对照表

| SOP Phase | 阶段名称 | 执行模板会话 | Prompt模板 | 产出文档 |
|-----------|---------|-------------|-----------|---------|
| Phase 0 | 项目初始化 | 会话0（项目初始化） | Phase 0 Prompt | PROJECT_CONTEXT.md |
| Phase 0.5 | 模块建模 | 会话A1（模块分析） | Phase 0.5 Prompt | MODULE_CONTEXT.md |
| Phase 0.8 | 需求分析 | — | Phase 0.8 Prompt | 需求分析文档 |
| Phase 1 | 页面分析 | 会话A2（页面分析+风险建模） | Phase 1 Prompt | PAGE_CONTEXT.md |
| Phase 1.5 | 风险建模 | 会话A2（页面分析+风险建模） | Phase 1.5 Prompt | RISK_MODEL.md |
| Phase 2 | 测试设计 | 会话A3（测试设计+执行表） | Phase 2 Prompt | TEST_DESIGN.md |
| Phase 2.5 | 测试执行表 | 会话A3（测试设计+执行表） | Phase 2 Prompt | TEST_CASES.md |
| Phase 3 | 技术实现分析 | 会话B（自动化分析设计） | Phase 3 Prompt | PAGE_ELEMENT_POSITION |
| Phase 3.5 | 自动化策略 | 会话B（自动化分析设计） | Phase 3.5 Prompt | AUTOMATION_DESIGN / AUTO_STRATEGY |
| Phase 4 | 自动化代码生成 | 会话C（自动化代码开发） | Phase 5 Prompt | BasePage / PageObject / conftest / test_*.py |
| Phase 4.5 | Bug分析 | 会话D（Bug分析） | Phase 4.5 Prompt | BUG_ANALYSIS.md |
| Phase 4.8 | 回归测试设计 | — | Phase 4.8 Prompt | 回归测试方案 |
| Phase 5 | 自动化失败分析 | 会话E（自动化失败分析） | Phase 5.5 / 5.8 Prompt | FAIL_ANALYSIS.md |
| Phase 6 | 接口测试 | 会话F（接口测试） | Phase 6 / 6.5 Prompt | API_TEST_DESIGN.md |
| Phase 7 | 持续集成分析 | 会话G（Jenkins/Allure分析） | Phase 7 / 8 Prompt | CI分析报告 |
| Phase 8 | 测试总结 | 会话H（测试总结） | Phase 9 Prompt | TEST_SUMMARY.md |
| Phase 9 | 知识沉淀 | 会话I（知识库更新） | Phase 10 Prompt | PROJECT_KNOWLEDGE.md |
| — | 上下文同步 | 会话J（上下文同步更新）★新增 | Phase 10 Prompt（扩展） | 更新的上下文文档 |

> **使用说明**：选择正确的入口 —— 新模块从 Phase 0.5 + 会话A1 开始；已有模块补充测试从 Phase 1 + 会话A2 开始；Bug分析从 Phase 4.5 + 会话D 开始。

------

# 5. Phase 0 项目初始化

模型：

Opus

目标：

建立项目级上下文。

输入：

- 项目URL
- 测试账号
- 技术栈
- 项目简介

输出：

PROJECT_CONTEXT.md

内容：

- 系统简介
- 技术栈
- 用户角色
- 模块树
- 权限模型
- 核心业务流程
- 风险矩阵
- 自动化优先级

------

# 6. Phase 0.5 模块建模

模型：

Sonnet

目标：

建立模块级上下文。

输入：

- PROJECT_CONTEXT.md
- 模块入口URL

输出：

MODULE_CONTEXT.md

内容：

- 模块目标
- 页面清单
- 页面关系
- 核心流程
- 数据对象
- 权限关系
- 风险点
- 自动化价值

------

# 7. Phase 0.8 需求分析与测试计划

模型：

Sonnet

目标：

提前发现需求风险。

输入：

- PRD
- 原型图
- 禅道需求
- 产品说明

输出：

- 需求目标
- 业务规则
- 测试范围
- 非测试范围
- 风险点
- 测试计划
- 自动化机会

------

# 8. Phase 1 页面分析

模型：

Sonnet

输入：

- PROJECT_CONTEXT.md
- MODULE_CONTEXT.md
- 页面URL
- 页面截图

输出：

PAGE_CONTEXT.md

内容：

- 页面目标
- 页面结构
- 输入区
- 查询区
- 表格区
- 分页区
- 弹窗区
- 按钮区
- 权限点
- 风险点

------

# 9. Phase 1.5 风险建模

模型：

Sonnet

输出：

- 业务风险
- 权限风险
- 数据风险
- 接口风险
- 性能风险
- 安全风险

并输出：

P0

P1

P2

风险等级。

------

# 10. Phase 2 测试设计

模型：

Sonnet

输出：

- 功能测试
- UI测试
- 边界值测试
- 异常测试
- 权限测试
- 数据校验测试
- 接口联动测试
- 安全测试

同时输出：

自动化优先级：

P0

P1

P2

------

# 11. Phase 2.5 测试执行表

模型：

Haiku

输出：

Excel格式测试用例。

字段：

- 用例编号
- 用例标题
- 所属模块
- 优先级
- 前置条件
- 测试步骤
- 测试数据
- 预期结果
- 实际结果

------

# 12. Phase 3 技术实现分析

模型：

Sonnet

测试开发核心阶段。

输入：

- HTML
- 页面截图

输出：

## 页面技术结构

- 搜索区
- 表格区
- 分页区
- 弹窗区
- 上传区
- 树结构

------

## Element Plus组件识别

识别：

- el-input
- el-select
- el-table
- el-dialog
- el-tree
- el-upload
- el-date-picker

------

## DOM结构分析

分析：

- 关键节点
- 稳定属性
- 动态属性

------

## 定位器设计

A级：

- data-testid
- id
- name
- placeholder

B级：

- CSS Selector

C级：

- XPath
- 动态class
- nth-child

------

## Vue异步分析

分析：

- 页面刷新
- 表格刷新
- 分页刷新
- 弹窗加载
- 表单回显

------

## WebDriverWait建议

输出：

- 页面加载等待
- 搜索等待
- 弹窗等待
- 表格等待

------

## 自动化风险分析

分析：

- Loading
- 动态DOM
- 动态ID
- 权限控制
- 虚拟列表

------

# 13. Phase 3.5 自动化策略设计

模型：

Sonnet

目标：

决定自动化覆盖范围。

输出：

## 自动化覆盖矩阵

P0

必须自动化

P1

建议自动化

P2

手工测试

------

## PageObject拆分方案

例如：

- LoginPage
- UserPage
- RolePage
- MenuPage

------

## 公共组件设计

例如：

- BaseTable
- BaseDialog
- BaseTree
- BaseUpload

------

## 等待策略库

例如：

- wait_table_loaded
- wait_dialog_visible
- wait_loading_disappear

------

## ROI分析

输出：

- 开发成本
- 维护成本
- 收益分析

------

# 14. Phase 4 自动化代码生成

模型：

Sonnet

顺序：

1.BasePage.py

2.LoginPage.py

3.XXXPage.py

4.conftest.py

5.test_xxx.py

要求：

- Selenium
- pytest
- PageObject
- WebDriverWait
- 企业规范

一次只生成一个文件。

------

# 15. Phase 5 缺陷分析

普通问题：

Sonnet

复杂问题：

Opus

输入：

- FAIL用例
- 截图
- HTML
- Console日志
- 接口信息
- 代码

输出：

- 根因分析
- 责任归属
- 修复建议
- 回归方案

同时生成：

禅道Bug内容。

------

# 16. Phase 6 接口测试

模型：

Sonnet

输出：

- 参数边界
- Token校验
- 权限校验
- 异常测试
- 安全测试

需要时生成：

- requests封装
- pytest脚本
- Token处理

------

# 17. Phase 7 持续集成分析

支持：

- Jenkins
- Allure
- GitLab CI

输出：

- 构建分析
- 失败原因
- 风险评估
- 修复建议

------

# 18. Phase 8 测试总结

模型：

Haiku

输出：

- 测试范围
- 执行情况
- Bug统计
- 风险评估
- 测试结论
- 上线建议

------

# 19. Phase 9 项目知识沉淀

模型：

Sonnet

输出：

PROJECT_KNOWLEDGE.md

内容：

- 高频Bug
- 风险模块
- 自动化覆盖情况
- 测试经验总结
- 后续优化建议

------

# 20. 核心原则

原则一：

模块级管理优于超长会话。

原则二：

文档传递上下文优于上下文记忆。

原则三：

先分析后编码。

原则四：

先设计后自动化。

原则五：

知识沉淀比单次测试更重要。

原则六：

AI辅助决策，人负责最终判断。