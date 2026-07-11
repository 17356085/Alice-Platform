"""Registry read API — a single discovery surface for Studio.

This endpoint deliberately aggregates existing resource stores.  It does not
introduce a new registry model or modify the execution core.
"""

from fastapi import APIRouter

registry_router = APIRouter(prefix="/api/v1/registry", tags=["registry"])


@registry_router.get("")
async def get_registry_snapshot(org_id: str = ""):
    """Return discoverable Agent, Workflow, Provider, Environment and Plugin resources."""
    from alice_engine.core.executor import AGENT_SKILL_MAP
    from aitest.platform.environment_store import get_environment_store
    from aitest.platform.model_provider_store import get_model_provider_store
    from aitest.platform.plugin import get_plugin_manager
    from aitest.platform.workflow_store import get_workflow_store

    plugin_manager = get_plugin_manager()
    plugin_manager.load_all()

    workflows = get_workflow_store().list_workflows(org_id=org_id or None, limit=100)
    providers = get_model_provider_store().list_providers(org_id=org_id or None)
    environments = get_environment_store().list_environments(org_id=org_id or None)

    agents = [
        {"id": agent_id, "skills": skills}
        for agent_id, skills in AGENT_SKILL_MAP.items()
        if agent_id.endswith("-agent")
    ]
    skills = sorted({skill for agent in agents for skill in agent["skills"]})
    skills.extend(skill for skill in plugin_manager.get_skills() if skill not in skills)

    return {
        "agents": agents,
        "skills": skills,
        "workflows": [workflow.to_dict() for workflow in workflows],
        "providers": [provider.to_dict() for provider in providers],
        "environments": [environment.to_dict() for environment in environments],
        "plugins": plugin_manager.list_plugins(),
    }
