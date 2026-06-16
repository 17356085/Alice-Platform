"""
Skill Loader — 从 governance/skills/ 加载 Skill Markdown Prompt。

P1-3: 新增 Prompt 变体支持（variant-aware 加载 + PromptVariant + A/B 准备）
P0-1 (2026-06-15): Prompt Versioning — @version 语法 + registry 版本解析

用法:
    from aitest.llm.skill_loader import load_skill, list_skills, list_variants, get_skill_version
    prompt = load_skill("test-design/page-analysis")            # 加载 current_version
    prompt = load_skill("test-design/page-analysis@v1.0")       # 加载指定版本
    prompt_v2 = load_skill("test-design/page-analysis", variant="page-analysis-v2")
    version_info = get_skill_version("test-design/page-analysis")  # 获取版本元数据
    skills = list_skills("automation")
    vars = list_variants("test-design/page-analysis")
"""
import functools
from pathlib import Path
from dataclasses import dataclass

# ── 路径配置 ──
WORKSTUDY = Path(__file__).resolve().parent.parent.parent
GOVERNANCE = WORKSTUDY / "governance"
SKILLS_DIR = GOVERNANCE / "skills"
SKILLS_DEV_DIR = GOVERNANCE / "skills-dev"  # 开发技能目录
SKILL_REGISTRY_FILE = SKILLS_DIR / "skill-registry.yaml"
SKILL_REGISTRY_DEV_FILE = SKILLS_DEV_DIR / "skill-registry-dev.yaml"  # 开发技能注册表


@dataclass
class PromptVariant:
    """Skill Prompt 的一个变体。"""
    variant_id: str       # "page-analysis-v2"
    skill_id: str         # "test-design/page-analysis"
    version: str          # "2.0-exp"
    content: str = ""     # 懒加载时为空，load_variant() 时填充
    tags: list = None     # ["experimental", "shorter"]
    description: str = ""

    def __post_init__(self):
        if self.tags is None:
            self.tags = []

    def to_dict(self) -> dict:
        return {
            "variant_id": self.variant_id,
            "skill_id": self.skill_id,
            "version": self.version,
            "tags": self.tags,
            "description": self.description,
        }


@dataclass
class SkillVersionInfo:
    """Skill 版本元数据。"""
    skill_id: str          # "test-design/page-analysis"
    resolved_version: str  # "1.0" (实际加载的版本)
    current_version: str   # "1.0" (registry 中标记的 current)
    file_path: str         # 实际加载的文件路径
    changelog: str = ""    # 版本 changelog
    released: str = ""     # 发布日期


