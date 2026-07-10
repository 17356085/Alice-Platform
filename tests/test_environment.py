"""Environment 完整测试 (P6-4)

测试场景:
1. Environment CRUD 操作
2. 默认 Environment 管理
3. 变量解析（secret_ref）
4. 标签过滤
5. 集成 Secret Manager
"""

import pytest
from aitest.infra.db import get_session
from aitest.platform.environment_store import EnvironmentStore, reset_environment_store
from aitest.platform.secret_store import SecretStore


def test_environment_crud():
    """测试 Environment CRUD 操作"""
    reset_environment_store()
    session = next(get_session())
    store = EnvironmentStore(session)

    # 1. 创建 Environment
    env = store.create_environment(
        environment_id="test-env",
        name="Test Environment",
        base_url="https://test.example.com",
        description="Test environment for unit testing",
        variables={"API_KEY": "test-key", "TIMEOUT": "30"},
        tags=["test", "dev"],
        created_by="test_user",
    )

    assert env.environment_id == "test-env"
    assert env.name == "Test Environment"
    assert env.base_url == "https://test.example.com"
    assert env.variables["API_KEY"] == "test-key"
    assert env.tags == ["test", "dev"]

    # 2. 获取 Environment
    env_get = store.get_environment("test-env")
    assert env_get is not None
    assert env_get.name == "Test Environment"

    # 3. 列出 Environments
    envs = store.list_environments()
    assert len(envs) >= 1
    assert any(e.environment_id == "test-env" for e in envs)

    # 4. 更新 Environment
    updated = store.update_environment(
        environment_id="test-env",
        name="Updated Test Environment",
        variables={"API_KEY": "updated-key"},
    )
    assert updated.name == "Updated Test Environment"
    assert updated.variables["API_KEY"] == "updated-key"

    # 5. 删除 Environment
    success = store.delete_environment("test-env")
    assert success is True

    # 确认已删除
    deleted = store.get_environment("test-env")
    assert deleted is None

    print("✅ Environment CRUD 测试通过")


def test_default_environment():
    """测试默认 Environment 管理"""
    reset_environment_store()
    session = next(get_session())
    store = EnvironmentStore(session)

    # 1. 创建第一个 Environment（设为默认）
    env1 = store.create_environment(
        environment_id="env1",
        name="Environment 1",
        base_url="https://env1.example.com",
        is_default=True,
    )
    assert env1.is_default is True

    # 2. 获取默认 Environment
    default_env = store.get_default_environment()
    assert default_env is not None
    assert default_env.environment_id == "env1"

    # 3. 创建第二个 Environment（设为默认，应取消第一个）
    env2 = store.create_environment(
        environment_id="env2",
        name="Environment 2",
        base_url="https://env2.example.com",
        is_default=True,
    )
    assert env2.is_default is True

    # 确认第一个不再是默认
    env1_updated = store.get_environment("env1")
    assert env1_updated.is_default is False

    # 确认第二个是默认
    default_env = store.get_default_environment()
    assert default_env.environment_id == "env2"

    # 4. 使用 set_default_environment() 切换回第一个
    store.set_default_environment("env1")
    default_env = store.get_default_environment()
    assert default_env.environment_id == "env1"

    # 清理
    store.delete_environment("env1")
    store.delete_environment("env2")

    print("✅ 默认 Environment 测试通过")


def test_resolve_variables_with_secrets():
    """测试变量解析（secret_ref）"""
    reset_environment_store()
    session = next(get_session())
    env_store = EnvironmentStore(session)
    secret_store = SecretStore(session)

    # 1. 创建 Secret
    secret_store.create_secret(
        secret_id="test-db-password",
        name="Test DB Password",
        type="password",
        value="secret-db-password-123",
        created_by="test_user",
    )

    # 2. 创建 Environment（引用 Secret）
    env = env_store.create_environment(
        environment_id="test-env-with-secret",
        name="Test Environment with Secret",
        base_url="https://test.example.com",
        variables={
            "DB_HOST": "localhost",
            "DB_PORT": "5432",
            "DB_PASSWORD": "secret:test-db-password",  # 引用 Secret
            "API_TIMEOUT": "30",
        },
    )

    # 3. 获取 Environment（变量未解析）
    assert env.variables["DB_PASSWORD"] == "secret:test-db-password"

    # 4. 解析变量（自动解密 secret_ref）
    resolved = env_store.resolve_variables("test-env-with-secret")
    assert resolved["DB_HOST"] == "localhost"
    assert resolved["DB_PORT"] == "5432"
    assert resolved["DB_PASSWORD"] == "secret-db-password-123"  # 已解密
    assert resolved["API_TIMEOUT"] == "30"

    # 清理
    env_store.delete_environment("test-env-with-secret")
    secret_store.delete_secret("test-db-password", deleted_by="test_user")

    print("✅ 变量解析（secret_ref）测试通过")


