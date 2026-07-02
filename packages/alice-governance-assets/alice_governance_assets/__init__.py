"""alice-governance-assets — 知识库 + 上下文模板。

包含:
  - knowledge/: 测试模式 + 已知坑位 (RAG 知识库)
  - context_templates/: environments.yaml + known-issues.yaml 模板

安装:
    pip install alice-governance-assets

用法:
    from alice_governance_assets import get_knowledge_path, get_context_templates_path
"""

from pathlib import Path


def get_pack_path() -> Path:
    return Path(__file__).parent


def get_knowledge_path() -> Path:
    """获取知识库目录路径（供 RAG 引擎索引）。"""
    return Path(__file__).parent / "knowledge"


def get_context_templates_path() -> Path:
    """获取上下文模板目录路径。"""
    return Path(__file__).parent / "context_templates"
