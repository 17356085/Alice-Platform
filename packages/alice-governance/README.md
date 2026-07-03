# Alice Governance

AI 测试自动化 Governance SDK — Skill 定义、校验器、知识库。

## 安装

```bash
pip install -e .
```

## 包含内容

```text
alice_governance/
├── skills/              测试自动化 Skill (24 个)
│   ├── automation/      自动化相关 Skill
│   ├── test-design/     测试设计 Skill
│   ├── execution/       执行相关 Skill
│   ├── diagnosis/       诊断 Skill
│   ├── knowledge/       知识管理 Skill
│   ├── project/         项目管理 Skill
│   ├── reporting/       报告 Skill
│   └── requirements/    需求分析 Skill
├── skills-dev/          开发 Skill (32 个)
│   ├── architecture/    架构设计 Skill
│   ├── backend/         后端开发 Skill
│   ├── frontend/        前端开发 Skill
│   ├── code-review/     代码审查 Skill
│   ├── debug/           调试 Skill
│   ├── test-dev/        测试开发 Skill
│   └── review/          评审 Skill
├── validators/          校验器
│   ├── sop_validator.py SOP 合规校验
│   └── coverage_checker.py 覆盖率检查
├── knowledge/           RAG 知识库
│   ├── test-patterns/   测试模式
│   └── pitfalls/        踩坑经验
├── context_templates/   上下文模板
│   ├── environments.yaml 环境配置
│   └── known-issues.yaml 已知问题
├── sop_dev/             开发 SOP 定义 (10 Phase)
│   └── phases/          Phase 定义文件
└── agents/              Agent 定义 YAML
```

## 快速开始

```python
from alice_governance import (
    get_pack_path,
    get_skills_dev_path,
    get_validators_path,
    get_knowledge_path,
)

# 获取 Skill 路径
pack_path = get_pack_path()
skills_dev_path = get_skills_dev_path()

# 获取校验器路径
validators_path = get_validators_path()

# 获取知识库路径
knowledge_path = get_knowledge_path()
```

## Skill 使用

### 测试 Skill (24 个)

```python
from alice_engine.core.skill_loader import SkillLoader

loader = SkillLoader(governance_path=get_pack_path())
skill = loader.load_skill("test-design/page-analyze")
print(skill.prompt)  # Skill 提示词
```

测试 Skill 列表:

| 类别 | Skill | 说明 |
| ---- | ---- | ---- |
| automation | page-analyze | 页面分析 |
| automation | test-generate | 测试脚本生成 |
| automation | page-object-generator | Page Object 生成 |
| test-design | testcase-design | 测试用例设计 |
| test-design | risk-modeling | 风险建模 |
| execution | allure-report-analyzer | Allure 报告分析 |
| diagnosis | bug-analysis | Bug 分析 |
| knowledge | knowledge-manager | 知识管理 |
| ... | ... | ... |

### 开发 Skill (32 个)

```python
loader = SkillLoader(governance_path=get_skills_dev_path().parent)
skill = loader.load_skill("backend/crud-generator")
```

开发 Skill 列表:

| 类别 | Skill | 说明 |
| ---- | ---- | ---- |
| architecture | project-scanner | 项目扫描 |
| architecture | tech-stack-decider | 技术栈决策 |
| backend | crud-generator | CRUD 生成 |
| backend | fastapi-router-generator | FastAPI 路由生成 |
| frontend | vue-component-generator | Vue 组件生成 |
| code-review | source-code-reviewer | 代码审查 |
| debug | error-locator | 错误定位 |
| test-dev | unit-test-generator | 单元测试生成 |
| ... | ... | ... |

## 校验器

### SOP Validator

```python
from alice_governance.validators.sop_validator import validate_sop_state

result = validate_sop_state(module="equipment")
print(result["violations"])  # 违规列表
print(result["score"])        # 合规分数
```

### Coverage Checker

```python
from alice_governance.validators.coverage_checker import check_coverage

result = check_coverage(module="equipment", page="alarm-config")
print(result["coverage"])  # 覆盖率
```

## 知识库

知识库用于 RAG 检索，提供测试模式和踩坑经验。

```python
from alice_governance import get_knowledge_path

knowledge_path = get_knowledge_path()
# 包含:
# - test-patterns/  测试模式 (CRUD, 搜索过滤, 权限矩阵, 批量操作)
# - pitfalls/       踩坑经验 (Element Plus, Selenium)
```

## 开发 SOP

10 Phase 开发流程:

| Phase | 名称 | Agent |
| ---- | ---- | ---- |
| 01 | Plan | plan-agent |
| 02 | Requirements | requirements-agent |
| 03 | Architecture | architecture-agent |
| 04 | Component Design | component-design-agent |
| 05 | Frontend Implementation | frontend-agent |
| 06 | Backend Implementation | backend-agent |
| 07 | Code Review | code-review-agent |
| 08 | Dev Test | test-dev-agent |
| 09 | Debug & Fix | debug-agent |
| 10 | Build | build-agent |

## Agent 定义

Agent 定义在 `agents/agent-definitions.yaml`:

```yaml
agents:
  project-agent:
    skills:
      - project/project-context-manager
      - project/hygiene-check
    model_tier: balanced

  automation-agent:
    skills:
      - automation/tech-analysis
      - automation/auto-strategy
      - automation/page-object-generator
      - automation/test-script-generator
    model_tier: balanced
```

## License

MIT
