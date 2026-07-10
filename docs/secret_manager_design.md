# Secret Manager 设计文档

> **创建时间**: 2026-07-11  
> **状态**: ✅ 设计完成  
> **相关任务**: P6-5 Secret Manager

## 设计目标

1. **安全存储**: 替换 `.env` 明文存储，加密保存敏感信息
2. **统一管理**: 集中管理 API Key、密码、Token 等敏感信息
3. **引用机制**: 通过 `secret_ref` 引用 Secret，解耦配置和密钥
4. **环境分离**: 开发环境文件加密，生产环境支持云端 Secret Manager
5. **审计追溯**: 记录 Secret 创建、更新、访问日志

## 架构概览

```
Secret Manager
  ├── Secret (数据模型)
  ├── SecretStore (CRUD + 加密/解密)
  ├── EncryptionProvider (加密实现)
  │   ├── FileEncryption (开发环境：Fernet 对称加密)
  │   └── CloudProvider (生产环境：AWS Secrets Manager / Vault)
  ├── REST API (/api/v1/secrets)
  └── Integration (ModelProvider / Environment / MCPServer)
```

## 核心组件

### 1. Secret 数据模型

```python
@dataclass
class Secret:
    secret_id: str          # 唯一标识（如 "anthropic-api-key"）
    name: str               # 显示名称（如 "Anthropic API Key (Production)"）
    type: str               # "api_key" | "password" | "token" | "certificate"
    value: str              # 加密后的值（不直接暴露）
    description: str        # 描述信息
    tags: List[str]         # 标签（如 ["production", "anthropic"]）
    org_id: str             # 组织 ID
    created_by: str         # 创建者
    created_at: str         # 创建时间
    updated_at: str         # 更新时间
    last_accessed_at: str   # 最后访问时间
    expires_at: Optional[str] # 过期时间（可选）
```

### 2. 数据库表设计

```sql
CREATE TABLE secrets (
    secret_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,                  -- "api_key" | "password" | "token" | "certificate"
    encrypted_value TEXT NOT NULL,       -- 加密后的值
    description TEXT DEFAULT '',
    tags TEXT DEFAULT '[]',              -- JSON 数组
    org_id TEXT NOT NULL DEFAULT 'default-org',
    created_by TEXT NOT NULL DEFAULT 'admin',
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    last_accessed_at TIMESTAMP,
    expires_at TIMESTAMP,
    
    INDEX idx_secrets_org_id (org_id),
    INDEX idx_secrets_type (type),
    INDEX idx_secrets_tags (tags)  -- GIN index for PostgreSQL
);

-- 审计日志表
CREATE TABLE secret_audit_logs (
    log_id TEXT PRIMARY KEY,
    secret_id TEXT NOT NULL,
    action TEXT NOT NULL,                -- "create" | "read" | "update" | "delete"
    actor TEXT NOT NULL,                 -- 执行者
    ip_address TEXT,
    timestamp TIMESTAMP NOT NULL,
    metadata TEXT DEFAULT '{}',          -- JSON
    
    INDEX idx_audit_secret_id (secret_id),
    INDEX idx_audit_timestamp (timestamp),
    FOREIGN KEY (secret_id) REFERENCES secrets(secret_id) ON DELETE CASCADE
);
```

### 3. 加密方案

#### 开发环境：文件加密 (Fernet)

**加密密钥管理**:
```python
# 方式 1: 从环境变量加载（推荐）
SECRET_ENCRYPTION_KEY=<base64-encoded-key>

# 方式 2: 从文件加载（备选）
governance/.data/.secret_key  # 不纳入 git
```

**密钥生成**:
```bash
# 初始化时自动生成
aitest secrets init
# 输出: Secret encryption key saved to governance/.data/.secret_key
#       Please backup this key securely!
```

**加密实现**:
```python
from cryptography.fernet import Fernet

class FileEncryptionProvider:
    def __init__(self, key_path: str = None):
        self.key = self._load_or_generate_key(key_path)
        self.fernet = Fernet(self.key)
    
    def encrypt(self, plaintext: str) -> str:
        """加密明文，返回 base64 字符串"""
        return self.fernet.encrypt(plaintext.encode()).decode()
    
    def decrypt(self, ciphertext: str) -> str:
        """解密密文，返回明文"""
        return self.fernet.decrypt(ciphertext.encode()).decode()
    
    def _load_or_generate_key(self, key_path: str) -> bytes:
        """加载或生成密钥"""
        if key_path and Path(key_path).exists():
            return Path(key_path).read_bytes()
        
        # 尝试从环境变量加载
        if key := os.getenv("SECRET_ENCRYPTION_KEY"):
            return key.encode()
        
        # 生成新密钥
        new_key = Fernet.generate_key()
        if key_path:
            Path(key_path).parent.mkdir(parents=True, exist_ok=True)
            Path(key_path).write_bytes(new_key)
        return new_key
```

