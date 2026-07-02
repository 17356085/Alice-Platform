"""Behavior Pack — 行为包加载器。

SDK 不硬编码 governance 路径。所有行为定义（skills、agents、context）
通过 BehaviorPack 统一加载。

三级 fallback:
  1. external pack（用户提供路径 → 挂载外部 governance）
  2. alice-governance（独立安装的完整行为包）
  3. governance_default（SDK 内置骨架 fallback）

用法:
    from alice_engine.behavior import BehaviorPack, load_behavior_pack

    # 模式 1: 外部行为包
    pack = load_behavior_pack("./governance")

    # 模式 2: 自动发现 alice-governance 或 governance_default
    pack = load_behavior_pack(None)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class BehaviorPack:
    """行为包 — SDK 的行为定义抽象层。

    不关心路径是 governance/ 还是别的名字，
    只提供 skills/agents/context 的统一访问接口。
    """

    root: Path | None = None

    @property
    def is_empty(self) -> bool:
        """是否有实际内容。"""
        return self.root is None or not self.root.exists()

    @property
    def skills_dir(self) -> Path | None:
        """skills 目录路径。"""
        if self.root is None:
            return None
        p = self.root / "skills"
        return p if p.exists() else None

    @property
    def skills_dev_dir(self) -> Path | None:
        """skills-dev 目录路径。"""
        if self.root is None:
            return None
        p = self.root / "skills-dev"
        return p if p.exists() else None

    @property
    def agents_dir(self) -> Path | None:
        """agents 目录路径。"""
        if self.root is None:
            return None
        p = self.root / "agents"
        return p if p.exists() else None

    @property
    def agents_yaml(self) -> Path | None:
        """agent-definitions.yaml 路径。"""
        d = self.agents_dir
        if d is None:
            return None
        p = d / "agent-definitions.yaml"
        return p if p.exists() else None

    @property
    def context_dir(self) -> Path | None:
        """context 目录路径。"""
        if self.root is None:
            return None
        p = self.root / "context"
        return p if p.exists() else None

    @property
    def artifacts_dir(self) -> Path | None:
        """artifacts 目录路径（自动创建）。"""
        if self.root is None:
            return None
        p = self.root / "artifacts"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def graph_state_dir(self) -> Path | None:
        """.graph_state 目录路径（自动创建）。"""
        if self.root is None:
            return None
        p = self.root / ".graph_state"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def kpi_dir(self) -> Path | None:
        """kpi 目录路径。"""
        if self.root is None:
            return None
        p = self.root / "kpi"
        return p if p.exists() else None

    def subpath(self, *parts: str) -> Path | None:
        """获取子路径（不存在则返回 None）。"""
        if self.root is None:
            return None
        p = self.root.joinpath(*parts)
        return p if p.exists() else None


def get_default_pack_path() -> Path:
    """获取 SDK 内置默认行为包路径。"""
    return Path(__file__).parent / "governance_default"


def _try_alice_governance() -> Path | None:
    """尝试发现 alice-governance 包。"""
    try:
        from alice_governance import get_pack_path
        p = get_pack_path()
        if p.exists():
            return p
    except ImportError:
        pass
    return None


def load_behavior_pack(path: str | Path | None = None) -> BehaviorPack:
    """加载行为包。

    优先级:
      1. 用户提供的 path（外部 governance）
      2. alice-governance 包（pip install alice-governance）
      3. SDK 内置 governance_default（骨架 fallback）

    Args:
        path: 行为包根目录路径。None 则自动发现。

    Returns:
        BehaviorPack 实例。
    """
    # 优先级 1: 用户显式指定的外部路径
    if path is not None:
        root = Path(path).resolve()
        if root.exists():
            logger.info("Behavior pack loaded: %s", root)
            return BehaviorPack(root=root)
        logger.warning("Behavior pack path does not exist: %s", root)

    # 优先级 2: alice-governance 包（独立安装的完整行为包）
    gov_root = _try_alice_governance()
    if gov_root is not None:
        logger.info("Using alice-governance pack: %s", gov_root)
        return BehaviorPack(root=gov_root)

    # 优先级 3: SDK 内置骨架 fallback
    default_root = get_default_pack_path()
    if default_root.exists():
        logger.info("Using default behavior pack: %s", default_root)
        return BehaviorPack(root=default_root)

    logger.warning("No behavior pack available")
    return BehaviorPack(root=None)
