"""Re-export from alice_engine.core.skill_loader — 保持向后兼容。"""

from alice_engine.core.skill_loader import (  # noqa: F401
    SkillLoader,
    PromptVariant,
    SkillVersionInfo,
)

# 兼容旧接口
_default_loader = None

def load_skill(skill_id: str, variant: str = None, version: str = None) -> str:
    global _default_loader
    if _default_loader is None:
        from aitest.runtime.paths import get_workstudy
        _default_loader = SkillLoader(governance_path=get_workstudy() / "governance")
    return _default_loader.load(skill_id, variant=variant, version=version)

def resolve_skill_version(skill_id: str, requested_version: str = None):
    global _default_loader
    if _default_loader is None:
        from aitest.runtime.paths import get_workstudy
        _default_loader = SkillLoader(governance_path=get_workstudy() / "governance")
    return _default_loader.get_skill_version(skill_id)
