"""alice-engine Default Governance Pack — 最小语义编译器。

这不是业务系统，是 SDK 的 bootstrap 行为包。
让 workflow 每个 phase 有可执行的 skill prompt。

用法:
    from alice_engine.governance_default import get_default_pack_path
    pack = load_behavior_pack(get_default_pack_path())
"""

from pathlib import Path


def get_default_pack_path() -> Path:
    """获取默认行为包路径。"""
    return Path(__file__).parent
