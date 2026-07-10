# Changelog

All notable changes to alice-governance will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-07-09

### Added

**Skill 体系**:
- 测试自动化 Skill 库（`skills/`）：24 个 Skill，覆盖 8 大类别
  - `automation/`（自动化）: page-analyze, test-generate, page-object-generator, auto-strategy, tech-analysis
  - `test-design/`（测试设计）: testcase-design, risk-modeling, boundary-value-analysis
  - `execution/`（执行）: allure-report-analyzer, test-runner, retry-strategy
  - `diagnosis/`（诊断）: bug-analysis, root-cause-analysis, flaky-test-detector
  - `knowledge/`（知识管理）: knowledge-manager, knowledge-retriever
  - `project/`（项目管理）: project-context-manager, hygiene-check, module-scanner
  - `reporting/`（报告）: test-report-generator, coverage-reporter
  - `requirements/`（需求分析）: requirements-analyzer, acceptance-criteria-extractor

- 开发 Skill 库（`skills-dev/`）：32 个 Skill，覆盖 7 大类别
  - `architecture/`（架构）: project-scanner, tech-stack-decider, component-planner
  - `backend/`（后端）: crud-generator, fastapi-router-generator, db-schema-designer
  - `frontend/`（前端）: vue-component-generator, composable-generator, form-builder
  - `code-review/`（代码审查）: source-code-reviewer, security-reviewer, performance-reviewer
  - `debug/`（调试）: error-locator, stack-trace-analyzer, regression-finder
  - `test-dev/`（测试开发）: unit-test-generator, integration-test-generator
  - `review/`（评审）: pr-reviewer, design-doc-reviewer

**知识库**（`knowledge/`）:
- 测试模式库（`test-patterns/`）: CRUD 测试、搜索过滤、权限矩阵、批量操作
- 踩坑经验库（`pitfalls/`）: Element Plus 已知问题、Selenium 反模式
- 供 RAG 检索引擎（平台 `RAGEngine`）和 `KnowledgeStore` 接口使用

**校验器**（`validators/`）:
- `sop_validator.py` — SOP 合规校验（检查 Agent 是否遵循 SOP 约束）
- `coverage_checker.py` — 覆盖率检查（检查测试覆盖率是否达标）

**上下文模板**（`context_templates/`）:
- `environments.yaml` — 测试环境配置模板（URL、账号、浏览器配置）
- `known-issues.yaml` — 已知问题库（可在 Skill 中注入，避免重复踩坑）

**开发 SOP**（`sop_dev/`）:
- 10 Phase 开发流程定义（`phases/` 目录，每 Phase 一个 YAML）
- Phase 01-10: Plan → Requirements → Architecture → Component Design → Frontend → Backend → Code Review → Dev Test → Debug & Fix → Build

**Agent 定义**（`agents/`）:
- `agent-definitions.yaml` — 所有 Agent 的 Skill 配置、Model Tier 配置
- 8 个测试 Agent + 9 个开发 Agent 定义

### Technical Details

**版本**: 1.0.0（与 alice-engine 1.0.0 配套）

**Python 版本**: >=3.11

**依赖**: 零外部依赖（所有 Skill 和配置文件为静态资源，通过 `get_pack_path()` 路径访问）

**安装**:
```bash
pip install alice-governance    # 从 PyPI（发布后）
pip install -e .                # 本地开发
```

**与 alice-engine 集成**:
```python
from alice_engine.core.skill_loader import SkillLoader
from alice_governance import get_pack_path

loader = SkillLoader(governance_path=get_pack_path())
skill = loader.load_skill("automation/page-object-generator")
print(skill.prompt)
```

---

## [Unreleased]

### Planned

**Skill 增强**:
- [ ] Browser-Use 适配 Skill（`automation/browser-use-driver`）
- [ ] 小程序测试 Skill（`automation/miniprogram-*`）
- [ ] E2E 场景测试 Skill（跨页面流程）

**知识库增强**:
- [ ] 更多测试模式（Vue 3 Composition API、异步组件测试）
- [ ] 更多踩坑经验（WebDriver BiDi、Shadow DOM）
- [ ] 项目特定知识库支持（`.tlo/knowledge/`）

**校验器增强**:
- [ ] 更严格的 SOP 门禁（Gate 检查）
- [ ] 基于 LLM 的智能 SOP 合规评分
- [ ] 自定义校验规则支持

**Agent 增强**:
- [ ] Agent 能力矩阵可视化
- [ ] Model Tier 动态调整（根据任务复杂度）
- [ ] Multi-Agent 协作定义（跨 Agent 依赖）

---

[1.0.0]: https://github.com/your-org/alice-governance/releases/tag/v1.0.0
