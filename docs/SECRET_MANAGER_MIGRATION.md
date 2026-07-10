# Secret Manager 迁移指南

> **创建时间**: 2026-07-11  
> **目标**: 从 `.env` 明文存储迁移到 Secret Manager

## 迁移收益

1. **安全性提升**: API Key 加密存储，不再明文保存
2. **集中管理**: 所有敏感信息统一管理，支持审计日志
3. **环境隔离**: 支持 dev/staging/prod 独立配置
4. **自动轮换**: 支持定期更新密钥，降低泄露风险
5. **向后兼容**: 渐进式迁移，现有代码无需修改

## 迁移步骤

### 步骤 1: 初始化 Secret Manager

Secret Manager 使用 Fernet 对称加密，需要生成加密密钥。

#### 方式 1: 自动生成（推荐）

首次启动服务时，会自动生成密钥并保存到 `governance/.data/.secret_key`：

```bash
# 启动服务（自动生成密钥）
aitest server start

# 输出:
# ⚠️  Please backup this key securely! Loss of this key means loss of all encrypted data.
# Encryption key saved to governance/.data/.secret_key
```

**⚠️ 重要**: 请立即备份 `governance/.data/.secret_key` 文件！丢失此文件将无法解密所有 Secret。

#### 方式 2: 使用环境变量

如果你希望在生产环境使用环境变量管理密钥：

```bash
# 生成密钥
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# 输出: xxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 设置环境变量
export SECRET_ENCRYPTION_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 启动服务
aitest server start
```

### 步骤 2: 创建 Secrets

将 `.env` 文件中的敏感信息迁移到 Secret Manager。

#### 示例: Anthropic API Key

**当前 `.env` 文件**:
```bash
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
GOOGLE_API_KEY=AIzaSyDxxxxx
MIMO_API_KEY=mimo-xxxxx
```

**创建 Secrets**:

方式 A: REST API（推荐）
```bash
# Anthropic API Key
curl -X POST http://localhost:8000/api/v1/secrets \
  -H "Content-Type: application/json" \
  -d '{
    "secret_id": "anthropic-api-key-prod",
    "name": "Anthropic API Key (Production)",
    "type": "api_key",
    "value": "sk-ant-api03-xxxxx",
    "description": "Production environment API key",
    "tags": ["production", "anthropic"]
  }'

# Google API Key
curl -X POST http://localhost:8000/api/v1/secrets \
  -H "Content-Type: application/json" \
  -d '{
    "secret_id": "google-api-key-prod",
    "name": "Google API Key (Production)",
    "type": "api_key",
    "value": "AIzaSyDxxxxx",
    "tags": ["production", "google"]
  }'

# Mimo API Key
curl -X POST http://localhost:8000/api/v1/secrets \
  -H "Content-Type: application/json" \
  -d '{
    "secret_id": "mimo-api-key-prod",
    "name": "Mimo API Key (Production)",
    "type": "api_key",
    "value": "mimo-xxxxx",
    "tags": ["production", "mimo"]
  }'
```

方式 B: Python SDK
```python
from aitest.infra.db import get_session
from aitest.platform.secret_store import SecretStore

session = next(get_session())
store = SecretStore(session)

# 创建 Secret
store.create_secret(
    secret_id="anthropic-api-key-prod",
    name="Anthropic API Key (Production)",
    type="api_key",
    value="sk-ant-api03-xxxxx",
    description="Production environment API key",
    tags=["production", "anthropic"],
    created_by="admin",
)
```

### 步骤 3: 更新 ModelProvider 配置

将 ModelProvider 从明文 `api_key` 切换到 `api_key_ref`。

#### 方式 A: 创建新 ModelProvider（推荐）

```bash
curl -X POST http://localhost:8000/api/v1/providers \
  -H "Content-Type: application/json" \
  -d '{
    "provider_id": "anthropic-prod",
    "name": "Anthropic Production",
    "type": "anthropic",
    "config": {
      "api_key_ref": "secret:anthropic-api-key-prod",
      "default_model": "claude-3-5-sonnet-20241022",
      "max_tokens": 4096
    }
  }'
```

#### 方式 B: 更新现有 ModelProvider

```bash
curl -X PUT http://localhost:8000/api/v1/providers/anthropic-prod \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "api_key_ref": "secret:anthropic-api-key-prod"
    }
  }'
```

### 步骤 4: 验证配置

测试 ModelProvider 是否能正常工作。

#### 方式 A: 测试连接（REST API）

