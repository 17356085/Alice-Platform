"""
Prompt Adapter — 将 Claude 优化的 Skill Prompt 适配到目标 LLM Provider。

不同模型的 Prompt 偏好：
  Claude:  长指令、分层结构、XML tags 友好、严格遵循 system prompt
  GPT-4o:  分步骤、markdown 格式、system/user 分离
  Qwen3:   短指令、中文友好、示例驱动、不支持复杂嵌套
  本地模型: 需要更多示例、context 窗口小、不支持 XML tags

用法:
    adapter = PromptAdapter()
    adapted = adapter.adapt(skill_prompt, provider_type="ollama", context="...")
"""


class PromptAdapter:
    """跨模型 Prompt 适配器。"""

    # 各 Provider 的适配配置
    ADAPTATIONS = {
        "claude": {
            "max_system_length": 32000,
            "strip_xml_tags": False,
            "prefer_markdown": False,
            "add_examples": False,
        },
        "openai": {
            "max_system_length": 8000,
            "strip_xml_tags": False,
            "prefer_markdown": True,
            "add_examples": False,
        },
        "deepseek": {
            "max_system_length": 16000,
            "strip_xml_tags": False,
            "prefer_markdown": True,
            "add_examples": False,
        },
        "ollama": {
            "max_system_length": 4000,
            "strip_xml_tags": True,
            "prefer_markdown": True,
            "add_examples": True,
        },
    }

    def adapt(
        self,
        skill_prompt: str,
        provider_type: str,
        context: str = "",
    ) -> str:
        """
        将 Skill Prompt 适配到目标 Provider。

        参数:
            skill_prompt:  原始 Skill Markdown（Claude 优化版）
            provider_type: "claude" | "openai" | "ollama"
            context:       附加的上下文信息（如 PROJECT_CONTEXT 片段）

        返回:
            适配后的 system prompt
        """
        config = self.ADAPTATIONS.get(provider_type, {})
        if not config:
            return skill_prompt  # 未知 Provider，保持原样

        adapted = skill_prompt

        # 1. 移除 XML tags（本地模型不擅长解析）
        if config.get("strip_xml_tags"):
            adapted = self._strip_xml_tags(adapted)

        # 2. 注入示例（本地模型需要更多引导）
        if config.get("add_examples"):
            adapted = self._inject_few_shot(adapted)

        # 3. 注入上下文
        if context:
            separator = "\n\n---\n\n" if config.get("prefer_markdown") else "\n\n"
            adapted = f"{adapted}{separator}## 参考上下文\n{context}"

        # 4. 截断过长的 system prompt
        max_len = config.get("max_system_length", 32000)
        if len(adapted) > max_len:
            # 保留头部（Skill 指令）和尾部（上下文），截掉中间
            head_size = max_len // 2
            tail_size = max_len // 4
            adapted = (
                adapted[:head_size]
                + f"\n\n[... 中间内容已截断，共省略 {len(adapted) - max_len} 字符 ...]\n\n"
                + adapted[-tail_size:]
            )

        return adapted

    # ── 内部方法 ──

    def _strip_xml_tags(self, text: str) -> str:
        """移除 XML 风格的标签，转为 Markdown 格式。"""
        import re

        # <tag>content</tag> → **tag**: content
        text = re.sub(r'<(\w+)>(.*?)</\1>', r'**\1**: \2', text, flags=re.DOTALL)

        # <example> → ### 示例
        text = text.replace('<example>', '\n### 示例\n')
        text = text.replace('</example>', '\n')

        # <rules> → ### 规则
        text = text.replace('<rules>', '\n### 规则\n')
        text = text.replace('</rules>', '\n')

        return text

    def _inject_few_shot(self, text: str) -> str:
        """为 Skill Prompt 注入 few-shot 示例（如果 Skill 本身缺少示例）。"""
        # 检查是否已有示例
        if "示例" in text or "example" in text.lower() or "样例" in text:
            return text  # 已有示例，不重复注入

        # 对于特定类型的 Skill，注入通用示例模板
        example_templates = {
            "页面分析": (
                "\n\n### 输出示例（必须遵循此格式）\n"
                "```\n"
                "## 元素清单\n"
                "| 元素名称 | 类型 | 定位器 | 备注 |\n"
                "|---------|------|--------|------|\n"
                "| 搜索输入框 | input | .search-input | 在页面顶部 |\n"
                "```\n"
            ),
            "代码生成": (
                "\n\n### 输出示例（必须遵循此格式）\n"
                "```python\n"
                "class ExamplePage(BasePage):\n"
                "    search_input = (By.CSS_SELECTOR, '.search-input')\n"
                "    \n"
                "    def search(self, keyword: str):\n"
                "        self.input(self.search_input, keyword)\n"
                "```\n"
            ),
        }

        # 根据关键词注入对应示例
        for keyword, example in example_templates.items():
            if keyword in text:
                return text + example

        return text
