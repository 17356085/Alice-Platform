"""Skill reference with version support (P4-1)."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class SkillRef:
    """Skill 引用（带版本）

    支持两种格式：
    - v1.0: "project/skill-name" (解析为 version="latest")
    - v2.0: {"id": "project/skill-name", "version": "1.2.0", "sha256": "..."}
    """
    id: str               # "project/context-sync"
    version: str = "latest"  # "1.2.0" | "latest"
    sha256: Optional[str] = None  # 内容哈希（可选）

    def to_dict(self):
        """转为字典格式"""
        result = {"id": self.id, "version": self.version}
        if self.sha256:
            result["sha256"] = self.sha256
        return result

    @classmethod
    def parse(cls, skill_entry) -> "SkillRef":
        """解析 skill 引用（兼容 v1.0 和 v2.0）

        Args:
            skill_entry: str 或 dict

        Returns:
            SkillRef 实例
        """
        if isinstance(skill_entry, str):
            # v1.0 format: "project/skill-name"
            return cls(id=skill_entry, version="latest", sha256=None)
        elif isinstance(skill_entry, dict):
            # v2.0 format: {id, version, sha256}
            return cls(
                id=skill_entry.get("id", ""),
                version=skill_entry.get("version", "latest"),
                sha256=skill_entry.get("sha256")
            )
        else:
            raise ValueError(f"Invalid skill entry format: {skill_entry}")
