"""Re-export from alice_engine.core.skill_loader — 保持向后兼容。"""

from alice_engine.core.skill_loader import (  # noqa: F401
    SkillLoader,
    PromptVariant,
    SkillVersionInfo,
)

# 兼容旧接口: load_skill() 函数
_default_loader = None

def load_skill(skill_id: str, variant: str = None, version: str = None) -> str:
    """兼容旧接口。"""
    global _default_loader
    if _default_loader is None:
        from aitest.runtime.paths import get_workstudy
        _default_loader = SkillLoader(governance_path=get_workstudy() / "governance")
    return _default_loader.load(skill_id, variant=variant, version=version)

def list_skills(category: str = None) -> list:
    global _default_loader
    if _default_loader is None:
        from aitest.runtime.paths import get_workstudy
        _default_loader = SkillLoader(governance_path=get_workstudy() / "governance")
    return _default_loader.list_skills(category)

def list_categories() -> list:
    global _default_loader
    if _default_loader is None:
        from aitest.runtime.paths import get_workstudy
        _default_loader = SkillLoader(governance_path=get_workstudy() / "governance")
    return _default_loader.list_categories()

def get_skill_metadata(skill_id: str) -> dict:
    global _default_loader
    if _default_loader is None:
        from aitest.runtime.paths import get_workstudy
        _default_loader = SkillLoader(governance_path=get_workstudy() / "governance")
    return _default_loader.get_skill_metadata(skill_id)

def get_skill_version(skill_id: str):
    global _default_loader
    if _default_loader is None:
        from aitest.runtime.paths import get_workstudy
        _default_loader = SkillLoader(governance_path=get_workstudy() / "governance")
    return _default_loader.get_skill_version(skill_id)

def resolve_skill_version(skill_id: str, requested_version: str = None):
    global _default_loader
    if _default_loader is None:
        from aitest.runtime.paths import get_workstudy
        _default_loader = SkillLoader(governance_path=get_workstudy() / "governance")
    return _default_loader.get_skill_version(skill_id)

def list_variants(skill_id: str = None) -> list:
    global _default_loader
    if _default_loader is None:
        from aitest.runtime.paths import get_workstudy
        _default_loader = SkillLoader(governance_path=get_workstudy() / "governance")
    return _default_loader.list_variants(skill_id)

def load_variant(skill_id: str, variant_id: str) -> str:
    global _default_loader
    if _default_loader is None:
        from aitest.runtime.paths import get_workstudy
        _default_loader = SkillLoader(governance_path=get_workstudy() / "governance")
    return _default_loader._load_variant(skill_id, variant_id)
