# Environment 资源化设计文档

> **创建时间**: 2026-07-11  
> **状态**: ✅ 设计完成  
> **相关任务**: P6-4 Environment 资源化

## 设计目标

1. **多环境支持**: dev/staging/prod 独立配置
2. **统一管理**: 集中管理环境配置（base_url、secrets、变量）
3. **引用 Secret**: 通过 secret_ref 引用敏感信息
4. **Run 关联**: Run 执行时自动应用 Environment 配置
5. **向后兼容**: 现有代码无需修改，支持 fallback

## 架构概览

```
Environment
  ├── Environment (数据模型)
  ├── EnvironmentStore (CRUD)
  ├── REST API (/api/v1/environments)
  └── Integration (Run 执行时应用配置)
```

## 核心组件

### 1. Environment 数据模型

```python
@dataclass
class Environment:
    environment_id: str         # 唯一标识（如 "staging", "production"）
    name: str                   # 显示名称（如 "Staging Environment"）
    base_url: str               # 测试环境 URL
    description: str            # 描述信息
    variables: Dict[str, str]   # 环境变量（可包含 secret_ref）
    tags: List[str]             # 标签（如 ["staging", "web"]）
    org_id: str                 # 组织 ID
    created_by: str             # 创建者
    created_at: str             # 创建时间
    updated_at: str             # 更新时间
    is_default: bool            # 是否默认环境
```

### 2. 数据库表设计

```sql
CREATE TABLE environments (
    environment_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    base_url TEXT NOT NULL,
    description TEXT DEFAULT '',
    variables TEXT DEFAULT '{}',     -- JSON 对象
    tags TEXT DEFAULT '[]',          -- JSON 数组
    org_id TEXT NOT NULL DEFAULT 'default-org',
    created_by TEXT NOT NULL DEFAULT 'admin',
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    is_default BOOLEAN DEFAULT FALSE,
    
    INDEX idx_environments_org_id (org_id),
    INDEX idx_environments_is_default (is_default)
);
```

### 3. Environment 配置示例

```json
{
  "environment_id": "staging",
  "name": "Staging Environment",
  "base_url": "https://staging.example.com",
  "description": "Staging environment for QA testing",
  "variables": {
    "DB_HOST": "staging-db.example.com",
    "DB_PORT": "5432",
    "DB_NAME": "aitest_staging",
    "DB_PASSWORD": "secret:staging-db-password",  // 引用 Secret
    "ADMIN_TOKEN": "secret:staging-admin-token",
    "API_TIMEOUT": "30",
    "DEBUG_MODE": "true"
  },
  "tags": ["staging", "qa"],
  "is_default": false
}
```

### 4. EnvironmentStore 接口

```python
class EnvironmentStore:
    def create_environment(
        self,
        environment_id: str,
        name: str,
        base_url: str,
        description: str = "",
        variables: Dict[str, str] = None,
        tags: List[str] = None,
        org_id: str = "default-org",
        created_by: str = "admin",
        is_default: bool = False,
    ) -> Environment:
        """创建 Environment"""
    
    def get_environment(self, environment_id: str) -> Optional[Environment]:
        """获取 Environment"""
    
    def list_environments(
        self,
        org_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> List[Environment]:
        """列出 Environments"""
    
    def update_environment(
        self,
        environment_id: str,
        name: Optional[str] = None,
        base_url: Optional[str] = None,
        description: Optional[str] = None,
        variables: Optional[Dict[str, str]] = None,
        tags: Optional[List[str]] = None,
        is_default: Optional[bool] = None,
    ) -> Environment:
        """更新 Environment"""
    
    def delete_environment(self, environment_id: str) -> bool:
        """删除 Environment"""
    
    def get_default_environment(self, org_id: str = "default-org") -> Optional[Environment]:
        """获取默认 Environment"""
    
    def set_default_environment(self, environment_id: str, org_id: str = "default-org"):
        """设置默认 Environment（取消其他默认）"""
    
    def resolve_variables(self, environment_id: str) -> Dict[str, str]:
        """解析 Environment 变量（自动解析 secret_ref）"""
```

### 5. REST API

#### 端点列表

```
POST   /api/v1/environments              # 创建 Environment
GET    /api/v1/environments              # 列出 Environments
GET    /api/v1/environments/:id          # 获取 Environment
PUT    /api/v1/environments/:id          # 更新 Environment
DELETE /api/v1/environments/:id          # 删除 Environment
POST   /api/v1/environments/:id/default  # 设置为默认
GET    /api/v1/environments/:id/resolved # 获取解析后的变量（包含解密值）
```

#### 请求/响应示例

