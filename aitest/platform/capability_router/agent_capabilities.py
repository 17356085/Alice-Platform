"""Agent → Capability 映射 (声明式配置)。

参考 Aperant config/agent-configs.ts: AGENT_CONFIGS registry。

每个 Agent 声明它需要哪些 Capability。
CapabilityRouter 据此生成传给 LLM 的 tool definitions。
"""
from typing import Dict, List

AGENT_CAPABILITIES: Dict[str, List[str]] = {
    # ── Project Agent: 项目初始化 + 上下文发现 ──
    "project-agent": [
        "rag.search",
        "rag.business_rules",
    ],

    # ── Requirement Agent: 需求分析 ──
    "requirement-agent": [
        "rag.business_rules",
        "rag.search",              # 查找相似页面/模块的测试模式
        "browser.navigate",        # 访问页面了解结构
    ],

    # ── Test Design Agent: 测试设计 ──
    "test-design-agent": [
        "rag.search",              # 查找已知 UI 模式 + 定位器历史
        "rag.business_rules",
        "browser.navigate",        # 观察页面组件
        "browser.screenshot",      # 截图保存为设计参考
    ],

    # ── Automation Agent: 自动化代码生成 ──
    "automation-agent": [
        "codegen.page_object",
        "codegen.test_script",
        "rag.search",              # 查找已知 UI 模式 + Gotcha
        "rag.business_rules",
        "execute.python",          # 验证生成代码的语法
    ],

    # ── Execution Agent: 测试执行 ──
    "execution-agent": [
        "execute.pytest",
        "browser.screenshot",      # 失败截图
        "rag.search",              # 查找已知问题
    ],

    # ── Bug Analysis Agent: 缺陷分析 ──
    "bug-analysis-agent": [
        "execute.pytest",          # 复现测试
        "browser.navigate",
        "browser.screenshot",
        "rag.search",              # 查找已知问题 + 修复方案
    ],

    # ── Report Agent: 报告生成 ──
    "report-agent": [
        "rag.search",              # 补充背景信息
        "rag.business_rules",
    ],

    # ── Knowledge Agent: 知识库更新 ──
    "knowledge-agent": [
        "rag.search",
        "rag.business_rules",
    ],
}
