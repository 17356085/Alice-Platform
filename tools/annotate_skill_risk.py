"""
Step 1: Annotate skill-registry.yaml + skill-registry-dev.yaml with risk_level + needs_confirm.

Classification logic:
  low:      read-only analysis, generates docs, no side effects
  medium:   generates code files, interacts with browser, writes to knowledge base
  high:     handles sensitive data, modifies config, generates executable with side effects
  critical: deletes data, executes system commands, manages credentials

needs_confirm: True for high|critical skills that modify state/destroy data.
"""

import yaml
from pathlib import Path
from copy import deepcopy

WORKSTUDY = Path(__file__).resolve().parent.parent
PROD_REGISTRY = WORKSTUDY / "governance" / "skills" / "skill-registry.yaml"
DEV_REGISTRY = WORKSTUDY / "governance" / "skills-dev" / "skill-registry-dev.yaml"

# ── Production Registry Annotations ──
PROD_RISK_MAP = {
    # project
    "project-context-manager": ("low", False),
    "context-sync": ("low", False),
    "hygiene-check": ("low", False),
    # requirements
    "module-modeling": ("low", False),
    "requirement-analysis": ("low", False),
    # test-design
    "page-analysis": ("low", False),
    "page-observe": ("medium", False),       # BrowserUse automation - browser interaction
    "pair-seed": ("low", False),
    "risk-modeling": ("low", False),
    "testcase-design": ("low", False),
    "test-data-generation": ("medium", False),  # generates test data, may contain sensitive patterns
    "api-testing": ("medium", False),         # API calls
    "miniapp-testing": ("medium", False),      # Mini-app interaction
    # automation
    "tech-analysis": ("low", False),
    "auto-strategy": ("low", False),
    "page-object-generator": ("medium", False),  # generates .py code files
    "test-script-generator": ("medium", False),  # generates executable test scripts
    "code-consistency-checker": ("low", False),  # mechanical check, read-only
    # execution
    "allure-report-analyzer": ("low", False),
    "excel-exporter": ("low", False),
    "data-sanitization": ("high", True),         # handles sensitive data, sanitization = data modification risk
    # diagnosis
    "bug-analysis": ("low", False),
    "ci-pipeline-analysis": ("low", False),
    "jenkinsfile-generator": ("medium", False),   # generates CI pipeline config
    # knowledge
    "knowledge-manager": ("medium", False),       # writes to knowledge base, could persist wrong info
    "completeness-check": ("low", False),
    # reporting
    "report-generator": ("low", False),
    # productivity
    "caveman": ("low", False),
}

# ── Dev Registry Annotations ──
DEV_RISK_MAP = {
    # plan
    "plan/create-project-plan": ("low", False),
    "plan/progress-tracker": ("low", False),
    "plan/risk-analyzer": ("low", False),
    "plan/sprint-planner": ("low", False),
    # requirements-dev
    "requirements-dev/feature-spec": ("low", False),
    "requirements-dev/user-story-writer": ("low", False),
    "requirements-dev/acceptance-criteria": ("low", False),
    "requirements-dev/data-model-spec": ("low", False),
    # architecture
    "architecture/project-scanner": ("low", False),
    "architecture/tech-stack-decider": ("low", False),
    "architecture/component-tree-designer": ("low", False),
    "architecture/api-contract-designer": ("low", False),
    # component-design
    "component-design/component-spec": ("low", False),
    "component-design/props-interface": ("low", False),
    "component-design/data-flow": ("low", False),
    "component-design/layout-mockup": ("low", False),
    # frontend
    "frontend/vue-component-generator": ("medium", False),  # generates Vue components
    "frontend/page-implementer": ("medium", False),         # generates pages
    "frontend/vuex-pinia-store": ("medium", False),         # generates state management
    "frontend/router-config": ("medium", False),            # generates router config
    "frontend/frontend-lint-checker": ("low", False),
    # backend
    "backend/fastapi-router-generator": ("medium", False),  # generates API code
    "backend/pydantic-schema-generator": ("medium", False), # generates schema
    "backend/sqlalchemy-model-generator": ("medium", False),# generates DB model
    "backend/crud-generator": ("high", True),               # CRUD operations could affect data
    "backend/unit-test-generator": ("medium", False),
    "backend/backend-consistency-checker": ("low", False),
    # code-review
    "code-review/source-code-reviewer": ("low", False),
    "code-review/performance-analyzer": ("low", False),
    "code-review/security-scanner": ("medium", False),      # security scanning, read-only analysis
    "code-review/consistency-enforcer": ("low", False),
    # test-dev
    "test-dev/unit-test-generator": ("medium", False),
    "test-dev/integration-test-generator": ("medium", False),
    "test-dev/coverage-checker": ("low", False),
    # debug
    "debug/error-locator": ("low", False),
    "debug/stack-trace-analyzer": ("low", False),
    "debug/fix-suggester": ("low", False),
    "debug/regression-verifier": ("low", False),
    # build
    "build/type-checker": ("low", False),
    "build/lint-executor": ("low", False),
    "build/test-runner": ("high", True),                   # executes tests - could affect system
    "build/package-bundler": ("medium", False),
    # review (P0 + P1 meta-governance)
    "review/architecture-assessment": ("low", False),
    "review/token-efficiency": ("low", False),
    "review/governance-coverage": ("low", False),
    "review/prompt-engineering": ("low", False),
    "review/production-readiness": ("low", False),
    "review/tech-debt-inventory": ("low", False),
    "review/component-cohesion": ("low", False),
    "review/quality-regression-analysis": ("low", False),
    "review/sop-effectiveness": ("low", False),
    "review/model-selection": ("low", False),
    "review/observability-gap": ("low", False),
    "review/security-posture": ("low", False),
    "review/skill-health": ("low", False),
    "review/agent-health": ("low", False),
    "review/memory-quality": ("low", False),
    # automation (PE Expert)
    "automation/prompt-engineering-expert": ("high", True), # actively modifies skill prompts - production impact
}


