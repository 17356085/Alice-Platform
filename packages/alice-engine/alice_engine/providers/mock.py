"""MockProvider — 用于测试的 Mock LLM 提供者。"""

import logging
from typing import Any

from alice_engine.providers.base import LLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class MockProvider(LLMProvider):
    """Mock LLM Provider — 用于测试和演示。

    不调用真实 LLM，返回预设的 mock 内容。
    """

    provider_name = "mock"
    provider_description = "Local mock provider for tests and demos"
    provider_supports_tools = True

    def supports_tools(self) -> bool:
        return True

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        tools: list[dict] | None = None,
        **kwargs,
    ) -> LLMResponse:
        """返回 mock 响应。"""
        skill_type = self._infer_skill_type(system_prompt)
        content = self._generate_mock_content(skill_type, system_prompt, user_prompt)

        logger.debug("MockProvider: skill_type=%s, content_len=%d", skill_type, len(content))

        return LLMResponse(
            content=content,
            tool_calls=[],
            usage={"prompt_tokens": 100, "completion_tokens": 200},
            model="mock",
            finish_reason="stop",
        )

    def _infer_skill_type(self, system_prompt: str) -> str:
        """从 system prompt 推断 skill 类型。"""
        prompt_lower = system_prompt.lower()

        if "page object" in prompt_lower or "po_generator" in prompt_lower:
            return "po_generator"
        elif "test script" in prompt_lower or "script" in prompt_lower:
            return "script_generator"
        elif "review" in prompt_lower:
            return "review"
        elif "observe" in prompt_lower or "explore" in prompt_lower:
            return "observe"
        elif "plan" in prompt_lower:
            return "plan"
        elif "gate" in prompt_lower or "quality" in prompt_lower:
            return "gate"
        else:
            return "generic"

    def _generate_mock_content(
        self, skill_type: str, system_prompt: str, user_prompt: str
    ) -> str:
        """生成 mock 内容。"""
        if skill_type == "po_generator":
            return self._mock_po_generator(user_prompt)
        elif skill_type == "script_generator":
            return self._mock_script_generator(user_prompt)
        elif skill_type == "review":
            return self._mock_review()
        elif skill_type == "observe":
            return self._mock_observe()
        elif skill_type == "plan":
            return self._mock_plan()
        elif skill_type == "gate":
            return self._mock_gate()
        else:
            return self._mock_generic()

    def _mock_po_generator(self, user_prompt: str) -> str:
        return """```python
from base.base_page import BasePage

class MockPage(BasePage):
    \"\"\"Mock Page Object。\"\"\"

    # 定位器
    locators = {
        "add_button": ("xpath", "//button[contains(text(),'新增')]"),
        "search_input": ("xpath", "//input[@placeholder='搜索']"),
        "table": ("css", ".el-table"),
    }

    def navigate(self):
        self.navigate_to("/mock")

    def add_item(self, data: dict):
        self.click("add_button")
        # ... fill form
```"""

    def _mock_script_generator(self, user_prompt: str) -> str:
        return """```python
import pytest

class TestMockPage:
    \"\"\"Mock 测试脚本。\"\"\"

    def test_add_item(self, page):
        \"\"\"测试新增功能。\"\"\"
        page.navigate()
        page.add_item({"name": "test"})
        assert page.is_success()

    def test_search(self, page):
        \"\"\"测试搜索功能。\"\"\"
        page.navigate()
        page.search("test")
        assert page.has_results()
```"""

    def _mock_review(self) -> str:
        return '{"passed": true, "issues": [], "score": 95}'

    def _mock_observe(self) -> str:
        return """页面结构分析:
- 主要组件: 表格、搜索栏、操作按钮
- 框架: Element Plus
- 路由: /mock
- 权限: 需要登录"""

    def _mock_plan(self) -> str:
        return """测试计划:
1. 页面探索和 PO 生成
2. 测试脚本编写
3. 执行和验证
4. 代码审查"""

    def _mock_gate(self) -> str:
        return '{"passed": true, "coverage": 85, "quality_score": 90}'

    def _mock_generic(self) -> str:
        return "Mock response: task completed successfully."