**存储位置**:
```
governance/.data/secrets/
  ├── .secret_key              # 加密密钥（不纳入 git）
  └── secrets.db               # SQLite 数据库（存储加密后的值）
```

#### 生产环境：云端 Secret Manager

**支持的云服务**:
- AWS Secrets Manager
- Azure Key Vault
- HashiCorp Vault
- Google Secret Manager

**实现接口**:
```python
class CloudEncryptionProvider:
    def __init__(self, provider: str, config: dict):
        self.provider = provider  # "aws" | "azure" | "vault" | "gcp"
        self.config = config
        self.client = self._init_client()
    
    def encrypt(self, plaintext: str) -> str:
        """云端加密不在本地进行，返回原文"""
        return plaintext
    
    def decrypt(self, ciphertext: str) -> str:
        """云端解密，从远程获取"""
        return self.client.get_secret_value(ciphertext)
    
    def store_secret(self, secret_id: str, value: str) -> str:
        """存储到云端，返回引用 ID"""
        return self.client.create_secret(secret_id, value)
```

### 4. secret_ref 引用机制

**引用格式**:
```
secret:<secret_id>
```

**示例**:
```python
# ModelProvider 配置
{
  "provider_id": "anthropic-prod",
  "config": {
    "api_key_ref": "secret:anthropic-api-key-prod"  # 引用 Secret
  }
}

# Environment 配置
{
  "environment_id": "staging",
  "secrets": {
    "admin_password": "secret:staging-admin-pw"
  }
}

# MCPServer 配置
{
  "mcp_server_id": "slack",
  "env": {
    "SLACK_BOT_TOKEN": "secret:slack-bot-token"
  }
}
```

**解析逻辑**:
```python
def resolve_secret_ref(ref: str) -> str:
    """解析 secret_ref，返回明文值"""
    if not ref.startswith("secret:"):
        return ref  # 不是 secret_ref，直接返回
    
    secret_id = ref[7:]  # 去掉 "secret:" 前缀
    secret_store = get_secret_store()
    secret = secret_store.get_secret(secret_id)
    
    if not secret:
        raise ValueError(f"Secret not found: {secret_id}")
    
    # 更新最后访问时间
    secret_store.update_last_accessed(secret_id)
    
    return secret.decrypt_value()
```

### 5. SecretStore 接口

```python
class SecretStore:
    def __init__(self, session, encryption_provider):
        self.session = session
        self.encryption = encryption_provider
    
    def create_secret(
        self,
        secret_id: str,
        name: str,
        type: str,
        value: str,  # 明文
        description: str = "",
        tags: List[str] = None,
        org_id: str = "default-org",
        created_by: str = "admin",
        expires_at: Optional[str] = None,
    ) -> Secret:
        """创建 Secret（自动加密）"""
        encrypted_value = self.encryption.encrypt(value)
        # ... 存储到数据库
    
    def get_secret(self, secret_id: str, decrypt: bool = True) -> Optional[Secret]:
        """获取 Secret（可选解密）"""
        secret = self.session.query(SecretModel).filter_by(secret_id=secret_id).first()
        if not secret:
            return None
        
        result = Secret.from_orm(secret)
        if decrypt:
            result.value = self.encryption.decrypt(secret.encrypted_value)
        
        # 记录审计日志
        self._log_access(secret_id, "read")
        
        return result
    
    def list_secrets(
        self,
        org_id: str = None,
        type: str = None,
        tags: List[str] = None,
        include_expired: bool = False,
    ) -> List[Secret]:
        """列出 Secrets（不返回解密值）"""
        # ... 查询数据库
    
    def update_secret(
        self,
        secret_id: str,
        name: str = None,
        value: str = None,  # 明文，如果提供则重新加密
        description: str = None,
        tags: List[str] = None,
        expires_at: Optional[str] = None,
    ) -> Secret:
        """更新 Secret"""
        # ... 更新数据库
    
    def delete_secret(self, secret_id: str) -> bool:
        """删除 Secret"""
        # ... 删除数据库记录 + 审计日志
    
    def rotate_secret(self, secret_id: str, new_value: str) -> Secret:
        """轮换 Secret（保留旧版本历史）"""
        # ... 创建新版本
    
    def _log_access(self, secret_id: str, action: str, metadata: dict = None):
        """记录审计日志"""
        # ... 写入 secret_audit_logs 表
```

### 6. REST API

#### 端点列表

