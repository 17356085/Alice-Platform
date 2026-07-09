"""Deprecated provider implementation.

Mock LLM Provider — 用于测试，不调用真实 API。

用法:
    from aitest.llm.providers.mock import MockProvider

    provider = MockProvider()
    response = provider.complete("system", "user")
    print(response.content)  # "[Mock] 测试输出"
"""

import time
from aitest.adapters.llm.provider_base import LLMResponse, LLMProvider


class MockProvider(LLMProvider):
    """Mock LLM Provider — 返回固定响应，不调用真实 API。"""

    def __init__(self, **kwargs):
        self.model = "mock-model"
        self.call_count = 0

    def supports_tools(self) -> bool:
        """Mock 支持 tool calling (用于测试)。"""
        return True

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        tools=None,
        temperature: float = 0.7,
        max_tokens: int = 8192,
    ) -> LLMResponse:
        """返回 Mock 响应。"""
        self.call_count += 1

        # 根据 system_prompt 推断 Skill 类型
        skill_type = self._infer_skill_type(system_prompt)

        # 生成对应的 Mock 内容
        content = self._generate_mock_content(skill_type, system_prompt, user_prompt)

        return LLMResponse(
            content=content,
            token_usage={
                "input": len(system_prompt) + len(user_prompt),
                "output": len(content),
                "total": len(system_prompt) + len(user_prompt) + len(content),
            },
            model=self.model,
            finish_reason="stop",
        )

    def stream_complete(
        self,
        system_prompt: str,
        user_prompt: str,
        tools=None,
        temperature: float = 0.7,
        max_tokens: int = 8192,
    ):
        """返回 Mock 流式响应。"""
        from aitest.adapters.llm.provider_base import StreamEvent

        response = self.complete(system_prompt, user_prompt, tools, temperature, max_tokens)

        # 模拟流式输出
        words = response.content.split()
        for i, word in enumerate(words):
            yield StreamEvent(
                type="content_chunk",
                content=word + " ",
            )

        yield StreamEvent(
            type="done",
            finish_reason="stop",
            token_usage=response.token_usage,
        )

    def _infer_skill_type(self, system_prompt: str) -> str:
        """从 system_prompt 推断 Skill 类型。"""
        prompt_lower = system_prompt.lower()

        if "project" in prompt_lower and "context" in prompt_lower:
            return "project"
        elif "requirement" in prompt_lower or "module" in prompt_lower:
            return "requirement"
        elif "test" in prompt_lower and "design" in prompt_lower:
            return "test_design"
        elif "test" in prompt_lower and "case" in prompt_lower:
            return "test_case"
        elif "automation" in prompt_lower or "page object" in prompt_lower:
            return "automation"
        elif "tech" in prompt_lower and "analysis" in prompt_lower:
            return "tech_analysis"
        elif "strategy" in prompt_lower:
            return "strategy"
        elif "execute" in prompt_lower or "pytest" in prompt_lower:
            return "execution"
        elif "report" in prompt_lower:
            return "report"
        elif "knowledge" in prompt_lower:
            return "knowledge"
        else:
            return "generic"

    def _generate_mock_content(self, skill_type: str, system_prompt: str, user_prompt: str) -> str:
        """生成 Mock 内容。"""
        # 从 user_prompt 提取模块和页面信息
        module = ""
        page = ""
        if "模块:" in user_prompt:
            parts = user_prompt.split("模块:")
            if len(parts) > 1:
                module = parts[1].split(",")[0].split("，")[0].strip()
        if "页面:" in user_prompt:
            parts = user_prompt.split("页面:")
            if len(parts) > 1:
                page = parts[1].split(",")[0].split("，")[0].strip()

        mock_contents = {
            "project": f"""# PROJECT_CONTEXT.md

## 项目概览
- 项目名称: 鞍集涂源管理系统
- 技术栈: Vue 3 + Element Plus
- 测试框架: pytest-selenium

## 模块列表
- equipment (设备管理)
- tank (储罐管理)
- production (生产管理)
- dcs (DCS 系统)
- personnel (人员管理)

## 页面统计
总计: 12 个页面
""",
            "requirement": f"""# MODULE_CONTEXT.md

## 模块: {module or 'equipment'}
- 描述: 设备管理模块
- 页面数: 4

## 页面列表
- alarm-config (告警配置)
- camera (摄像头管理)
- key-param (关键参数)
- maintenance (设备维护)

## 业务流程
1. 用户登录系统
2. 进入设备管理模块
3. 选择具体页面进行操作
""",
            "test_design": f"""# TEST_DESIGN.md

## 测试场景
- BS-001: 正常添加告警配置
- BS-002: 编辑告警配置
- BS-003: 删除告警配置
- BS-004: 搜索告警配置

## 风险点
- 数据验证不完整
- 权限控制缺失
- 并发操作冲突
""",
            "test_case": f"""# TEST_CASES.md

## 测试用例

| 编号 | 标题 | 优先级 | 状态 |
|------|------|--------|------|
| TC-001 | 添加告警配置 | P0 | 待执行 |
| TC-002 | 编辑告警配置 | P1 | 待执行 |
| TC-003 | 删除告警配置 | P1 | 待执行 |
| TC-004 | 搜索告警配置 | P2 | 待执行 |

## P0 用例
- TC-001: 添加告警配置 (核心功能)
""",
            "tech_analysis": f"""# TECH_ANALYSIS.md

## 页面元素分析
- 输入框: el-input (3个)
- 按钮: el-button (5个)
- 表格: el-table (1个)
- 分页: el-pagination (1个)

## 路由信息
- 路径: #/equipment/alarm-config
- 类型: Hash 路由

## API 接口
- GET /api/alarm/list
- POST /api/alarm/config
- DELETE /api/alarm/config/{{id}}
""",
            "strategy": f"""# AUTO_STRATEGY.md

## 定位器策略
- 优先使用 CSS 选择器
- 避免使用 XPath
- 使用 data-testid 属性

## 等待策略
- 使用 wait_vue_stable()
- 避免 time.sleep()
- 显式等待最长 10s

## 文件结构
- Page Object: page/{module or 'equipment'}_page/{page or 'AlarmConfig'}Page.py
- 测试脚本: script/{module or 'equipment'}/test_{page or 'alarm_config'}.py
""",
            "automation": f"""# Page Object 代码

```python
from base.base_page import BasePage

class {(page or 'AlarmConfig').replace('-', '').title()}Page(BasePage):
    \"\"\"告警配置页面对象。\"\"\"

    # 定位器
    SEARCH_INPUT = ".el-input:first-child"
    SEARCH_BUTTON = ".el-button--primary"
    ADD_BUTTON = ".el-button--success"
    TABLE = ".el-table"

    def search(self, keyword: str):
        \"\"\"搜索告警。\"\"\"
        self.fill(self.SEARCH_INPUT, keyword)
        self.click(self.SEARCH_BUTTON)

    def add_alarm(self, name: str, device: str):
        \"\"\"添加告警。\"\"\"
        self.click(self.ADD_BUTTON)
        # ... 填写表单
```

# 测试脚本

```python
import pytest
from page.{module or 'equipment'}_page.{(page or 'AlarmConfig').replace('-', '').title()}Page import {(page or 'AlarmConfig').replace('-', '').title()}Page

class Test{(page or 'AlarmConfig').replace('-', '').title()}:
    def test_add_alarm(self, browser):
        \"\"\"测试添加告警配置。\"\"\"
        page = {(page or 'AlarmConfig').replace('-', '').title()}Page(browser)
        page.search("测试")
        page.add_alarm("测试告警", "设备A")
        # 断言...
```
""",
            "execution": f"""# 测试执行结果

## 执行摘要
- 总用例: 4
- 通过: 3
- 失败: 1
- 跳过: 0
- 耗时: 12.5s

## 失败详情
- test_edit_alarm: TimeoutError (编辑弹窗加载超时)
""",
            "report": f"""# TEST_REPORT_{module or 'equipment'}.md

## 测试报告
- 模块: {module or 'equipment'}
- 页面: {page or 'alarm-config'}
- 执行时间: 2026-07-01

## 结果统计
- 总用例: 4
- 通过: 3 (75%)
- 失败: 1 (25%)
- 耗时: 12.5s

## 失败用例
- test_edit_alarm: TimeoutError
""",
            "knowledge": f"""# 知识沉淀

## 模块: {module or 'equipment'}
- 已学习页面: {page or 'alarm-config'}
- 已知问题: 1个
- 覆盖率: 75%
""",
            "generic": f"""[Mock] 测试输出

模块: {module or 'unknown'}
页面: {page or 'unknown'}

这是一个 Mock 响应，用于测试 Engine 流程。
实际执行时会调用真实 LLM API。
""",
        }

        return mock_contents.get(skill_type, mock_contents["generic"])
