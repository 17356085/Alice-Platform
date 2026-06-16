# Workflows

## 目标
把高频协作任务固化为标准流程，统一输入、阶段、产物、输出和完成标准。

## 设计原则
- Workflow 必须服务于模块上下文树
- 每个流程都要指定产物落位
- 每个流程都要绑定一个或多个 Skill
- 每个流程都能被新 AI 快速接手

## 当前流程（9 个）

### 核心流程（6 个）

| Workflow | 涉及 Skill | 说明 |
|----------|-----------|------|
| project-takeover | project-context-manager | 新项目初始化 |
| module-onboarding | module-modeling → page-analysis → risk-modeling | 新模块入场 |
| module-test-design | testcase-design → test-data-generation | 模块测试设计 |
| automation-implementation | page-object-generator → test-script-generator → conftest-generator → code-consistency-checker | 自动化代码实现 |
| automation-failure-closure | bug-analysis → ci-pipeline-analysis → knowledge-extractor | 失败闭环 |
| test-cycle-closure | test-summary → allure-report-analyzer → knowledge-extractor | 测试周期总结 |

### 新增流程（3 个）

| Workflow | 涉及 Skill | 说明 |
|----------|-----------|------|
| session-sync | context-sync | 会话上下文同步 |
| api-test-design | api-testing | 接口测试设计 |
| code-health-check | code-consistency-checker | 代码质量检查（2026-06 新增） |
| ci-pipeline-orchestration | jenkinsfile-generator | CI Pipeline 编排（2026-06 新增） |
| knowledge-sync | knowledge-extractor + context-sync | 知识沉淀同步（2026-06 新增） |

## 完整注册表
→ `workflow-registry.yaml`