```
POST   /api/v1/secrets              # 创建 Secret
GET    /api/v1/secrets              # 列出 Secrets（不返回解密值）
GET    /api/v1/secrets/:id          # 获取 Secret（不返回解密值）
GET    /api/v1/secrets/:id/value    # 获取 Secret 解密值（需要权限）
PUT    /api/v1/secrets/:id          # 更新 Secret
DELETE /api/v1/secrets/:id          # 删除 Secret
POST   /api/v1/secrets/:id/rotate   # 轮换 Secret
GET    /api/v1/secrets/:id/audit    # 获取审计日志
```

#### 请求/响应模型

**创建 Secret**:
```json
POST /api/v1/secrets
{
  "secret_id": "anthropic-api-key-prod",
  "name": "Anthropic API Key (Production)",
  "type": "api_key",
  "value": "sk-ant-...",  // 明文，服务端自动加密
  "description": "Production environment API key",
  "tags": ["production", "anthropic"],
  "expires_at": "2027-01-01T00:00:00Z"  // 可选
}

Response:
{
  "secret_id": "anthropic-api-key-prod",
  "name": "Anthropic API Key (Production)",
  "type": "api_key",
  "description": "Production environment API key",
  "tags": ["production", "anthropic"],
  "created_at": "2026-07-11T10:00:00Z",
  "expires_at": "2027-01-01T00:00:00Z"
  // 注意：不返回 value
}
```

**获取 Secret（不解密）**:
```json
GET /api/v1/secrets/anthropic-api-key-prod

Response:
{
  "secret_id": "anthropic-api-key-prod",
  "name": "Anthropic API Key (Production)",
  "type": "api_key",
  "description": "Production environment API key",
  "tags": ["production", "anthropic"],
  "created_at": "2026-07-11T10:00:00Z",
  "last_accessed_at": "2026-07-11T12:00:00Z"
  // 不返回 value
}
```

**获取 Secret 解密值**:
```json
GET /api/v1/secrets/anthropic-api-key-prod/value

Response:
{
  "secret_id": "anthropic-api-key-prod",
  "value": "sk-ant-..."  // 解密后的明文
}
```

**列出 Secrets**:
```json
GET /api/v1/secrets?type=api_key&tags=production

Response:
{
  "secrets": [
    {
      "secret_id": "anthropic-api-key-prod",
      "name": "Anthropic API Key (Production)",
      "type": "api_key",
      "tags": ["production", "anthropic"],
      "created_at": "2026-07-11T10:00:00Z"
    },
    ...
  ],
  "total": 10
}
```

**审计日志**:
```json
GET /api/v1/secrets/anthropic-api-key-prod/audit

Response:
{
  "secret_id": "anthropic-api-key-prod",
  "logs": [
    {
      "log_id": "log_xxx",
      "action": "read",
      "actor": "admin",
      "timestamp": "2026-07-11T12:00:00Z",
      "ip_address": "192.168.1.100"
    },
    {
      "action": "create",
      "actor": "admin",
      "timestamp": "2026-07-11T10:00:00Z"
    }
  ]
}
```

### 7. 安全性设计

#### 权限控制

**角色定义**:
- `secret:read`: 读取 Secret 元数据（不含解密值）
- `secret:read_value`: 读取 Secret 解密值
- `secret:create`: 创建 Secret
- `secret:update`: 更新 Secret
- `secret:delete`: 删除 Secret
- `secret:audit`: 查看审计日志

**实现**:
```python
@secrets_router.get("/secrets/{secret_id}/value")
@require_permission("secret:read_value")  # 装饰器检查权限
async def get_secret_value(secret_id: str, user: User = Depends(get_current_user)):
    secret = secret_store.get_secret(secret_id, decrypt=True)
    return {"secret_id": secret_id, "value": secret.value}
```

#### 敏感数据脱敏

**日志脱敏**:
```python
def sanitize_log(log_entry: dict) -> dict:
    """日志中脱敏敏感字段"""
    if "value" in log_entry:
        log_entry["value"] = "***REDACTED***"
    if "api_key" in log_entry:
        log_entry["api_key"] = log_entry["api_key"][:8] + "..."
    return log_entry
```

**错误消息脱敏**:
```python
try:
    secret = secret_store.get_secret(secret_id)
except Exception as e:
    # 不暴露具体错误信息
    raise HTTPException(status_code=404, detail="Secret not found")
```

#### 过期检查

```python
def get_secret(self, secret_id: str) -> Optional[Secret]:
    secret = self._query_secret(secret_id)
    
    if secret.expires_at:
        if datetime.fromisoformat(secret.expires_at) < datetime.now(timezone.utc):
            raise ValueError(f"Secret expired: {secret_id}")
    
    return secret
```

## 集成点

### 1. ModelProvider 集成

