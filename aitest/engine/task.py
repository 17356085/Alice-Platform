"""Re-export from alice_engine.core.task — 保持向后兼容。"""

from alice_engine.core.task import (  # noqa: F401
    ArtifactRule,
    Observation,
    AgentState,
    AgentEventType,
    AgentEvent,
)

# 平台特有: 产物规则 (留在此处)
AUTOMATION_ARTIFACT_RULES = {
    "automation/tech-analysis": [
        ArtifactRule(glob_pattern="{module_dir}/pages/{page}/TECH_ANALYSIS.md", label="TECH_ANALYSIS.md"),
    ],
    "automation/auto-strategy": [
        ArtifactRule(glob_pattern="{module_dir}/pages/{page}/AUTO_STRATEGY.md", label="AUTO_STRATEGY.md"),
    ],
    "automation/page-object-generator": [
        ArtifactRule(glob_pattern="{test_project_root}/page/{module}_page/{PageName}Page.py", label="PageObject 文件"),
        ArtifactRule(glob_pattern="{test_project_root}/page/{module}_page/{PageName}Page.py",
                     check_type="grep_pass", grep_pattern=r"class \w+\(BasePage\):", label="继承 BasePage"),
        ArtifactRule(glob_pattern="{test_project_root}/page/{module}_page/{PageName}Page.py",
                     check_type="grep_pass", grep_pattern=r"//\*\[@id=", grep_should_find=False,
                     label="禁止绝对 XPath", required=False),
        ArtifactRule(glob_pattern="{test_project_root}/page/{module}_page/{PageName}Page.py",
                     check_type="grep_pass", grep_pattern=r"time\.sleep\(", grep_should_find=False,
                     label="禁止 time.sleep"),
        ArtifactRule(glob_pattern="{test_project_root}/page/{module}_page/{PageName}Page.py",
                     check_type="grep_pass", grep_pattern=r"^[^#]*\bprint\(", grep_should_find=False,
                     label="禁止 print 调试"),
    ],
    "automation/test-script-generator": [
        ArtifactRule(glob_pattern="{test_project_root}/script/{module}/test_{page_underscore}.py", label="测试脚本文件"),
        ArtifactRule(glob_pattern="{test_project_root}/script/{module}/test_{page_underscore}.py",
                     check_type="grep_pass", grep_pattern=r"def test_", label="包含 test_ 函数"),
        ArtifactRule(glob_pattern="{test_project_root}/script/{module}/test_{page_underscore}.py",
                     check_type="grep_pass", grep_pattern=r"time\.sleep\(", grep_should_find=False,
                     label="禁止 time.sleep"),
        ArtifactRule(glob_pattern="{test_project_root}/script/{module}/test_{page_underscore}.py",
                     check_type="grep_pass", grep_pattern=r"^[^#]*\bprint\(", grep_should_find=False,
                     label="禁止 print 调试", required=False),
        ArtifactRule(glob_pattern="{test_project_root}/script/{module}/conftest.py",
                     label="conftest.py", required=False),
    ],
    "automation/code-consistency-checker": [],
}

DEV_ARTIFACT_RULES = {
    "architecture/project-scanner": [
        ArtifactRule(glob_pattern="{module_dir}/PROJECT_STRUCTURE.md", label="PROJECT_STRUCTURE.md"),
    ],
    "architecture/tech-stack-decider": [
        ArtifactRule(glob_pattern="{module_dir}/TECH_STACK.md", label="TECH_STACK.md"),
    ],
    "architecture/component-tree-designer": [
        ArtifactRule(glob_pattern="{module_dir}/COMPONENT_TREE.md", label="COMPONENT_TREE.md"),
    ],
    "architecture/api-contract-designer": [
        ArtifactRule(glob_pattern="{module_dir}/API_CONTRACTS.md", label="API_CONTRACTS.md"),
    ],
    "frontend/vue-component-generator": [
        ArtifactRule(glob_pattern="{module_dir}/src/components/{PageName}.vue", label="Vue 组件文件"),
        ArtifactRule(glob_pattern="{module_dir}/src/components/{PageName}.vue",
                     check_type="grep_pass", grep_pattern=r"<script setup lang=\"ts\">",
                     label="Composition API"),
        ArtifactRule(glob_pattern="{module_dir}/src/components/{PageName}.vue",
                     check_type="grep_pass", grep_pattern=r": any", grep_should_find=False,
                     label="禁止 any 类型"),
    ],
    "backend/fastapi-router-generator": [
        ArtifactRule(glob_pattern="{module_dir}/routers/{page}.py", label="FastAPI Router 文件"),
        ArtifactRule(glob_pattern="{module_dir}/routers/{page}.py",
                     check_type="grep_pass", grep_pattern=r"async def", label="async def 端点"),
    ],
    "backend/pydantic-schema-generator": [
        ArtifactRule(glob_pattern="{module_dir}/schemas/{page}.py", label="Pydantic Schema 文件"),
        ArtifactRule(glob_pattern="{module_dir}/schemas/{page}.py",
                     check_type="grep_pass", grep_pattern=r"model_config\s*=", label="Pydantic v2 model_config"),
    ],
    "backend/sqlalchemy-model-generator": [
        ArtifactRule(glob_pattern="{module_dir}/models/{page}.py", label="SQLAlchemy Model 文件"),
        ArtifactRule(glob_pattern="{module_dir}/models/{page}.py",
                     check_type="grep_pass", grep_pattern=r"mapped_column", label="SQLAlchemy 2.0 mapped_column"),
    ],
    "backend/backend-consistency-checker": [],
    "frontend/frontend-lint-checker": [],
}

_ALL_ARTIFACT_RULES = {**AUTOMATION_ARTIFACT_RULES, **DEV_ARTIFACT_RULES}

CODE_REDLINE_CHECKS = [
    ("继承 BasePage", r"class \w+\(BasePage\):", True),
    ("绝对 XPath", r"//\*\[@id=", False),
    ("time.sleep 硬等待", r"time\.sleep\(", False),
    ("print 调试", r"^[^#]*\bprint\(", False),
    ("手动 URL 硬编码", r'get\("https?://', False),
]
