"""Agent 定义加载 — 从 YAML 加载 Agent → Skill 映射。

解耦: governance_path 通过参数传入。

用法:
    from alice_engine.core.agent_definitions import AgentDefinitions

    defs = AgentDefinitions(governance_path="./governance")
    skills = defs.get_skills("automation-agent")
    agent_def = defs.get_definition("automation-agent")
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# 内置 fallback 映射
FALLBACK_AGENT_SKILL_MAP = {
    "project-agent": [
        "project/project-context-manager", "project/context-sync",
        "project/hygiene-check", "knowledge/completeness-check",
    ],
    "requirement-agent": [
        "requirements/module-modeling", "requirements/requirement-analysis",
    ],
    "test-design-agent": [
        "test-design/page-analysis", "test-design/risk-modeling", "test-design/testcase-design",
    ],
    "automation-agent": [
        "automation/tech-analysis", "automation/auto-strategy",
        "automation/page-object-generator", "automation/test-script-generator",
        "automation/code-consistency-checker",
    ],
    "execution-agent": [
        "execution/allure-report-analyzer",
    ],
    "bug-analysis-agent": [
        "diagnosis/bug-analysis",
    ],
    "report-agent": [
        "reporting/report-generator",
    ],
    "knowledge-agent": [
        "knowledge/knowledge-manager",
    ],
}


class AgentDefinitions:
    """Agent 定义管理器。

    用法:
        defs = AgentDefinitions(governance_path="./governance")
        skills = defs.get_skills("automation-agent")
    """

    def __init__(self, governance_path: str | Path):
        self.governance = Path(governance_path)
        self._cache: dict | None = None
        self._skill_map_cache: dict | None = None

    def get_skills(self, agent_name: str) -> list[str]:
        """获取 Agent 的 Skill 列表。"""
        skill_map = self._load_skill_map()
        return skill_map.get(agent_name, [])

    def get_definition(self, agent_name: str) -> dict:
        """获取 Agent 的完整定义。"""
        definitions = self._load_definitions()
        return definitions.get(agent_name, {})

    def list_agents(self) -> list[str]:
        """列出所有 Agent 名称。"""
        skill_map = self._load_skill_map()
        return sorted(skill_map.keys())

    def get_model_tier(self, agent_name: str) -> str:
        """获取 Agent 的模型层级。"""
        definition = self.get_definition(agent_name)
        return definition.get("model_tier", "balanced")

    def _load_skill_map(self) -> dict:
        """加载 Agent → Skill 映射。"""
        if self._skill_map_cache is not None:
            return self._skill_map_cache

        yaml_path = self.governance / "agents" / "agent-definitions.yaml"
        if not yaml_path.exists():
            self._skill_map_cache = FALLBACK_AGENT_SKILL_MAP.copy()
            return self._skill_map_cache

        try:
            import yaml
            with open(yaml_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            agents = data.get("agents", {})
            result = {}
            for agent_id, defn in agents.items():
                if defn.get("is_orchestrator"):
                    continue
                skills = defn.get("skills", [])
                if skills:
                    result[agent_id] = skills
            self._skill_map_cache = result
        except Exception as e:
            logger.warning("Failed to load agent definitions: %s", e)
            self._skill_map_cache = FALLBACK_AGENT_SKILL_MAP.copy()

        return self._skill_map_cache

    def _load_definitions(self) -> dict:
        """加载完整 Agent 定义。"""
        if self._cache is not None:
            return self._cache

        yaml_path = self.governance / "agents" / "agent-definitions.yaml"
        if not yaml_path.exists():
            self._cache = {}
            return self._cache

        try:
            import yaml
            with open(yaml_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            self._cache = data.get("agents", {})
        except Exception as e:
            logger.warning("Failed to load agent definitions: %s", e)
            self._cache = {}

        return self._cache
