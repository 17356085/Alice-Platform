"""alice-governance — 完整行为定义层。

包含:
  - skills/: 测试自动化 Skill (24 个)
  - skills-dev/: 开发 Skill (32 个)
  - agents/: Agent 定义
  - validators/: SOP + 覆盖率校验器
  - knowledge/: RAG 知识库
  - context_templates/: 环境配置模板
  - sop_dev/: 开发 SOP 10 Phase 定义

安装:
    pip install alice-governance

用法:
    from alice_governance import get_pack_path, get_knowledge_path, get_validators_path
"""

from pathlib import Path


def get_pack_path() -> Path:
    """获取 governance pack 路径。"""
    return Path(__file__).parent


def get_knowledge_path() -> Path:
    """获取知识库目录路径（供 RAG 引擎索引）。"""
    return Path(__file__).parent / "knowledge"


def get_context_templates_path() -> Path:
    """获取上下文模板目录路径。"""
    return Path(__file__).parent / "context_templates"


def get_skills_dev_path() -> Path:
    """获取开发 Skill 目录路径。"""
    return Path(__file__).parent / "skills-dev"


def get_sop_dev_path() -> Path:
    """获取开发 SOP 目录路径。"""
    return Path(__file__).parent / "sop_dev"


def get_validators_path() -> Path:
    """获取校验器目录路径。"""
    return Path(__file__).parent / "validators"
