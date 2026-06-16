"""
MCP 路径配置 — 单一事实源。
所有模块从此导入路径常量，避免硬编码。
"""
from pathlib import Path

WORKSTUDY = Path(__file__).resolve().parent.parent.parent
ZJSN_TEST = WORKSTUDY / "ZJSN_Test-master526"
GOVERNANCE = WORKSTUDY / "governance"
PROJECT_CONTEXT = GOVERNANCE / "context" / "projects" / "web-automation" / "PROJECT_CONTEXT.md"
KNOWN_ISSUES = GOVERNANCE / "context" / "known-issues.yaml"
MODULE_INDEX = GOVERNANCE / "context" / "projects" / "web-automation" / "MODULE_INDEX.md"
ENVIRONMENTS = GOVERNANCE / "context" / "environments.yaml"
ARTIFACTS_DIR = GOVERNANCE / "artifacts"
CONTEXT_MODULES = GOVERNANCE / "context" / "projects" / "web-automation" / "modules"
AUDIT_DIR = GOVERNANCE / "audit"
AUDIT_LOG_FILE = AUDIT_DIR / "tool-calls.jsonl"

# SOP Gate 检查脚本
SOP_GATE_SCRIPT = ZJSN_TEST / "tools" / "check_sop_gate.py"
CODE_QUALITY_SCRIPT = ZJSN_TEST / "tools" / "check_code_quality.py"
