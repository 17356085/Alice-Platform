"""SafetyAuditor — 运行时安全检查。"""

import re
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SafetyFlag:
    severity: str = "low"
    rule: str = ""
    detail: str = ""


_SAFETY_RULES = [
    ("hardcoded_password", r'password\s*=\s*["\'][^"\']+["\']', "high", "硬编码密码"),
    ("hardcoded_token", r'(api_key|token|secret)\s*=\s*["\'][^"\']+["\']', "high", "硬编码密钥"),
    ("sql_injection", r'(execute|cursor\.execute)\s*\(\s*["\'].*%s', "critical", "SQL 注入风险"),
    ("eval_usage", r'\beval\s*\(', "critical", "eval() 调用"),
    ("exec_usage", r'\bexec\s*\(', "critical", "exec() 调用"),
    ("os_system", r'\bos\.system\s*\(', "high", "os.system() 调用"),
    ("subprocess_shell", r'subprocess\.\w+\(.*shell\s*=\s*True', "high", "subprocess shell=True"),
    ("pickle_load", r'pickle\.load', "medium", "pickle 反序列化"),
]


def check_output_safety(content: str, skill_id: str = "") -> list:
    if not content:
        return []
    flags = []
    for rule_name, pattern, severity, detail in _SAFETY_RULES:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            flags.append(SafetyFlag(severity=severity, rule=rule_name, detail=f"{detail}: {len(matches)} 处"))
    return flags
