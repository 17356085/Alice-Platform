"""alice-governance-suite — 开发 SOP + 门禁校验。

包含:
  - skills-dev/: 9 Agent × 32 Skill (开发 SOP)
  - sop_dev/: 10 Phase 定义
  - validators/: sop_validator + coverage_checker

安装:
    pip install alice-governance-suite

用法:
    from alice_governance_suite import get_skills_dev_path, get_sop_dev_path
    from alice_governance_suite.validators.sop_validator import validate_sop_state
"""

from pathlib import Path


def get_pack_path() -> Path:
    return Path(__file__).parent


def get_skills_dev_path() -> Path:
    return Path(__file__).parent / "skills-dev"


def get_sop_dev_path() -> Path:
    return Path(__file__).parent / "sop_dev"


def get_validators_path() -> Path:
    return Path(__file__).parent / "validators"
