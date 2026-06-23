"""
Intent Parser — 自然语言 → 结构化测试意图。

双层策略:
  1. 规则匹配（零 token）：正则识别高频测试指令
  2. LLM 兜底（~200 tokens）：复杂/模糊意图

用法:
    from aitest.chat.intent_parser import parse_intent
    result = parse_intent("给equipment/alarm-config写自动化测试")
    # → {"type":"run_agent", "agent":"automation-agent", "module":"equipment", "page":"alarm-config"}
"""
import re
from pathlib import Path
from typing import Optional


# ══════════════════════════════════════════════════════════════════════════
#  模块发现
# ══════════════════════════════════════════════════════════════════════════

def _get_known_modules() -> list[str]:
    governance = Path(__file__).resolve().parent.parent.parent / "governance"
    from aitest.platform.paths import get_project_dir
    modules_dir = get_project_dir() / "modules"
    if modules_dir.exists():
        return sorted([d.name for d in modules_dir.iterdir() if d.is_dir()])
    return []


# ══════════════════════════════════════════════════════════════════════════
#  规则匹配
# ══════════════════════════════════════════════════════════════════════════

# Agent 别名映射
# 格式: (匹配模式, agent_name, 权重)
# 模式中空格分隔的多个词 = 所有词必须在消息中出现（任意顺序、不要求连续）
AGENT_ALIASES = [
    # 中文
    ("完整流程", "full-sop", 8), ("全流程", "full-sop", 6),
    ("bug分析", "bug-analysis-agent", 7), ("失败分析", "bug-analysis-agent", 7),
    ("bug", "bug-analysis-agent", 5),
    ("写测试", "automation-agent", 7), ("生成测试", "automation-agent", 7),
    ("生成代码", "automation-agent", 7), ("测试代码", "automation-agent", 7),
    ("自动化", "automation-agent", 5), ("page object", "automation-agent", 7),
    ("分析", "test-design-agent", 5), ("页面分析", "test-design-agent", 7),
    ("元素分析", "test-design-agent", 7), ("测试用例", "test-design-agent", 7),
    ("test case", "test-design-agent", 7), ("测试设计", "test-design-agent", 7),
    ("sop", "full-sop", 5),
    # 英文
    ("full sop", "full-sop", 8), ("complete flow", "full-sop", 8),
    ("bug analysis", "bug-analysis-agent", 7), ("root cause", "bug-analysis-agent", 7),
    ("write test", "automation-agent", 7), ("generate test", "automation-agent", 7),
    ("automation", "automation-agent", 6), ("automate", "automation-agent", 6),
    ("generate code", "automation-agent", 7), ("code generation", "automation-agent", 7),
    ("analyze page", "test-design-agent", 7), ("page analysis", "test-design-agent", 7),
    ("element analysis", "test-design-agent", 7), ("analyze elements", "test-design-agent", 7),
    ("test design", "test-design-agent", 7),
]


def parse_intent(message: str) -> dict:
    """
    解析用户消息为结构化意图。

    返回:
        {
            "type": "run_agent"|"run_sop"|"run_skill"|"status"|"question"|"chat",
            "agent": "automation-agent"|"test-design-agent"|"bug-analysis-agent"|...,
            "module": "equipment",
            "page": "alarm-config",
            "skill_id": "",
            "confidence": 0.0-1.0,
        }
    """
    msg = message.strip()
    result: dict = {
        "type": "chat",
        "agent": "",
        "module": "",
        "page": "",
        "skill_id": "",
        "confidence": 0.0,
    }

    known_modules = _get_known_modules()
    module_pattern = "|".join(re.escape(m) for m in known_modules) if known_modules else r"\w+"

    # ── 提取模块和页面 ──
    # 模式: module/page 或 module page 或 "XX模块" 或 "XX的YY"
    m = re.search(rf"({module_pattern})\s*[/\s]\s*([a-zA-Z0-9_-]+)", msg)
    if m:
        result["module"] = m.group(1)
        result["page"] = m.group(2)
    else:
        # "XX模块"
        m2 = re.search(rf"({module_pattern})\s*模块", msg)
        if m2:
            result["module"] = m2.group(1)
        # "XX的XX" 或单独模块名
        m3 = re.search(rf"({module_pattern})的([a-zA-Z0-9一-鿿_-]+)", msg)
        if m3:
            result["module"] = m3.group(1)
            result["page"] = m3.group(2)

    mod = result["module"]
    page = result["page"]

    # ── 意图匹配 ──
    msg_lower = msg.lower()

    # 状态查询
    if re.search(r"状态|进度|dashboard|check\b", msg_lower) and not re.search(r"测试|自动化|写|生成", msg_lower):
        result["type"] = "status"
        result["confidence"] = 0.95
        return result

    # Agent 意图匹配（按权重优先级）
    # 模式中空格分隔的词 = 全部出现才匹配（不要求连续、不要求顺序）
    best_score = 0
    best_agent = ""
    best_is_sop = False
    for pattern, agent, weight in AGENT_ALIASES:
        words = pattern.lower().split()
        if all(w in msg_lower for w in words):
            if weight > best_score:
                best_score = weight
                if agent == "full-sop":
                    best_is_sop = True
                    best_agent = "automation-agent"
                else:
                    best_is_sop = False
                    best_agent = agent

    if best_score > 0:
        if best_is_sop:
            result["type"] = "run_sop"
        else:
            result["type"] = "run_agent"
        result["agent"] = best_agent
        result["confidence"] = min(best_score / 8.0, 1.0)

    # 有模块但没匹配到 agent → 默认 automation-agent
    if result["type"] == "chat" and mod:
        result["type"] = "run_agent"
        result["agent"] = "automation-agent"
        result["confidence"] = 0.5

    return result


def parse_with_llm(message: str, provider: str = "claude") -> dict:
    """
    LLM 兜底：复杂意图用 LLM 分类。

    仅当规则匹配 confidence < 0.5 时才调用。
    """
    known_modules = _get_known_modules()

    prompt = f"""你是测试意图分类器。分析用户消息，输出 JSON。

已知模块: {', '.join(known_modules) if known_modules else '从消息中提取'}
意图类型: run_agent(执行单个Agent) | run_sop(完整SOP流水线) | status(查看状态) | chat(一般对话)
Agent: automation-agent(写代码) | test-design-agent(测试设计) | bug-analysis-agent(Bug分析) | report-agent(报告)

输出格式: {{"type":"...","agent":"...","module":"...","page":"...","confidence":0.0}}

用户消息: {message}

JSON:"""

    try:
        from aitest.llm.provider import get_provider
        llm = get_provider(provider)
        response = llm.complete(
            system_prompt="你是意图分类器。只输出 JSON，不要解释。",
            user_prompt=prompt,
            max_tokens=200,
            temperature=0.1,
        )
        content = response.content.strip()
        # 提取 JSON
        json_match = re.search(r'\{[^{}]*\}', content, re.DOTALL)
        if json_match:
            import json
            result = json.loads(json_match.group())
            result["_llm_fallback"] = True
            return result
    except Exception:
        pass

    return {"type": "chat", "agent": "", "module": "", "page": "", "confidence": 0.0}