def annotate_prod_registry():
    """Annotate production registry (list format)."""
    with open(PROD_REGISTRY, "r", encoding="utf-8") as f:
        content = f.read()

    data = yaml.safe_load(content)
    skills = data.get("skills", [])

    annotated = 0
    for skill in skills:
        sid = skill.get("id", "")
        if sid in PROD_RISK_MAP:
            risk_level, needs_confirm = PROD_RISK_MAP[sid]
        else:
            risk_level, needs_confirm = "low", False

        skill["risk_level"] = risk_level
        skill["needs_confirm"] = needs_confirm
        annotated += 1

    # Write with explicit YAML formatting
    output = yaml.dump(data, allow_unicode=True, default_flow_style=False,
                       sort_keys=False, width=120)
    with open(PROD_REGISTRY, "w", encoding="utf-8") as f:
        f.write(output)

    return annotated


def annotate_dev_registry():
    """Annotate dev registry (dict/nested-key format)."""
    with open(DEV_REGISTRY, "r", encoding="utf-8") as f:
        content = f.read()

    data = yaml.safe_load(content)
    skills = data.get("skills", {})

    annotated = 0
    for sid, skill in skills.items():
        if sid in DEV_RISK_MAP:
            risk_level, needs_confirm = DEV_RISK_MAP[sid]
        else:
            risk_level, needs_confirm = "low", False

        skill["risk_level"] = risk_level
        skill["needs_confirm"] = needs_confirm
        annotated += 1

    output = yaml.dump(data, allow_unicode=True, default_flow_style=False,
                       sort_keys=False, width=120)
    with open(DEV_REGISTRY, "w", encoding="utf-8") as f:
        f.write(output)

    return annotated


if __name__ == "__main__":
    prod_count = annotate_prod_registry()
    dev_count = annotate_dev_registry()
    print(f"Annotated: production={prod_count} skills, dev={dev_count} skills")

    # Verify
    prod = yaml.safe_load(open(PROD_REGISTRY, "r", encoding="utf-8"))
    dev = yaml.safe_load(open(DEV_REGISTRY, "r", encoding="utf-8"))

    prod_stats = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    for s in prod.get("skills", []):
        rl = s.get("risk_level", "low")
        prod_stats[rl] = prod_stats.get(rl, 0) + 1
    print(f"Production dist: {prod_stats}")

    dev_stats = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    for sid, s in dev.get("skills", {}).items():
        rl = s.get("risk_level", "low")
        dev_stats[rl] = dev_stats.get(rl, 0) + 1
    print(f"Dev dist: {dev_stats}")

    # Verify risk_level present on all
    for s in prod.get("skills", []):
        if "risk_level" not in s:
            print(f"MISSING: {s.get('id')}")
    for sid, s in dev.get("skills", {}).items():
        if "risk_level" not in s:
            print(f"MISSING: {sid}")
    print("All skills annotated.")