def test_filter_by_tags():
    """测试标签过滤"""
    reset_environment_store()
    session = next(get_session())
    store = EnvironmentStore(session)

    # 创建多个 Environment
    store.create_environment(
        environment_id="env-staging",
        name="Staging",
        base_url="https://staging.example.com",
        tags=["staging", "qa"],
    )

    store.create_environment(
        environment_id="env-production",
        name="Production",
        base_url="https://prod.example.com",
        tags=["production"],
    )

    store.create_environment(
        environment_id="env-dev",
        name="Development",
        base_url="https://dev.example.com",
        tags=["dev", "staging"],
    )

    # 过滤标签
    staging_envs = store.list_environments(tags=["staging"])
    assert len(staging_envs) == 2  # env-staging, env-dev
    staging_ids = [e.environment_id for e in staging_envs]
    assert "env-staging" in staging_ids
    assert "env-dev" in staging_ids

    production_envs = store.list_environments(tags=["production"])
    assert len(production_envs) == 1
    assert production_envs[0].environment_id == "env-production"

    # 清理
    store.delete_environment("env-staging")
    store.delete_environment("env-production")
    store.delete_environment("env-dev")

    print("✅ 标签过滤测试通过")


def test_environment_has_secret_ref():
    """测试 Environment 辅助方法"""
    from aitest.platform.environment import Environment

    # 有 secret_ref
    env_with_secret = Environment(
        environment_id="test",
        name="Test",
        base_url="https://test.com",
        variables={
            "DB_PASSWORD": "secret:db-password",
            "API_KEY": "plain-key",
        },
    )

    assert env_with_secret.has_secret_ref() is True
    refs = env_with_secret.get_secret_refs()
    assert len(refs) == 1
    assert "secret:db-password" in refs

    # 无 secret_ref
    env_without_secret = Environment(
        environment_id="test2",
        name="Test2",
        base_url="https://test2.com",
        variables={
            "API_KEY": "plain-key",
            "TIMEOUT": "30",
        },
    )

    assert env_without_secret.has_secret_ref() is False
    assert env_without_secret.get_secret_refs() == []

    print("✅ Environment 辅助方法测试通过")


def test_end_to_end():
    """端到端测试：创建 Secret → 创建 Environment → 解析变量"""
    reset_environment_store()
    session = next(get_session())
    env_store = EnvironmentStore(session)
    secret_store = SecretStore(session)

    # 1. 创建 Secrets
    secret_store.create_secret(
        secret_id="e2e-db-password",
        name="E2E DB Password",
        type="password",
        value="e2e-db-password-value",
        created_by="e2e_test",
    )

    secret_store.create_secret(
        secret_id="e2e-api-key",
        name="E2E API Key",
        type="api_key",
        value="e2e-api-key-value",
        created_by="e2e_test",
    )

    # 2. 创建 Environment（引用 Secrets）
    env = env_store.create_environment(
        environment_id="e2e-env",
        name="E2E Environment",
        base_url="https://e2e.example.com",
        description="End-to-end test environment",
        variables={
            "DB_HOST": "e2e-db.example.com",
            "DB_PASSWORD": "secret:e2e-db-password",
            "API_KEY": "secret:e2e-api-key",
            "DEBUG_MODE": "true",
        },
        tags=["e2e", "test"],
        is_default=True,
    )

    # 3. 验证 Environment 配置
    assert env.environment_id == "e2e-env"
    assert env.base_url == "https://e2e.example.com"
    assert env.variables["DB_PASSWORD"] == "secret:e2e-db-password"  # 未解析
    assert env.is_default is True

    # 4. 解析变量
    resolved = env_store.resolve_variables("e2e-env")
    assert resolved["DB_HOST"] == "e2e-db.example.com"
    assert resolved["DB_PASSWORD"] == "e2e-db-password-value"  # 已解密
    assert resolved["API_KEY"] == "e2e-api-key-value"  # 已解密
    assert resolved["DEBUG_MODE"] == "true"

    # 5. 验证默认 Environment
    default_env = env_store.get_default_environment()
    assert default_env.environment_id == "e2e-env"

    # 清理
    env_store.delete_environment("e2e-env")
    secret_store.delete_secret("e2e-db-password", deleted_by="e2e_test")
    secret_store.delete_secret("e2e-api-key", deleted_by="e2e_test")

    print("✅ 端到端测试通过")


if __name__ == "__main__":
    print("🌍 Environment 完整测试\n")

    # 运行所有测试
    test_environment_crud()
    test_default_environment()
    test_resolve_variables_with_secrets()
    test_filter_by_tags()
    test_environment_has_secret_ref()
    test_end_to_end()

    print("\n🎉 所有测试通过！")