**创建 Environment**:
```json
POST /api/v1/environments
{
  "environment_id": "staging",
  "name": "Staging Environment",
  "base_url": "https://staging.example.com",
  "description": "Staging environment for QA testing",
  "variables": {
    "DB_HOST": "staging-db.example.com",
    "DB_PASSWORD": "secret:staging-db-password",
    "API_TIMEOUT": "30"
  },
  "tags": ["staging", "qa"]
}

Response:
{
  "environment_id": "staging",
  "name": "Staging Environment",
  "base_url": "https://staging.example.com",
  "variables": {
    "DB_HOST": "staging-db.example.com",
    "DB_PASSWORD": "secret:staging-db-password",  // 不解密
    "API_TIMEOUT": "30"
  },
  "created_at": "2026-07-11T14:00:00Z"
}
```

**获取解析后的变量**:
```json
GET /api/v1/environments/staging/resolved

Response:
{
  "environment_id": "staging",
  "variables": {
    "DB_HOST": "staging-db.example.com",
    "DB_PASSWORD": "actual-password-value",  // 已解密
    "API_TIMEOUT": "30"
  }
}
```

**列出 Environments**:
```json
GET /api/v1/environments?org_id=default-org

Response:
{
  "environments": [
    {
      "environment_id": "production",
      "name": "Production",
      "base_url": "https://prod.example.com",
      "is_default": true,
      "tags": ["production"]
    },
    {
      "environment_id": "staging",
      "name": "Staging",
      "base_url": "https://staging.example.com",
      "is_default": false,
      "tags": ["staging", "qa"]
    }
  ]
}
```

## 集成点

### 1. Run 执行时应用 Environment

**RunModel 新增字段**:
```python
class RunModel(Base):
    # ... 现有字段 ...
    
    # P6-4: Environment 关联（可选，向后兼容）
    environment_id = Column(String(64), nullable=True, default=None)
```

**数据库迁移**:
```sql
ALTER TABLE runs ADD COLUMN environment_id TEXT DEFAULT NULL;
```

**Run 执行流程**:
```python
# 1. 创建 Run
run_id = create_run(
    workspace_id="ws_xxx",
    agent="page-observer",
    module="login",
    environment_id="staging"  # 指定 Environment
)

# 2. 执行 Run
executor = RunExecutor(run_id)
executor.execute()

# 内部流程:
# a. 加载 Environment
env = environment_store.get_environment("staging")

# b. 解析变量（自动解密 secret_ref）
resolved_vars = environment_store.resolve_variables("staging")
# {"DB_HOST": "...", "DB_PASSWORD": "actual-password", ...}

# c. 应用到执行上下文
execution_context.base_url = env.base_url
execution_context.env_variables = resolved_vars

# d. 执行 Agent
agent_result = execute_agent(context=execution_context)
```

### 2. ExecutionContext 更新

```python
@dataclass
class ExecutionContext:
    run_id: str
    workspace_id: str
    agent_id: str
    module: str
    pages: List[str]
    
    # P6-4: Environment 配置
    environment_id: Optional[str] = None
    base_url: Optional[str] = None
    env_variables: Dict[str, str] = field(default_factory=dict)
    
    def get_base_url(self) -> str:
        """获取 base_url（优先级: base_url > Environment > 默认值）"""
        if self.base_url:
            return self.base_url
        if self.environment_id:
            env = get_environment_store().get_environment(self.environment_id)
            if env:
                return env.base_url
        return "https://default.example.com"
    
    def get_env_variable(self, key: str, default: str = None) -> Optional[str]:
        """获取环境变量（自动解析 secret_ref）"""
        if key in self.env_variables:
            return self.env_variables[key]
        return default
```

### 3. 向后兼容

**优先级链**:
```
1. 显式传入的 base_url/变量（最高优先级）
   ↓ fallback
2. environment_id 关联的 Environment
   ↓ fallback
3. 默认值或环境变量
```

**示例**:
```python
# 方式 1: 使用 Environment（新方式）
run = create_run(
    agent="page-observer",
    module="login",
    environment_id="staging"  # 自动应用 staging 配置
)

# 方式 2: 显式传入（旧方式，向后兼容）
run = create_run(
    agent="page-observer",
    module="login",
    base_url="https://custom.example.com"  # 覆盖 Environment
)

# 方式 3: 都不提供（fallback 到默认值）
run = create_run(
    agent="page-observer",
    module="login"
)
```

## 使用场景

### 场景 1: 多环境测试

```python
# 创建多个 Environment
staging_env = environment_store.create_environment(
    environment_id="staging",
    name="Staging",
    base_url="https://staging.example.com",
    variables={"DB_HOST": "staging-db", "DB_PASSWORD": "secret:staging-db-pw"}
)

prod_env = environment_store.create_environment(
    environment_id="production",
    name="Production",
    base_url="https://prod.example.com",
    variables={"DB_HOST": "prod-db", "DB_PASSWORD": "secret:prod-db-pw"}
)

# 在不同环境执行测试
run_staging = create_run(module="login", environment_id="staging")
run_prod = create_run(module="login", environment_id="production")
```