```bash
curl -X POST http://localhost:8000/api/v1/providers/test \
  -H "Content-Type: application/json" \
  -d '{
    "type": "anthropic",
    "config": {
      "api_key_ref": "secret:anthropic-api-key-prod",
      "default_model": "claude-3-5-sonnet-20241022"
    }
  }'

# 响应:
# {
#   "success": true,
#   "test_response": "OK"
# }
```

#### 方式 B: 运行测试 Run

```bash
aitest run create --target agent:page-observer --module login --provider-id anthropic-prod
```

如果执行成功，说明 Secret Manager 配置正确。

### 步骤 5: 清理 `.env` 文件

迁移完成后，从 `.env` 中删除敏感信息。

```bash
# 备份
cp .env .env.backup

# 删除敏感信息
sed -i '/ANTHROPIC_API_KEY/d' .env
sed -i '/GOOGLE_API_KEY/d' .env
sed -i '/MIMO_API_KEY/d' .env

# 确认 .env.backup 已备份
ls -l .env.backup
```

**⚠️ 注意**: 不要删除 `.env` 文件本身，其他配置项可能仍需保留。

### 步骤 6: 更新 `.gitignore`

确保密钥文件不被提交到 Git：

```bash
# 添加到 .gitignore
echo "governance/.data/.secret_key" >> .gitignore
echo ".env.backup" >> .gitignore

# 确认已忽略
git check-ignore governance/.data/.secret_key
```

## 向后兼容说明

### get_provider() 优先级

```python
from aitest.adapters.llm.interface import get_provider

# 优先级 1: provider_id 参数（从 ModelProviderStore 加载）
llm = get_provider("claude", provider_id="anthropic-prod")
# → 使用 ModelProvider 的 api_key_ref

# 优先级 2: 环境变量（向后兼容）
llm = get_provider("claude")
# → 使用 ANTHROPIC_API_KEY 环境变量

# 优先级 3: 显式传入（测试用）
llm = get_provider("claude", api_key="sk-ant-test")
# → 使用传入的 api_key（覆盖所有其他来源）
```

### ModelProvider.get_api_key() 优先级

```python
# 优先级 1: api_key_ref（Secret Manager）
config = ProviderConfig(api_key_ref="secret:anthropic-api-key-prod")

# 优先级 2: api_key（明文，向后兼容）
config = ProviderConfig(api_key="sk-ant-plaintext")

# 优先级 3: 都没有（返回 None）
config = ProviderConfig()
```

### 渐进式迁移

你可以混合使用明文和 secret_ref，逐步迁移：

```python
# 已迁移的 Provider
provider_prod = ModelProvider(
    provider_id="anthropic-prod",
    config=ProviderConfig(api_key_ref="secret:anthropic-api-key-prod")
)

# 尚未迁移的 Provider（仍使用明文）
provider_dev = ModelProvider(
    provider_id="anthropic-dev",
    config=ProviderConfig(api_key="sk-ant-dev-plaintext")
)
```

## 回滚方案

如果遇到问题，可以快速回滚到明文方式。

### 方式 1: 恢复 .env 文件

```bash
# 恢复备份
cp .env.backup .env

# 重启服务
aitest server start
```

### 方式 2: 更新 ModelProvider 使用明文

```bash
curl -X PUT http://localhost:8000/api/v1/providers/anthropic-prod \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "api_key": "sk-ant-api03-xxxxx"
    }
  }'
```

## 生产环境最佳实践

### 1. 密钥备份

**文件加密方式**:
```bash
# 备份密钥文件
cp governance/.data/.secret_key /secure/backup/.secret_key.backup

# 或使用云端备份
aws s3 cp governance/.data/.secret_key s3://my-backup-bucket/secret-keys/
```

**环境变量方式**:
```bash
# 将密钥存储到云端 Secret Manager
aws secretsmanager create-secret \
  --name aitest-encryption-key \
  --secret-string "xxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# 容器启动时从云端加载
export SECRET_ENCRYPTION_KEY=$(aws secretsmanager get-secret-value \
  --secret-id aitest-encryption-key \
  --query SecretString \
  --output text)
```

### 2. 密钥轮换

定期更换 API Key，降低泄露风险：

