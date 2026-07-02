# Skills

## 目标
将高频、可复用、可约束的 AI 能力沉淀为 Skill。

## 最小定义结构
- 目标
- 输入
- 输出
- 规则
- 依赖
- 边界
- 关联 Workflow

## 当前统计
**28 个 Skill 文件**（24 active + 4 deprecated）

### 按分类分布

| 分类 | 数量 | 目录 | 说明 |
|------|------|------|------|
| project/ | 2 | `skills/project/` | 项目级上下文管理（含 CURRENT_TASK 支持） |
| requirements/ | 2 | `skills/requirements/` | 需求分析与模块建模 |
| test-design/ | 6 | `skills/test-design/` | 测试分析与设计 |
| automation/ | 6 | `skills/automation/` | 自动化技术与代码生成 |
| execution/ | 2 | `skills/execution/` | 执行与报告 |
| diagnosis/ | 3 | `skills/diagnosis/` | Bug 诊断与 CI 分析 |
| knowledge/ | 2 | `skills/knowledge/` | 知识管理（knowledge-manager 合并了 extract+precipitate） |
| reporting/ | 2 | `skills/reporting/` | 进度与报告 |
| _deprecated/ | 4 | `skills/_deprecated/` | 废弃归档 |

### 废弃 Skill

| Skill | 替代 |
|-------|------|
| `code-generation` | → page-object-generator + test-script-generator + conftest-generator |
| `element-plus-locator` | → tech-analysis（深度定位能力已合并） |
| `knowledge-extractor` | → knowledge-manager (mode: extract) |
| `knowledge-precipitation` | → knowledge-manager (mode: precipitate) |

## 核心 Skill（高频使用）

| Skill | 用途 | 口语化触发 |
|-------|------|-----------|
| page-analysis | 页面元素分析 | "看看XX页面有什么元素" |
| testcase-design | 测试用例设计 | "给XX页面设计测试用例" |
| tech-analysis | 定位器 + 等待策略 | "这个按钮怎么定位" |
| code-consistency-checker | 代码规范检查 | "这段代码写得对不对" |
| bug-analysis | 失败根因分析 | "这个用例为什么挂了" |
| page-object-generator | Page Object 生成 | "生成XX的PageObject" |
| jenkinsfile-generator | CI Pipeline 更新 | "帮我更新CI配置" |
| knowledge-extractor | Bug→坑位知识沉淀 | "这个Bug其他人也会遇到吗" |
| allure-report-analyzer | 测试报告自动摘要 | "这次测试结果怎么样" |
| context-sync | 会话上下文同步 | "上次做到哪了" |

## 完整注册表
→ `skill-registry.yaml`

## 口语化路由
→ `CLAUDE.md` § 口语化入口（21条 "你可以这样说" → Skill 映射）