@functools.lru_cache(maxsize=64)
def _load_skill_cached(skill_id: str, variant: str = "", version: str = "") -> str:
    """
    P0-4: load_skill 的缓存版本。variant/version 默认 '' 以确保缓存键可哈希。
    P0-1: version 参数支持 @version 语法。

    异常:
        FileNotFoundError: Skill 文件不存在
        ValueError: 变体 ID 未注册 或 版本未找到
    """
    # 变体优先
    if variant:
        return load_variant(skill_id, variant)

    # P0-1: 版本解析 — 查找 registry 中匹配版本的 file 路径
    if version:
        version_file = _resolve_version_file(skill_id, version)
        if version_file:
            return version_file.read_text(encoding="utf-8")

    # 尝试格式1: "category/skill-name" → governance/skills/category/skill-name.md
    skill_path = SKILLS_DIR / f"{skill_id}.md"
    if skill_path.exists():
        return skill_path.read_text(encoding="utf-8")

    # 尝试格式1b: 开发技能 → governance/skills-dev/category/skill-name.md
    skill_dev_path = SKILLS_DEV_DIR / f"{skill_id}.md"
    if skill_dev_path.exists():
        return skill_dev_path.read_text(encoding="utf-8")

    # 尝试格式2: 在 skill-registry.yaml 中查找
    registry = _load_registry()
    for s in registry.get("skills", []):
        s_id = s.get("id", "")
        # 匹配完整 ID 或尾部名称
        if s_id == skill_id or s_id.split("/")[-1] == skill_id.split("/")[-1]:
            skill_path = GOVERNANCE / s.get("file", "")
            if skill_path.exists():
                return skill_path.read_text(encoding="utf-8")
            break

    # 尝试格式2b: 在 skill-registry-dev.yaml 中查找
    if SKILL_REGISTRY_DEV_FILE.exists():
        import yaml as _yaml
        with open(SKILL_REGISTRY_DEV_FILE, "r", encoding="utf-8") as f:
            dev_registry = _yaml.safe_load(f)
        for s in dev_registry.get("skills", {}).values():
            if s.get("id") == skill_id:
                # P0-1: dev registry 也支持版本
                if version:
                    version_file = _resolve_dev_version_file(s, version)
                    if version_file:
                        return version_file.read_text(encoding="utf-8")
                dev_skill_path = GOVERNANCE / s.get("file", "")
                if dev_skill_path.exists():
                    return dev_skill_path.read_text(encoding="utf-8")
                break

    raise FileNotFoundError(
        f"Skill not found: '{skill_id}'. "
        f"Searched: {skill_path}\n"
        f"Available categories: {list_categories()}\n"
        f"Use list_skills() to see all skills."
    )


def _resolve_version_file(skill_id: str, version: str) -> Path | None:
    """P0-1: 从测试 skill registry 解析指定版本的文件路径。"""
    registry = _load_registry()
    for s in registry.get("skills", []):
        s_id = s.get("id", "")
        if s_id == skill_id or s_id.split("/")[-1] == skill_id.split("/")[-1]:
            for v in s.get("versions", []):
                if v.get("version") == version:
                    vf = GOVERNANCE / v.get("file", "")
                    if vf.exists():
                        return vf
            # 版本未找到：如果只有一个版本且 current_version 匹配，回退到主文件
            if s.get("current_version") == version:
                fallback = GOVERNANCE / s.get("file", "")
                if fallback.exists():
                    return fallback
            break
    return None


def _resolve_dev_version_file(skill_def: dict, version: str) -> Path | None:
    """P0-1: 从开发 skill registry 解析指定版本的文件路径。"""
    for v in skill_def.get("versions", []):
        if v.get("version") == version:
            vf = GOVERNANCE / v.get("file", "")
            if vf.exists():
                return vf
    if skill_def.get("current_version") == version:
        fallback = GOVERNANCE / skill_def.get("file", "")
        if fallback.exists():
            return fallback
    return None


def load_skill(skill_id: str, variant: str = None, version: str = None) -> str:
    """
    根据 Skill ID 加载 Skill Prompt 内容（P0-4: 委托给缓存内部函数）。

    参数:
        skill_id: Skill 标识符。
                  格式1（推荐）: "category/skill-name" 如 "test-design/page-analysis"
                  格式2（兼容）: "skill-name" 如 "page-analysis"（在 skill-registry.yaml 中查找）
                  P0-1 格式3: "category/skill-name@v1.0" 加载指定版本
        variant:  可选变体 ID。指定后加载变体文件而非默认版本。
                  变体必须在 skill-registry.yaml 的 variants 区块中注册。
        version:  P0-1 可选版本号。指定后加载该版本的 Prompt 文件。
                  优先级: variant > version > @syntax > current_version

    返回:
        Skill Markdown 文件的完整内容

    异常:
        FileNotFoundError: Skill 文件不存在
        ValueError: 变体 ID 未注册 或 版本未找到
    """
    # P0-1: 解析 @version 语法
    resolved_version = version or ""
    if "@" in skill_id and "/" in skill_id:
        base_id, _, ver = skill_id.partition("@")
        if ver and not resolved_version:
            resolved_version = ver
            skill_id = base_id

    return _load_skill_cached(skill_id, variant or "", resolved_version)


