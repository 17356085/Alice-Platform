"""Provider 单元测试。"""

import pytest
from alice_engine.providers import (
    MockProvider,
    get_provider,
    get_provider_contract,
    list_providers,
    list_provider_contracts,
    register_provider,
    register_provider_contract,
)
from alice_engine.providers.base import LLMProvider, LLMResponse, ProviderContract


class TestMockProvider:
    """MockProvider 测试。"""

    def test_mock_provider_init(self):
        """测试 MockProvider 初始化。"""
        provider = MockProvider()
        assert provider.supports_tools() is True

    def test_mock_provider_complete(self):
        """测试 MockProvider.complete()。"""
        provider = MockProvider()
        response = provider.complete("system", "user")

        assert isinstance(response, LLMResponse)
        assert response.content != ""
        assert response.model == "mock"
        assert response.finish_reason == "stop"
        assert response.token_usage == {
            "prompt_tokens": 100,
            "completion_tokens": 200,
            "input": 100,
            "output": 200,
            "total": 300,
        }


class TestProviderRegistry:
    """Provider 注册表测试。"""

    def test_list_providers(self):
        """测试列出 Provider。"""
        providers = list_providers()
        assert "mock" in providers
        assert "claude" in providers
        assert "openai" in providers

    def test_list_provider_contracts(self):
        contracts = list_provider_contracts()
        assert any(c.name == "mock" and c.supports_tools for c in contracts)

    def test_get_mock_provider(self):
        """测试获取 MockProvider。"""
        provider = get_provider("mock")
        assert isinstance(provider, MockProvider)

    def test_get_provider_contract(self):
        contract = get_provider_contract("mock")
        assert contract is not None
        assert contract.name == "mock"
        assert contract.supports_tools is True

    def test_get_unknown_provider(self):
        """测试获取未知 Provider。"""
        from alice_engine.exceptions import LLMProviderError
        with pytest.raises(LLMProviderError):
            get_provider("unknown")

    def test_register_provider(self):
        """测试注册自定义 Provider。"""
        class MyProvider(LLMProvider):
            provider_name = "my-provider"
            provider_supports_tools = False

            def supports_tools(self):
                return False

            def complete(self, system_prompt, user_prompt, **kwargs):
                return LLMResponse(content="my response")

        register_provider("my-provider", MyProvider)
        provider = get_provider("my-provider")
        assert isinstance(provider, MyProvider)

    def test_register_provider_contract(self):
        contract = ProviderContract(name="external-provider", description="plugin", available=True)
        register_provider_contract("external-provider", contract)
        resolved = get_provider_contract("external-provider")
        assert resolved is not None
        assert resolved.name == "external-provider"
        assert resolved.description == "plugin"