```bash
# 1. 创建新版本 Secret
curl -X POST http://localhost:8000/api/v1/secrets \
  -H "Content-Type: application/json" \
  -d '{
    "secret_id": "anthropic-api-key-prod-v2",
    "name": "Anthropic API Key (Production v2)",
    "type": "api_key",
    "value": "sk-ant-new-key",
    "tags": ["production", "anthropic"]
  }'

# 2. 更新 ModelProvider 引用
curl -X PUT http://localhost:8000/api/v1/providers/anthropic-prod \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "api_key_ref": "secret:anthropic-api-key-prod-v2"
    }
  }'

# 3. 测试新 Key
curl -X POST http://localhost:8000/api/v1/providers/test \
  -d '{"type": "anthropic", "config": {"api_key_ref": "secret:anthropic-api-key-prod-v2"}}'

# 4. 删除旧 Key
curl -X DELETE http://localhost:8000/api/v1/secrets/anthropic-api-key-prod
```

### 3. 审计日志监控

定期检查 Secret 访问日志，发现异常访问：

```bash
# 获取审计日志
curl http://localhost:8000/api/v1/secrets/anthropic-api-key-prod/audit

# 响应:
# [
#   {"action": "read", "actor": "admin", "timestamp": "2026-07-11T10:00:00Z"},
#   {"action": "update", "actor": "admin", "timestamp": "2026-07-11T09:00:00Z"},
#   ...
# ]
```

### 4. 权限控制

生产环境应配置细粒度权限：

```yaml
# 权限配置示例（未来实现）
roles:
  - name: developer
    permissions:
      - secret:read  # 可查看 Secret 元数据
  - name: admin
    permissions:
      - secret:read
      - secret:read_value  # 可查看解密值
      - secret:create
      - secret:update
      - secret:delete
```

### 5. 多环境隔离

为不同环境创建独立的 Secrets：

```bash
# 生产环境
secret:anthropic-api-key-prod

# 测试环境
secret:anthropic-api-key-staging

# 开发环境
secret:anthropic-api-key-dev
```

对应的 ModelProvider：
```bash
# 生产
anthropic-prod → secret:anthropic-api-key-prod

# 测试
anthropic-staging → secret:anthropic-api-key-staging

# 开发
anthropic-dev → secret:anthropic-api-key-dev
```

## 常见问题

### Q1: 丢失了 `.secret_key` 文件怎么办？

**A**: 如果丢失加密密钥，所有已加密的 Secret 将无法解密。需要：
1. 重新生成新密钥
2. 重新创建所有 Secrets
3. 更新所有 ModelProvider 配置

**预防措施**: 定期备份 `governance/.data/.secret_key` 到安全位置。

### Q2: 如何在 Docker 容器中使用 Secret Manager？

**A**: 方式 1（环境变量）:
```dockerfile
# Dockerfile
ENV SECRET_ENCRYPTION_KEY=${SECRET_ENCRYPTION_KEY}

# docker-compose.yml
services:
  aitest:
    environment:
      - SECRET_ENCRYPTION_KEY=${SECRET_ENCRYPTION_KEY}
```

方式 2（挂载密钥文件）:
```yaml
services:
  aitest:
    volumes:
      - ./governance/.data/.secret_key:/app/governance/.data/.secret_key:ro
```

### Q3: 如何迁移到云端 Secret Manager（AWS/Azure/Vault）？

**A**: 当前版本支持文件加密，云端 Secret Manager 支持为占位实现。生产环境建议：
1. 使用文件加密 + 密钥存储到云端 Secret Manager
2. 或等待 P6-5 后续更新，完整集成云端 Secret Manager

### Q4: Secret Manager 是否支持版本历史？

**A**: 当前版本不支持。建议手动管理版本（如 `anthropic-api-key-prod-v1`, `v2`）。未来版本将支持自动版本历史。

### Q5: 如何批量导入 Secrets？

**A**: 使用 Python 脚本批量创建：
```python
from aitest.infra.db import get_session
from aitest.platform.secret_store import SecretStore
import os

session = next(get_session())
store = SecretStore(session)

# 从 .env 读取
secrets = {
    "anthropic-api-key-prod": os.getenv("ANTHROPIC_API_KEY"),
    "google-api-key-prod": os.getenv("GOOGLE_API_KEY"),
    "mimo-api-key-prod": os.getenv("MIMO_API_KEY"),
}

for secret_id, value in secrets.items():
    if value:
        store.create_secret(
            secret_id=secret_id,
            name=secret_id.replace("-", " ").title(),
            type="api_key",
            value=value,
            created_by="migration_script",
        )
        print(f"✅ Created: {secret_id}")
```

## 相关文档

- 设计文档: `docs/secret_manager_design.md`
- API 文档: `/docs#/secrets` (Swagger UI)
- 测试代码: `tests/test_secret_manager.py`
- 路线图: `docs/MASTER_ROADMAP.md` (P6-5)