def list_skills(category: str = None) -> list[dict]:
    """
    列出所有可用 Skill。

    参数:
        category: 按分类筛选（如 "automation", "test-design"）。留空返回全部。

    返回:
        [{"id": "test-design/page-analysis", "category": "test-design", "status": "active"}, ...]
    """
    registry = _load_registry()
    skills = []

    for s in registry.get("skills", []):
        cat = s.get("category", "unknown")
        if category and cat != category:
            continue
        if s.get("status") == "deprecated":
            continue
        skills.append({
            "id": s.get("id", ""),
            "category": cat,
            "status": s.get("status", "active"),
            "file": s.get("file", ""),
        })

    return skills


def list_categories() -> list[str]:
    """列出所有 Skill 分类。"""
    registry = _load_registry()
    categories = set()
    for s in registry.get("skills", []):
        cat = s.get("category", "")
        if cat and cat != "deprecated":
            categories.add(cat)
    return sorted(categories)


def get_skill_metadata(skill_id: str) -> dict:
    """获取 Skill 的注册表元数据。"""
    registry = _load_registry()
    for s in registry.get("skills", []):
        if s.get("id") == skill_id or s.get("id") == skill_id.split("/")[-1]:
            return {
                "id": s.get("id", ""),
                "category": s.get("category", ""),
                "status": s.get("status", ""),
                "file": s.get("file", ""),
                "workflows": s.get("workflows", []),
                "note": s.get("note", ""),
            }
    return {}


