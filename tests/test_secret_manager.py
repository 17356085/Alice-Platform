"""Secret Manager 完整测试 (P6-5)

测试场景:
1. 加密/解密功能
2. Secret CRUD 操作
3. 审计日志
4. secret_ref 解析
5. ModelProvider 集成（api_key_ref）
6. 过期检查
"""

import os
import pytest
from pathlib import Path
from datetime import datetime, timezone, timedelta

# 设置测试用加密密钥
os.environ["SECRET_ENCRYPTION_KEY"] = "test-key-for-testing-only-32bytes="


def test_encryption_provider():
    """测试加密 Provider"""
    from aitest.infra.encryption import FileEncryptionProvider, reset_encryption_provider

    reset_encryption_provider()

    # 创建加密 Provider（使用环境变量密钥）
    provider = FileEncryptionProvider()

    # 测试加密/解密
    plaintext = "sk-ant-api03-test-key-123456789"
    encrypted = provider.encrypt(plaintext)

    # 加密后应该不同
    assert encrypted != plaintext
    assert len(encrypted) > 0

    # 解密应该恢复原文
    decrypted = provider.decrypt(encrypted)
    assert decrypted == plaintext

    print("✅ 加密/解密测试通过")


def test_secret_store_crud():
    """测试 SecretStore CRUD 操作"""
    from aitest.infra.db import get_session
    from aitest.platform.secret_store import SecretStore
    from aitest.infra.encryption import reset_encryption_provider

    reset_encryption_provider()
    session = next(get_session())
    store = SecretStore(session)

    # 1. 创建 Secret
    secret = store.create_secret(
        secret_id="test-api-key",
        name="Test API Key",
        type="api_key",
        value="sk-test-secret-value",
        description="Test secret for unit testing",
        tags=["test", "api_key"],
        created_by="test_user",
    )

    assert secret.secret_id == "test-api-key"
    assert secret.name == "Test API Key"
    assert secret.value == ""  # 创建时不返回明文

    # 2. 获取 Secret（不解密）
    secret_no_decrypt = store.get_secret("test-api-key", decrypt=False)
    assert secret_no_decrypt is not None
    assert secret_no_decrypt.value == ""

    # 3. 获取 Secret（解密）
    secret_decrypt = store.get_secret("test-api-key", decrypt=True)
    assert secret_decrypt is not None
    assert secret_decrypt.value == "sk-test-secret-value"

    # 4. 列出 Secrets
    secrets = store.list_secrets(type="api_key")
    assert len(secrets) >= 1
    assert any(s.secret_id == "test-api-key" for s in secrets)

    # 5. 更新 Secret
    updated = store.update_secret(
        secret_id="test-api-key",
        name="Updated Test API Key",
        description="Updated description",
    )
    assert updated.name == "Updated Test API Key"

    # 6. 删除 Secret
    success = store.delete_secret("test-api-key", deleted_by="test_user")
    assert success is True

    # 确认已删除
    deleted = store.get_secret("test-api-key", decrypt=False, check_expiry=False)
    assert deleted is None

    print("✅ SecretStore CRUD 测试通过")


def test_audit_logs():
    """测试审计日志"""
    from aitest.infra.db import get_session
    from aitest.platform.secret_store import SecretStore
    from aitest.infra.encryption import reset_encryption_provider

    reset_encryption_provider()
    session = next(get_session())
    store = SecretStore(session)

    # 创建 Secret
    store.create_secret(
        secret_id="audit-test-key",
        name="Audit Test Key",
        type="api_key",
        value="secret-value",
        created_by="test_user",
    )

    # 访问 Secret（触发 read 审计）
    store.get_secret("audit-test-key", decrypt=True)

    # 更新 Secret（触发 update 审计）
    store.update_secret("audit-test-key", name="Updated Name", updated_by="test_user")

    # 获取审计日志
    logs = store.get_audit_logs("audit-test-key")

    # 应该有 3 条日志: create, read, update
    assert len(logs) >= 3

    actions = [log.action for log in logs]
    assert "create" in actions
    assert "read" in actions
    assert "update" in actions

    # 清理
    store.delete_secret("audit-test-key", deleted_by="test_user")

    print("✅ 审计日志测试通过")


def test_secret_expiry():
    """测试 Secret 过期检查"""
    from aitest.infra.db import get_session
    from aitest.platform.secret_store import SecretStore
    from aitest.infra.encryption import reset_encryption_provider

    reset_encryption_provider()
    session = next(get_session())
    store = SecretStore(session)

    # 创建已过期的 Secret
    expired_time = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()

    store.create_secret(
        secret_id="expired-key",
        name="Expired Key",
        type="api_key",
        value="expired-value",
        expires_at=expired_time,
        created_by="test_user",
    )

    # 获取时应该抛出异常
    with pytest.raises(ValueError, match="Secret expired"):
        store.get_secret("expired-key", decrypt=True, check_expiry=True)

    # 不检查过期时应该能获取
    secret = store.get_secret("expired-key", decrypt=True, check_expiry=False)
    assert secret is not None
    assert secret.value == "expired-value"

    # 清理
    store.delete_secret("expired-key", deleted_by="test_user")

    print("✅ 过期检查测试通过")


