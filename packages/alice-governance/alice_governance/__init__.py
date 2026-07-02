"""alice-governance — 完整行为定义层。

安装:
    pip install alice-governance

用法:
    from alice_governance import get_pack_path
    from alice_engine.behavior import load_behavior_pack

    pack = load_behavior_pack(get_pack_path())
    loader = SkillLoader(governance_path=pack.root)
"""

from pathlib import Path


def get_pack_path() -> Path:
    """获取 governance pack 路径。"""
    return Path(__file__).parent