**更新 ProviderConfig.get_api_key()**:
```python
def get_api_key(self) -> Optional[str]:
    """获取 API Key（优先从 Secret Manager）"""
    # 优先级 1: api_key_ref（Secret Manager）
    if self.config.api_key_ref:
        secret_store = get_secret_store()
        secret_id = self.config.api_key_ref.replace("secret:", "")
        secret = secret_store.get_secret(secret_id, decrypt=True)
        if secret:
            return secret.value
    
    # 优先级 2: 明文 api_key（向后兼容）
    if self.config.api_key:
        return self.config.api_key
    
    return None
```

**迁移路径**:
```python
# 旧方式（明文）
provider = ModelProvider(
    provider_id="anthropic-prod",
    config=ProviderConfig(api_key="sk-ant-...")
)

# 新方式（secret_ref）
provider = ModelProvider(
    provider_id="anthropic-prod",
    config=ProviderConfig(api_key_ref="secret:anthropic-api-key-prod")
)
```

### 2. Environment 集成

```python
@dataclass
class Environment:
    environment_id: str
    name: str
    base_url: str
    secrets: Dict[str, str]  # {"admin_password": "secret:staging-admin-pw"}
    
    def resolve_secrets(self) -> Dict[str, str]:
        """解析所有 secret_ref"""
        resolved = {}
        for key, ref in self.secrets.items():
            resolved[key] = resolve_secret_ref(ref)
        return resolved
```

### 3. MCPServer 集成

```python
@dataclass
class MCPServer:
    mcp_server_id: str
    command: str
    args: List[str]
    env: Dict[str, str]  # {"SLACK_BOT_TOKEN": "secret:slack-bot-token"}
    
    def get_process_env(self) -> Dict[str, str]:
        """获取进程环境变量（解析 secret_ref）"""
        resolved_env = {}
        for key, ref in self.env.items():
            resolved_env[key] = resolve_secret_ref(ref)
        return resolved_env
```

## 迁移指南

### 从 .env 迁移到 Secret Manager

**步骤 1: 初始化 Secret Manager**
```bash
aitest secrets init
# 输出: Secret encryption key generated: governance/.data/.secret_key
```

**步骤 2: 导入现有 Secrets**
```bash
# 从 .env 文件导入
aitest secrets import --from-env .env

# 手动创建
aitest secrets create \
  --id anthropic-api-key-prod \
  --name "Anthropic API Key (Production)" \
  --type api_key \
  --value "sk-ant-..."
```

**步骤 3: 更新 ModelProvider**
```bash
# 更新配置，使用 secret_ref
aitest providers update anthropic-prod \
  --api-key-ref secret:anthropic-api-key-prod

# 或通过 REST API
curl -X PUT http://localhost:8000/api/v1/providers/anthropic-prod \
  -d '{"config": {"api_key_ref": "secret:anthropic-api-key-prod"}}'
```

**步骤 4: 验证**
```bash
# 测试 Provider 连接
aitest providers test anthropic-prod

# 运行测试 Run
aitest run create --target agent:page-observer --module login
```

**步骤 5: 清理 .env**
```bash
# 备份
cp .env .env.backup

# 删除敏感信息
sed -i '/ANTHROPIC_API_KEY/d' .env
```

### 回滚方案

如果遇到问题，可回滚到明文方式：
```bash
# 方式 1: 恢复 .env
cp .env.backup .env

# 方式 2: 更新 ModelProvider 使用明文
aitest providers update anthropic-prod --api-key "sk-ant-..."
```

## 未来扩展

### 1. Secret 版本历史

```python
class SecretVersion:
    version: int
    value: str  # 加密值
    created_at: str
    created_by: str

def get_secret_version(secret_id: str, version: int) -> SecretVersion:
    """获取指定版本的 Secret"""
    pass
```

### 2. Secret 共享

```python
def share_secret(secret_id: str, target_org_id: str, permissions: List[str]):
    """跨组织共享 Secret"""
    pass
```

### 3. Secret 自动轮换

```python
def setup_auto_rotation(secret_id: str, interval_days: int):
    """设置自动轮换（定时任务）"""
    pass
```

### 4. Secret 泄露检测

```python
def check_secret_exposure(secret_id: str) -> bool:
    """检测 Secret 是否泄露（集成 GitGuardian）"""
    pass
```

## 相关文件

- `aitest/platform/secret.py`: Secret 数据模型
- `aitest/platform/secret_models.py`: ORM 模型
- `aitest/platform/secret_store.py`: SecretStore 实现
- `aitest/infra/encryption.py`: 加密 Provider（File / Cloud）
- `aitest/server/api/secrets_v1.py`: REST API
- `aitest/cli/secrets.py`: CLI 命令
- `migrations/add_secrets_table_sqlite.sql`: 数据库迁移
- `docs/MASTER_ROADMAP.md`: P6-5 任务