def test_resolve_secret_ref():
    """测试 secret_ref 解析"""
    from aitest.infra.db import get_session
    from aitest.platform.secret_store import SecretStore, resolve_secret_ref
    from aitest.infra.encryption import reset_encryption_provider

    reset_encryption_provider()
    session = next(get_session())
    store = SecretStore(session)

    # 创建 Secret
    store.create_secret(
        secret_id="ref-test-key",
        name="Ref Test Key",
        type="api_key",
        value="sk-ref-test-value",
        created_by="test_user",
    )

    # 测试 secret_ref 解析
    ref = "secret:ref-test-key"
    resolved = resolve_secret_ref(ref, session)
    assert resolved == "sk-ref-test-value"

    # 测试非 secret_ref（直接返回）
    plaintext = "sk-plain-value"
    resolved_plain = resolve_secret_ref(plaintext, session)
    assert resolved_plain == plaintext

    # 测试不存在的 secret_ref
    with pytest.raises(ValueError, match="Secret not found"):
        resolve_secret_ref("secret:nonexistent", session)

    # 清理
    store.delete_secret("ref-test-key", deleted_by="test_user")

    print("✅ secret_ref 解析测试通过")


def test_model_provider_integration():
    """测试 ModelProvider 集成（api_key_ref）"""
    from aitest.infra.db import get_session
    from aitest.platform.secret_store import SecretStore
    from aitest.platform.model_provider import ModelProvider, ProviderConfig
    from aitest.infra.encryption import reset_encryption_provider

    reset_encryption_provider()
    session = next(get_session())
    store = SecretStore(session)

    # 1. 创建 Secret
    store.create_secret(
        secret_id="anthropic-api-key-test",
        name="Anthropic API Key (Test)",
        type="api_key",
        value="sk-ant-test-integration-key",
        created_by="test_user",
    )

    # 2. 创建 ModelProvider（使用 api_key_ref）
    provider = ModelProvider(
        provider_id="test-provider",
        name="Test Provider",
        type="anthropic",
        config=ProviderConfig(
            api_key_ref="secret:anthropic-api-key-test",
            default_model="claude-3-5-sonnet-20241022",
        ),
    )

    # 3. 获取 API Key（应该自动解析 secret_ref）
    api_key = provider.get_api_key()
    assert api_key == "sk-ant-test-integration-key"

    # 4. 测试向后兼容（明文 api_key）
    provider_plain = ModelProvider(
        provider_id="test-provider-plain",
        name="Test Provider Plain",
        type="anthropic",
        config=ProviderConfig(
            api_key="sk-ant-plain-key",
        ),
    )

    api_key_plain = provider_plain.get_api_key()
    assert api_key_plain == "sk-ant-plain-key"

    # 5. 测试 api_key_ref 优先级高于 api_key
    provider_priority = ModelProvider(
        provider_id="test-provider-priority",
        name="Test Provider Priority",
        type="anthropic",
        config=ProviderConfig(
            api_key="sk-ant-should-be-ignored",
            api_key_ref="secret:anthropic-api-key-test",
        ),
    )

    api_key_priority = provider_priority.get_api_key()
    assert api_key_priority == "sk-ant-test-integration-key"

    # 清理
    store.delete_secret("anthropic-api-key-test", deleted_by="test_user")

    print("✅ ModelProvider 集成测试通过")


def test_end_to_end():
    """端到端测试：创建 Secret → 关联 ModelProvider → 验证"""
    from aitest.infra.db import get_session
    from aitest.platform.secret_store import SecretStore
    from aitest.platform.model_provider_store import ModelProviderStore
    from aitest.infra.encryption import reset_encryption_provider

    reset_encryption_provider()
    session = next(get_session())
    secret_store = SecretStore(session)
    provider_store = ModelProviderStore(session)

    # 1. 创建 Secret
    secret_store.create_secret(
        secret_id="e2e-api-key",
        name="E2E API Key",
        type="api_key",
        value="sk-e2e-test-value",
        tags=["e2e", "test"],
        created_by="e2e_test",
    )

    # 2. 创建 ModelProvider（引用 Secret）
    from aitest.platform.model_provider import ProviderConfig
    provider_store.create_provider(
        provider_id="e2e-provider",
        name="E2E Test Provider",
        type="anthropic",
        config=ProviderConfig(
            api_key_ref="secret:e2e-api-key",
            default_model="claude-3-5-sonnet-20241022",
        ),
        created_by="e2e_test",
    )

    # 3. 获取 ModelProvider 并验证 API Key
    provider = provider_store.get_provider("e2e-provider")
    assert provider is not None

    api_key = provider.get_api_key()
    assert api_key == "sk-e2e-test-value"

    # 4. 验证审计日志
    logs = secret_store.get_audit_logs("e2e-api-key")
    assert len(logs) >= 2  # create + read

    # 清理
    provider_store.delete_provider("e2e-provider")
    secret_store.delete_secret("e2e-api-key", deleted_by="e2e_test")

    print("✅ 端到端测试通过")


if __name__ == "__main__":
    print("🔐 Secret Manager 完整测试\n")

    # 运行所有测试
    test_encryption_provider()
    test_secret_store_crud()
    test_audit_logs()
    test_secret_expiry()
    test_resolve_secret_ref()
    test_model_provider_integration()
    test_end_to_end()

    print("\n🎉 所有测试通过！")