### 场景 2: CI/CD 集成

```bash
# CI Pipeline
# Stage 1: 在 staging 环境测试
aitest run create --module login --environment staging

# Stage 2: 测试通过后，在 production 环境回归
aitest run create --module login --environment production
```

### 场景 3: 本地开发 vs 远程测试

```python
# 本地开发环境
local_env = environment_store.create_environment(
    environment_id="local",
    name="Local Development",
    base_url="http://localhost:3000",
    variables={"DEBUG_MODE": "true"}
)

# 远程测试环境
remote_env = environment_store.create_environment(
    environment_id="remote",
    name="Remote Testing",
    base_url="https://test.example.com",
    variables={"DEBUG_MODE": "false"}
)
```

## 安全性设计

### 1. Secret 引用

Environment 中的敏感变量使用 secret_ref：

```json
{
  "variables": {
    "DB_PASSWORD": "secret:staging-db-password",  // 引用 Secret
    "API_KEY": "secret:staging-api-key",
    "PUBLIC_CONFIG": "plain-text-value"  // 非敏感信息可明文
  }
}
```

**自动解析**:
```python
# 获取 Environment 配置
env = environment_store.get_environment("staging")
# variables: {"DB_PASSWORD": "secret:staging-db-password", ...}

# 解析变量（自动解密）
resolved = environment_store.resolve_variables("staging")
# {"DB_PASSWORD": "actual-password", ...}
```

### 2. 权限控制

**角色定义**（未来实现）:
- `environment:read`: 读取 Environment 配置
- `environment:read_resolved`: 读取解析后的变量（包含解密值）
- `environment:create`: 创建 Environment
- `environment:update`: 更新 Environment
- `environment:delete`: 删除 Environment

### 3. 审计日志

Environment 的创建/更新/删除操作应记录审计日志（未来扩展）。

## 迁移指南

### 从硬编码配置迁移

**当前方式**（硬编码）:
```python
# 测试代码中硬编码
base_url = "https://staging.example.com"
db_host = "staging-db.example.com"
```

**新方式**（Environment 资源化）:
```python
# 1. 创建 Environment
environment_store.create_environment(
    environment_id="staging",
    base_url="https://staging.example.com",
    variables={"DB_HOST": "staging-db.example.com"}
)

# 2. Run 执行时指定 Environment
run = create_run(module="login", environment_id="staging")
```

### 从 project.yaml 迁移

**当前 project.yaml**:
```yaml
connection:
  base_url: https://example.com
  timeout: 30
```

**新方式**（Environment 资源化）:
```python
environment_store.create_environment(
    environment_id="default",
    base_url="https://example.com",
    variables={"TIMEOUT": "30"},
    is_default=True
)
```

## 未来扩展

### 1. Environment 继承

```python
# 基础环境
base_env = Environment(
    environment_id="base",
    variables={"TIMEOUT": "30", "RETRY": "3"}
)

# 继承基础环境
staging_env = Environment(
    environment_id="staging",
    parent_id="base",  # 继承 base
    variables={"DB_HOST": "staging-db"}  # 覆盖/新增变量
)
# 最终: {"TIMEOUT": "30", "RETRY": "3", "DB_HOST": "staging-db"}
```

### 2. Environment 版本历史

```python
# 保留历史版本
environment_store.create_version(
    environment_id="staging",
    version="v1.2.0",
    variables={...}
)

# 回滚到指定版本
environment_store.rollback(
    environment_id="staging",
    version="v1.1.0"
)
```

### 3. Environment 变量校验

```python
# 定义 schema
schema = {
    "DB_HOST": {"type": "string", "required": True},
    "DB_PORT": {"type": "integer", "default": 5432},
    "DB_PASSWORD": {"type": "secret_ref", "required": True}
}

# 校验 Environment
environment_store.validate(environment_id="staging", schema=schema)
```

## 相关文件

- `aitest/platform/environment.py`: Environment 数据模型
- `aitest/platform/environment_models.py`: ORM 模型
- `aitest/platform/environment_store.py`: EnvironmentStore 实现
- `aitest/server/api/environments_v1.py`: REST API
- `aitest/infra/models.py`: RunModel.environment_id 字段
- `migrations/add_environments_table_sqlite.sql`: 数据库迁移
- `migrations/add_run_environment_id_sqlite.sql`: Run 表迁移
- `tests/test_environment.py`: 完整测试
- `docs/MASTER_ROADMAP.md`: P6-4 任务
