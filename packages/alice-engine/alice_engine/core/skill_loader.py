"""Skill Loader — 从 governance/skills/ 加载 Skill Markdown Prompt。

解耦: governance_path 通过参数传入，不再依赖平台路径模块。

用法:
    from alice_engine.core.skill_loader import SkillLoader

    loader = SkillLoader(governance_path=project.governance_path)
    prompt = loader.load("test-design/page-analysis")
    prompt = loader.load("test-design/page-analysis@v1.0")
"""
import functools
from pathlib import Path
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class PromptVariant:
    """Skill Prompt 的一个变体。"""
    variant_id: str       # "page-analysis-v2"
    skill_id: str         # "test-design/page-analysis"
    version: str          # "2.0-exp"
    content: str = ""
    tags: list = None
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
    skill_id: str
    resolved_version: str
    current_version: str
    file_path: str
    changelog: str = ""
    released: str = ""


class SkillLoader:
    """Skill 加载器 — 从 governance 目录加载 Skill Prompt。

    用法:
        loader = SkillLoader(governance_path="./governance")
        prompt = loader.load("test-design/page-analysis")
        skills = loader.list_skills("automation")
    """

    def __init__(self, governance_path: str | Path):
        self.governance = Path(governance_path)
        self.skills_dir = self.governance / "skills"
        self.skills_dev_dir = self.governance / "skills-dev"
        self._registry_cache: dict | None = None

    def load(self, skill_id: str, variant: str = None, version: str = None) -> str:
        """加载 Skill Prompt 内容。

        Args:
            skill_id: Skill ID (如 "test-design/page-analysis" 或 "test-design/page-analysis@v1.0")
            variant: 可选变体 ID
            version: 可选版本号

        Returns:
            Skill Markdown 内容

        Raises:
            FileNotFoundError: Skill 文件不存在
        """
        # 解析 @version 语法
        resolved_version = version or ""
        if "@" in skill_id and "/" in skill_id:
            base_id, _, ver = skill_id.partition("@")
            if ver and not resolved_version:
                resolved_version = ver
                skill_id = base_id

        # 变体优先
        if variant:
            return self._load_variant(skill_id, variant)

        # 版本解析
        if resolved_version:
            version_file = self._resolve_version_file(skill_id, resolved_version)
            if version_file:
                return version_file.read_text(encoding="utf-8")

        # 格式1: "category/skill-name" → governance/skills/category/skill-name.md
        skill_path = self.skills_dir / f"{skill_id}.md"
        if skill_path.exists():
            return skill_path.read_text(encoding="utf-8")

        # 格式1b: 开发技能
        skill_dev_path = self.skills_dev_dir / f"{skill_id}.md"
        if skill_dev_path.exists():
            return skill_dev_path.read_text(encoding="utf-8")

        # 格式2: 在 registry 中查找
        registry = self._load_registry()
        for s in registry.get("skills", []):
            s_id = s.get("id", "")
            if s_id == skill_id or s_id.split("/")[-1] == skill_id.split("/")[-1]:
                skill_path = self.governance / s.get("file", "")
                if skill_path.exists():
                    return skill_path.read_text(encoding="utf-8")
                break

        # Dev registry
        dev_registry_file = self.skills_dev_dir / "skill-registry-dev.yaml"
        if dev_registry_file.exists():
            import yaml
            with open(dev_registry_file, "r", encoding="utf-8") as f:
                dev_registry = yaml.safe_load(f)
            for s in dev_registry.get("skills", {}).values():
                if s.get("id") == skill_id:
                    if resolved_version:
                        version_file = self._resolve_dev_version_file(s, resolved_version)
                        if version_file:
                            return version_file.read_text(encoding="utf-8")
                    dev_skill_path = self.governance / s.get("file", "")
                    if dev_skill_path.exists():
                        return dev_skill_path.read_text(encoding="utf-8")
                    break

        raise FileNotFoundError(
            f"Skill not found: '{skill_id}'. "
            f"Searched: {skill_path}\n"
            f"Available categories: {self.list_categories()}"
        )

    def list_skills(self, category: str = None) -> list[dict]:
        """列出可用 Skill。"""
        registry = self._load_registry()
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

    def list_categories(self) -> list[str]:
        """列出所有 Skill 分类。"""
        registry = self._load_registry()
        categories = set()
        for s in registry.get("skills", []):
            cat = s.get("category", "")
            if cat and cat != "deprecated":
                categories.add(cat)
        return sorted(categories)

    def get_skill_metadata(self, skill_id: str) -> dict:
        """获取 Skill 的注册表元数据。"""
        registry = self._load_registry()
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

    def get_skill_version(self, skill_id: str) -> SkillVersionInfo | None:
        """获取 Skill 的版本元数据。"""
        clean_id = skill_id
        if "@" in skill_id:
            clean_id, _, _ = skill_id.partition("@")

        registry = self._load_registry()
        for s in registry.get("skills", []):
            s_id = s.get("id", "")
            if s_id == clean_id or s_id.split("/")[-1] == clean_id.split("/")[-1]:
                versions = s.get("versions", [])
                current = s.get("current_version", "?")
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
                return SkillVersionInfo(
                    skill_id=s_id,
                    resolved_version=current,
                    current_version=current,
                    file_path=s.get("file", ""),
                )

        # Dev registry
        dev_registry_file = self.skills_dev_dir / "skill-registry-dev.yaml"
        if dev_registry_file.exists():
            import yaml
            with open(dev_registry_file, "r", encoding="utf-8") as f:
                dev_registry = yaml.safe_load(f)
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

    def list_variants(self, skill_id: str = None) -> list[PromptVariant]:
        """列出可用的 Prompt 变体。"""
        registry = self._load_registry()
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

    def _load_registry(self) -> dict:
        """加载 skill-registry.yaml。"""
        if self._registry_cache is not None:
            return self._registry_cache

        import yaml
        registry_file = self.skills_dir / "skill-registry.yaml"
        if not registry_file.exists():
            self._registry_cache = {"skills": [], "variants": []}
        else:
            with open(registry_file, "r", encoding="utf-8") as f:
                self._registry_cache = yaml.safe_load(f) or {"skills": [], "variants": []}

        return self._registry_cache

    # ── Contract 校验 ──────────────────────────────────────────────

    def get_contract(self, skill_id: str) -> dict | None:
        """获取 skill 的 contract 定义。"""
        registry = self._load_registry()
        for s in registry.get("skills", []):
            s_id = s.get("id", "")
            if s_id == skill_id or s_id.split("/")[-1] == skill_id.split("/")[-1]:
                return s.get("contract")
        return None

    def get_stability(self, skill_id: str) -> str:
        """获取 skill 的 stability 级别。

        Returns:
            "system" | "core" | "extended" | "experimental"
            未定义则默认 "extended"。
        """
        contract = self.get_contract(skill_id)
        if contract:
            return contract.get("stability", "extended")
        return "extended"

    def validate_contracts(self) -> list[dict]:
        """校验所有 core/system skill 是否可加载。

        Returns:
            问题列表。每项: {"skill_id": str, "stability": str, "issue": str}
        """
        issues = []
        registry = self._load_registry()

        for s in registry.get("skills", []):
            s_id = s.get("id", "")
            if not s_id:
                continue

            # 跳过 deprecated
            if s.get("status") == "deprecated":
                continue

            contract = s.get("contract", {})
            stability = contract.get("stability", "extended")

            # 只检查 system 和 core
            if stability not in ("system", "core"):
                continue

            # 检查 skill 文件是否存在
            skill_file = s.get("file", "")
            if skill_file:
                full_path = self.governance / skill_file
                if not full_path.exists():
                    issues.append({
                        "skill_id": s_id,
                        "stability": stability,
                        "issue": f"skill file not found: {skill_file}",
                    })

        return issues

    def enforce_contracts(self) -> None:
        """强制执行 contract 校验。

        system 级缺失 → raise RuntimeError
        core 级缺失 → raise RuntimeError
        extended 级缺失 → log warning
        experimental 级 → ignore
        """
        import logging
        logger = logging.getLogger(__name__)

        registry = self._load_registry()

        for s in registry.get("skills", []):
            s_id = s.get("id", "")
            if not s_id or s.get("status") == "deprecated":
                continue

            contract = s.get("contract", {})
            stability = contract.get("stability", "extended")
            skill_file = s.get("file", "")

            if not skill_file:
                continue

            full_path = self.governance / skill_file
            exists = full_path.exists()

            if stability == "system" and not exists:
                raise RuntimeError(
                    f"[CONTRACT] System skill missing: {s_id} ({skill_file}). "
                    f"SDK cannot function without this skill."
                )
            elif stability == "core" and not exists:
                raise RuntimeError(
                    f"[CONTRACT] Core skill missing: {s_id} ({skill_file}). "
                    f"Install alice-governance for full capability."
                )
            elif stability == "extended" and not exists:
                logger.warning(
                    "[CONTRACT] Extended skill missing: %s (%s). "
                    "Some features may be unavailable.", s_id, skill_file
                )
            # experimental → ignore

    def _resolve_version_file(self, skill_id: str, version: str) -> Path | None:
        """从 registry 解析指定版本的文件路径。"""
        registry = self._load_registry()
        for s in registry.get("skills", []):
            s_id = s.get("id", "")
            if s_id == skill_id or s_id.split("/")[-1] == skill_id.split("/")[-1]:
                for v in s.get("versions", []):
                    if v.get("version") == version:
                        vf = self.governance / v.get("file", "")
                        if vf.exists():
                            return vf
                if s.get("current_version") == version:
                    fallback = self.governance / s.get("file", "")
                    if fallback.exists():
                        return fallback
                break
        return None

    def _resolve_dev_version_file(self, skill_def: dict, version: str) -> Path | None:
        """从开发 skill registry 解析指定版本的文件路径。"""
        for v in skill_def.get("versions", []):
            if v.get("version") == version:
                vf = self.governance / v.get("file", "")
                if vf.exists():
                    return vf
        if skill_def.get("current_version") == version:
            fallback = self.governance / skill_def.get("file", "")
            if fallback.exists():
                return fallback
        return None

    def _load_variant(self, skill_id: str, variant_id: str) -> str:
        """加载指定变体。"""
        registry = self._load_registry()
        variants = registry.get("variants") or []

        for v in variants:
            if v.get("id") == variant_id and v.get("skill_id") == skill_id:
                variant_path = self.governance / v["file"]
                if not variant_path.exists():
                    raise FileNotFoundError(
                        f"Variant file not found: {variant_path}"
                    )
                return variant_path.read_text(encoding="utf-8")

        # 不带 skill_id 前缀的匹配
        for v in variants:
            if v.get("id") == variant_id:
                variant_path = self.governance / v["file"]
                if variant_path.exists():
                    return variant_path.read_text(encoding="utf-8")

        raise ValueError(
            f"Variant '{variant_id}' not found for skill '{skill_id}'."
        )