@functools.lru_cache(maxsize=1)
def _load_registry() -> dict:
    """加载 skill-registry.yaml（P0-4: 结果缓存，会话内不变）。"""
    import yaml
    if not SKILL_REGISTRY_FILE.exists():
        return {"skills": [], "variants": []}
    with open(SKILL_REGISTRY_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ══════════════════════════════════════════════════════════════════════════
#  P0-1: Skill 版本查询
# ══════════════════════════════════════════════════════════════════════════

def get_skill_version(skill_id: str) -> SkillVersionInfo | None:
    """
    P0-1: 获取 Skill 的版本元数据。

    参数:
        skill_id: Skill ID (支持 "category/name" 或 "name" 格式)

    返回:
        SkillVersionInfo 或 None（未找到时）
    """
    # 解析 @version 语法
    clean_id = skill_id
    if "@" in skill_id:
        clean_id, _, _ = skill_id.partition("@")

    registry = _load_registry()
    for s in registry.get("skills", []):
        s_id = s.get("id", "")
        if s_id == clean_id or s_id.split("/")[-1] == clean_id.split("/")[-1]:
            versions = s.get("versions", [])
            current = s.get("current_version", "?")
            # 找到 current_version 对应的版本详情
            for v in versions:
                if v.get("version") == current:
                    return SkillVersionInfo(
                        skill_id=s_id,
                        resolved_version=current,
                        current_version=current,
                        file_path=s.get("file", ""),
                        changelog=v.get("changelog", ""),
                        released=v.get("released", ""),
                    )
            # 有 current_version 但 versions[] 中没有详情
            return SkillVersionInfo(
                skill_id=s_id,
                resolved_version=current,
                current_version=current,
                file_path=s.get("file", ""),
            )

    # Dev registry
    if SKILL_REGISTRY_DEV_FILE.exists():
        import yaml as _yaml
        with open(SKILL_REGISTRY_DEV_FILE, "r", encoding="utf-8") as f:
            dev_registry = _yaml.safe_load(f)
        for s in dev_registry.get("skills", {}).values():
            if s.get("id") == clean_id:
                versions = s.get("versions", [])
                current = s.get("current_version", "?")
                for v in versions:
                    if v.get("version") == current:
                        return SkillVersionInfo(
                            skill_id=s.get("id", clean_id),
                            resolved_version=current,
                            current_version=current,
                            file_path=s.get("file", ""),
                            changelog=v.get("changelog", ""),
                            released=v.get("released", ""),
                        )
                return SkillVersionInfo(
                    skill_id=s.get("id", clean_id),
                    resolved_version=current,
                    current_version=current,
                    file_path=s.get("file", ""),
                )

    return None


def resolve_skill_version(skill_id: str, requested_version: str = None) -> SkillVersionInfo:
    """
    P0-1: 解析 Skill 加载时将使用的实际版本。

    优先级: requested_version > @syntax > current_version

    返回:
        SkillVersionInfo (如果找不到匹配版本，返回 current_version 的 info)
    """
    clean_id = skill_id
    ver = requested_version
    if "@" in skill_id:
        clean_id, _, v = skill_id.partition("@")
        if v and not ver:
            ver = v

    info = get_skill_version(clean_id)
    if info is None:
        # 未注册的 skill — 返回默认信息
        return SkillVersionInfo(
            skill_id=clean_id,
            resolved_version=ver or "?",
            current_version="?",
            file_path=f"skills/{clean_id}.md",
        )

    if ver:
        # 验证请求的版本是否存在
        registry = _load_registry()
        for s in registry.get("skills", []):
            if s.get("id") == clean_id or s.get("id", "").split("/")[-1] == clean_id.split("/")[-1]:
                for v in s.get("versions", []):
                    if v.get("version") == ver:
                        info.resolved_version = ver
                        info.file_path = v.get("file", info.file_path)
                        info.changelog = v.get("changelog", "")
                        info.released = v.get("released", "")
                        return info
                break

    return info


# ══════════════════════════════════════════════════════════════════════════
#  P1-3: Prompt 变体支持
# ══════════════════════════════════════════════════════════════════════════

def load_variant(skill_id: str, variant_id: str) -> str:
    """
    加载指定 Skill 的指定变体 Prompt 内容。

    参数:
        skill_id:   Skill ID (e.g. "test-design/page-analysis")
        variant_id: 变体 ID (e.g. "page-analysis-v2")

    返回:
        变体 Prompt 文件的完整内容

    异常:
        ValueError: 变体未在 registry 中注册
        FileNotFoundError: 变体文件不存在
    """
    registry = _load_registry()
    variants = registry.get("variants", [])

    for v in variants:
        if v.get("id") == variant_id and v.get("skill_id") == skill_id:
            variant_path = GOVERNANCE / v["file"]
            if not variant_path.exists():
                raise FileNotFoundError(
                    f"Variant file not found: {variant_path}\n"
                    f"Variant '{variant_id}' for skill '{skill_id}' is registered but file is missing."
                )
            return variant_path.read_text(encoding="utf-8")

    # 也尝试不带 skill_id 前缀的匹配
    for v in variants:
        if v.get("id") == variant_id:
            variant_path = GOVERNANCE / v["file"]
            if variant_path.exists():
                return variant_path.read_text(encoding="utf-8")

    raise ValueError(
        f"Variant '{variant_id}' not found for skill '{skill_id}'.\n"
        f"Use list_variants('{skill_id}') to see available variants."
    )


def list_variants(skill_id: str = None) -> list[PromptVariant]:
    """
    列出可用的 Prompt 变体。

    参数:
        skill_id: 按 Skill ID 筛选（None = 全部）

    返回:
        PromptVariant 列表（content 字段为空，需要调用 load_variant() 加载）
    """
    registry = _load_registry()
    result = []

    variants = registry.get("variants") or []
    for v in variants:
        vid = v.get("id", "")
        sid = v.get("skill_id", "")
        if skill_id and sid != skill_id:
            continue
        result.append(PromptVariant(
            variant_id=vid,
            skill_id=sid,
            version=v.get("version", "?"),
            tags=v.get("tags", []),
            description=v.get("description", ""),
        ))

    return result
