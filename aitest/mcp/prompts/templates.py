"""
P1-1: Prompt 模板文本常量（纯数据，与逻辑分离）。
每个模板以 module-level 常量导出，由 prompts/__init__.py 的 _PromptDef 引用。
"""

GENERATE_PAGE_OBJECT = (
    "你是一个精通 Python + Selenium + Pytest 的测试自动化专家。\n\n"
    "请阅读以下上下文：\n"
    "- resource://page-doc/{module}/{page}/PAGE_CONTEXT.md\n"
    "- resource://page-doc/{module}/{page}/PAGE_INTERFACE.yaml（如果有）\n"
    "- resource://project-context/basepage-api\n"
    "- resource://project-context/rules\n\n"
    "任务：为 {module} 模块的 {page} 页面生成 Page Object 类。\n\n"
    "要求：\n"
    "1. 继承 BasePage\n"
    "2. 使用 CSS Selector / 相对 XPath（禁止绝对 XPath）\n"
    "3. 使用 wait_vue_stable() / WebDriverWait（禁止 time.sleep）\n"
    "4. 使用 self.navigate_to() 导航（禁止手动点击菜单）\n"
    "5. 不做断言（assert 只在 test_*.py 中）\n\n"
    "生成后自检：\n"
    '- grep -n "class \\w\\+:" <file>\n'
    '- grep "time.sleep" <file>\n'
    '- grep "print(" <file>\n'
    "如有违规，自动修正。"
)

ANALYZE_FAILURE = (
    "你是测试失败分析专家。请分析以下 pytest 失败：\n\n"
    "模块: {module}\n"
    "错误输出:\n```\n{error_output}\n```\n\n"
    "分析步骤:\n"
    "1. 使用 tool:rag_search_known_issues 搜索已知问题（query=错误关键词）\n"
    "2. 使用 tool:get_module_status 查看模块 SOP 状态\n"
    "3. 判断根因: 定位器问题 / 等待问题 / 数据问题 / 环境问题 / 代码红线违规\n"
    "4. 给出修复方案（具体到文件:行号）\n"
    "5. 如果匹配已知问题，引用 known_issue.id 并给出已验证的修复策略\n\n"
    "输出格式: 根因 + 修复方案 + 是否自动修复"
)

DESIGN_TEST_CASES = (
    "你是测试设计专家。请基于以下上下文设计测试用例：\n\n"
    "- resource://page-doc/{module}/{page}/PAGE_CONTEXT.md\n"
    "- resource://page-doc/{module}/{page}/RISK_MODEL.md（如果有）\n"
    "- resource://project-context/ep-pitfalls\n\n"
    "要求：\n"
    "1. 按 P0（核心流程）/ P1（重要功能）/ P2（边界异常）三级优先级排列\n"
    "2. 每个用例包含: ID / 标题 / 前置条件 / 步骤 / 预期结果 / 风险等级\n"
    "3. 覆盖 Element Plus 已知坑位（下拉框/弹窗/日期选择器等）\n"
    "4. 至少包含 1 个「非破坏性」用例作为冒烟测试候选\n\n"
    "目标产出: TEST_CASES.md"
)

REVIEW_CODE = (
    "对以下文件执行代码红线扫描（8 条）:\n"
    "文件: {file}\n\n"
    "红线清单:\n"
    "1. ❌ 不继承 BasePage → ✅ class XxxPage(BasePage)\n"
    "2. ❌ 绝对 XPath → ✅ CSS Selector / 相对 XPath\n"
    "3. ❌ time.sleep(N) → ✅ wait_vue_stable() / WebDriverWait\n"
    "4. ❌ print() 调试 → ✅ logger.info() / logger.warning()\n"
    "5. ❌ 手动菜单导航 → ✅ self.navigate_to(\"一级\", \"二级\")\n"
    "6. ❌ 重复/副本文件 → ✅ 确认后删除 Git 冲突副本\n"
    "7. ❌ Page Object 含 assert → ✅ assert 只在 test_*.py\n"
    "8. ❌ 硬编码 URL/密码 → ✅ config.py / .env\n\n"
    "使用 tool:check_code_quality target={file} 执行自动化检查。\n"
    "对于每条违规，给出: 位置(文件:行号) → 修复建议 → 自动修复代码。"
)

SOP_STATUS = (
    "请使用 tool:get_module_status 查看以下模块的 SOP 进度:\n"
    "模块: {module}\n\n"
    "然后判断:\n"
    "1. 当前处于哪个 Phase\n"
    "2. 缺失哪些产物（MODULE_CONTEXT / PAGE_CONTEXT / TEST_CASES / PageObject / 测试脚本）\n"
    "3. 下一步应该做什么（使用 run_sop mode=resume 续跑 或 mode=full 重跑）\n"
    "4. 估算剩余工作量\n\n"
    "输出: 状态报告（含文档完整性清单）"
)

BUG_REPORT = (
    "从以下测试失败生成标准化 Bug 报告:\n\n"
    "模块: {module}\n"
    "测试用例: {test_name}\n"
    "失败输出:\n```\n{failure_output}\n```\n\n"
    "报告格式:\n"
    "1. Bug ID (自动生成: BUG-{module}-YYYYMMDD-NNN)\n"
    "2. 标题 (一句话描述)\n"
    "3. 严重度 (Critical / High / Medium / Low)\n"
    "4. 复现步骤 (从 test_name 推断)\n"
    "5. 实际结果 vs 预期结果\n"
    "6. 根因分析 (使用 tool:rag_search_known_issues + search_known_issues)\n"
    "7. 建议修复 (具体到文件:行号)\n"
    "8. 关联已知问题 (如有)\n\n"
    "使用 tool:rag_search_known_issues 确认是否为已知问题。"
)
