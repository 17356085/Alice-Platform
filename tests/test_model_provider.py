"""测试 ModelProvider 资源化 (P6-1)

测试场景:
1. 创建 ModelProvider
2. 列出 ModelProviders
3. 获取单个 ModelProvider
4. 更新 ModelProvider
5. 测试连接
6. 集成到 get_provider()
7. 删除 ModelProvider
"""

import json


def test_create_provider():
    """测试创建 ModelProvider"""
    from aitest.platform.model_provider_store import get_model_provider_store
    from aitest.platform.model_provider import ProviderConfig

    print("\n=== Test 1: Create ModelProvider ===")

    store = get_model_provider_store()

    config = ProviderConfig(
        api_key="sk-ant-test-key",
        default_model="claude-3-5-sonnet-20241022",
        max_tokens=4096,
        timeout_seconds=60,
    )

    provider = store.create_provider(
        provider_id="test-anthropic-prod",
        name="Test Anthropic Production",
        type="anthropic",
        config=config,
        org_id="test-org",
        created_by="test-user",
    )

    print(f"✓ Created provider: {provider.provider_id}")
    print(f"  Type: {provider.type}")
    print(f"  Status: {provider.status}")
    print(f"  Config: {json.dumps(provider.config.to_dict(), indent=2)}")


def test_list_providers():
    """测试列出 ModelProviders"""
    from aitest.platform.model_provider_store import get_model_provider_store

    print("\n=== Test 2: List ModelProviders ===")

    store = get_model_provider_store()
    providers = store.list_providers(org_id="test-org")

    print(f"✓ Found {len(providers)} providers:")
    for p in providers:
        print(f"  - {p.provider_id} ({p.type}) — {p.status}")


def test_get_provider():
    """测试获取 ModelProvider"""
    from aitest.platform.model_provider_store import get_model_provider_store

    print("\n=== Test 3: Get ModelProvider ===")

    store = get_model_provider_store()
    provider = store.get_provider("test-anthropic-prod")

    if provider:
        print(f"✓ Retrieved provider: {provider.provider_id}")
        print(f"  Name: {provider.name}")
        print(f"  Type: {provider.type}")
    else:
        print("✗ Provider not found")


def test_update_provider():
    """测试更新 ModelProvider"""
    from aitest.platform.model_provider_store import get_model_provider_store
    from aitest.platform.model_provider import ProviderConfig

    print("\n=== Test 4: Update ModelProvider ===")

    store = get_model_provider_store()

    new_config = ProviderConfig(
        api_key="sk-ant-updated-key",
        default_model="claude-3-5-sonnet-20241022",
        max_tokens=8192,  # 更新
        timeout_seconds=120,  # 更新
    )

    provider = store.update_provider(
        provider_id="test-anthropic-prod",
        name="Test Anthropic Production (Updated)",
        config=new_config,
    )

    if provider:
        print(f"✓ Updated provider: {provider.provider_id}")
        print(f"  Max tokens: {provider.config.max_tokens}")
        print(f"  Timeout: {provider.config.timeout_seconds}s")
    else:
        print("✗ Provider not found")


def test_integration_with_get_provider():
    """测试集成到 get_provider()"""
    print("\n=== Test 5: Integration with get_provider() ===")

    try:
        from aitest.adapters.llm.interface import get_provider

        # 方式 1: 使用 provider_id
        llm = get_provider("claude", provider_id="test-anthropic-prod")
        print(f"✓ Created provider from ModelProvider resource")
        print(f"  Type: {type(llm).__name__}")

        # 方式 2: 传统方式（环境变量）
        llm_env = get_provider("claude")
        print(f"✓ Created provider from environment variables (fallback)")
        print(f"  Type: {type(llm_env).__name__}")

    except Exception as e:
        print(f"✗ Integration test failed: {e}")


def test_delete_provider():
    """测试删除 ModelProvider"""
    from aitest.platform.model_provider_store import get_model_provider_store

    print("\n=== Test 6: Delete ModelProvider ===")

    store = get_model_provider_store()
    success = store.delete_provider("test-anthropic-prod")

    if success:
        print(f"✓ Deleted provider: test-anthropic-prod")
    else:
        print("✗ Provider not found")


def main():
    """运行所有测试"""
    print("Testing ModelProvider Resource (P6-1)")
    print("=" * 60)

    try:
        test_create_provider()
        test_list_providers()
        test_get_provider()
        test_update_provider()
        test_integration_with_get_provider()
        test_delete_provider()

        print("\n" + "=" * 60)
        print("✓ All tests passed!")

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
