# MCP Server 资源化设计文档

> **创建时间**: 2026-07-11  
> **状态**: ✅ 设计完成  
> **相关任务**: P6-2 MCP Server 资源化

## 设计目标

1. **动态管理**: 从硬编码 registry.py 升级为数据库资源
2. **进程管理**: 启动/停止/监控 MCP Server 进程
3. **Environment 集成**: MCP Server 环境变量引用 Environment/Secret
4. **Tool 注册**: 动态加载 MCP Tools 到平台
5. **健康检查**: 监控 MCP Server 状态，自动重启

## 当前实现分析

### 现有架构

**文件**:
- `aitest/mcp/mcp_client.py` — MCP 客户端实现
- `aitest/mcp/registry.py` — 硬编码的 MCP Server 配置

**当前配置方式**（硬编码）:
```python
MCP_SERVER_REGISTRY: dict[str, McpServerConfig] = {
    "browser-mcp": McpServerConfig(
        id="browser-mcp",
        name="Browser MCP",
        description="Playwright browser automation",
        transport_type="stdio",
        command="npx",
        args=["-y", "@anthropic-ai/playwright-mcp-server"],
    ),
}
```

**问题**:
1. 无法动态添加/删除 MCP Server
2. 配置变更需要修改代码重启服务
3. 无法管理 MCP Server 进程生命周期
4. 环境变量硬编码，无法引用 Secret

## 资源化架构

### 1. MCPServer 数据模型

```python
@dataclass
class MCPServer:
    mcp_server_id: str              # 唯一标识（如 "slack-connector"）
    name: str                       # 显示名称
    description: str                # 描述信息
    transport_type: str             # "stdio" | "http"
    command: str                    # stdio: 启动命令（如 "npx"）
    args: List[str]                 # stdio: 命令参数
    url: str                        # http: MCP Server URL
    env: Dict[str, str]             # 环境变量（可包含 secret_ref / environment_ref）
    tools: List[str]                # 暴露的 Tools（从 MCP Server 动态获取）
    status: str                     # "stopped" | "starting" | "running" | "error"
    process_id: Optional[int]       # 进程 ID（stdio 类型）
    org_id: str                     # 组织 ID
    created_by: str                 # 创建者
    created_at: str                 # 创建时间
    updated_at: str                 # 更新时间
    last_health_check: Optional[str] # 最后健康检查时间
```

### 2. 数据库表设计

```sql
CREATE TABLE mcp_servers (
    mcp_server_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    transport_type TEXT NOT NULL,     -- "stdio" | "http"
    command TEXT DEFAULT '',           -- stdio: 启动命令
    args TEXT DEFAULT '[]',            -- stdio: 命令参数（JSON 数组）
    url TEXT DEFAULT '',               -- http: MCP Server URL
    env TEXT DEFAULT '{}',             -- 环境变量（JSON 对象）
    tools TEXT DEFAULT '[]',           -- 暴露的 Tools（JSON 数组）
    status TEXT DEFAULT 'stopped',     -- "stopped" | "starting" | "running" | "error"
    process_id INTEGER DEFAULT NULL,   -- 进程 ID
    org_id TEXT NOT NULL DEFAULT 'default-org',
    created_by TEXT NOT NULL DEFAULT 'admin',
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    last_health_check TIMESTAMP,
    
    INDEX idx_mcp_servers_org_id (org_id),
    INDEX idx_mcp_servers_status (status)
);
```

### 3. MCPServer 配置示例

```json
{
  "mcp_server_id": "slack-connector",
  "name": "Slack MCP Server",
  "description": "Slack integration via MCP",
  "transport_type": "stdio",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-slack"],
  "env": {
    "SLACK_BOT_TOKEN": "secret:slack-bot-token",        // 引用 Secret
    "SLACK_WORKSPACE": "environment:SLACK_WORKSPACE"    // 引用 Environment 变量
  },
  "tools": [
    "slack_list_channels",
    "slack_post_message",
    "slack_get_channel_history"
  ],
  "status": "running",
  "process_id": 12345
}
```

## 核心组件

### 1. MCPServerManager（进程管理）

```python
class MCPServerManager:
    """MCP Server 进程管理器"""
    
    def __init__(self):
        self.processes: Dict[str, subprocess.Popen] = {}
        self.clients: Dict[str, McpClientResult] = {}
    
    async def start_server(self, mcp_server: MCPServer) -> bool:
        """启动 MCP Server
        
        1. 解析环境变量（secret_ref / environment_ref）
        2. 启动进程（stdio）或连接 URL（http）
        3. 健康检查（调用 list_tools 验证）
        4. 更新状态和 process_id
        """
    
    async def stop_server(self, mcp_server_id: str) -> bool:
        """停止 MCP Server
        
        1. 关闭 MCP 客户端连接
        2. 终止进程（stdio）
        3. 更新状态为 "stopped"
        """
    
    async def restart_server(self, mcp_server_id: str) -> bool:
        """重启 MCP Server"""
    
    async def get_status(self, mcp_server_id: str) -> Dict:
        """获取 MCP Server 状态
        
        Returns:
            {
                "status": "running",
                "process_id": 12345,
                "tools": ["tool1", "tool2"],
                "last_health_check": "2026-07-11T15:00:00Z"
            }
        """
    
    async def health_check(self, mcp_server_id: str) -> bool:
        """健康检查
        
        1. 调用 MCP Server 的 list_tools
        2. 如果失败，标记为 "error"
        3. 如果连续 3 次失败，自动重启
        """
    
    async def list_tools(self, mcp_server_id: str) -> List[str]:
        """列出 MCP Server 暴露的 Tools"""
```

### 2. MCPServerStore（CRUD）

```python
class MCPServerStore:
    def create_mcp_server(
        self,
        mcp_server_id: str,
        name: str,
        transport_type: str,
        command: str = "",
        args: List[str] = None,
        url: str = "",
        env: Dict[str, str] = None,
        description: str = "",
        org_id: str = "default-org",
        created_by: str = "admin",
    ) -> MCPServer:
        """创建 MCP Server（不启动进程）"""
    
    def get_mcp_server(self, mcp_server_id: str) -> Optional[MCPServer]:
        """获取 MCP Server"""
    
    def list_mcp_servers(
        self,
        org_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[MCPServer]:
        """列出 MCP Servers"""
    
    def update_mcp_server(
        self,
        mcp_server_id: str,
        name: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        # ... 其他字段
    ) -> MCPServer:
        """更新 MCP Server"""
    
    def delete_mcp_server(self, mcp_server_id: str) -> bool:
        """删除 MCP Server（先停止进程）"""
    
    def update_status(
        self,
        mcp_server_id: str,
        status: str,
        process_id: Optional[int] = None,
    ):
        """更新状态"""
    
    def update_tools(self, mcp_server_id: str, tools: List[str]):
        """更新 Tools 列表（从 MCP Server 动态获取）"""
    
    def resolve_env(self, mcp_server_id: str) -> Dict[str, str]:
        """解析环境变量（自动解析 secret_ref / environment_ref）
        
        示例:
            env = {
                "SLACK_BOT_TOKEN": "secret:slack-bot-token",
                "WORKSPACE": "environment:SLACK_WORKSPACE"
            }
            
            resolved = {
                "SLACK_BOT_TOKEN": "xoxb-actual-token",
                "WORKSPACE": "my-workspace"
            }
        """
```

### 3. REST API

#### 端点列表

```
POST   /api/v1/mcp-servers              # 创建 MCP Server
GET    /api/v1/mcp-servers              # 列出 MCP Servers
GET    /api/v1/mcp-servers/:id          # 获取 MCP Server
PUT    /api/v1/mcp-servers/:id          # 更新 MCP Server
DELETE /api/v1/mcp-servers/:id          # 删除 MCP Server
POST   /api/v1/mcp-servers/:id/start    # 启动 MCP Server
POST   /api/v1/mcp-servers/:id/stop     # 停止 MCP Server
POST   /api/v1/mcp-servers/:id/restart  # 重启 MCP Server
GET    /api/v1/mcp-servers/:id/status   # 获取状态
GET    /api/v1/mcp-servers/:id/tools    # 列出 Tools
POST   /api/v1/mcp-servers/:id/health   # 手动健康检查
```

#### 请求/响应示例

**创建 MCP Server**:
```json
POST /api/v1/mcp-servers
{
  "mcp_server_id": "slack-connector",
  "name": "Slack MCP Server",
  "transport_type": "stdio",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-slack"],
  "env": {
    "SLACK_BOT_TOKEN": "secret:slack-bot-token"
  },
  "description": "Slack integration"
}

Response:
{
  "mcp_server_id": "slack-connector",
  "name": "Slack MCP Server",
  "status": "stopped",
  "created_at": "2026-07-11T15:00:00Z"
}
```

**启动 MCP Server**:
```json
POST /api/v1/mcp-servers/slack-connector/start

Response:
{
  "success": true,
  "mcp_server_id": "slack-connector",
  "status": "running",
  "process_id": 12345,
  "tools": ["slack_list_channels", "slack_post_message"]
}
```

**获取状态**:
```json
GET /api/v1/mcp-servers/slack-connector/status

Response:
{
  "mcp_server_id": "slack-connector",
  "status": "running",
  "process_id": 12345,
  "tools": ["slack_list_channels", "slack_post_message"],
  "last_health_check": "2026-07-11T15:30:00Z",
  "uptime_seconds": 1800
}
```

## 集成点

### 1. 引用 Secret

```python
# MCPServer 配置
{
  "env": {
    "SLACK_BOT_TOKEN": "secret:slack-bot-token",
    "API_KEY": "secret:api-key"
  }
}

# MCPServerStore.resolve_env()
def resolve_env(self, mcp_server_id: str) -> Dict[str, str]:
    server = self.get_mcp_server(mcp_server_id)
    resolved = {}
    for key, value in server.env.items():
        if value.startswith("secret:"):
            # 解析 Secret
            resolved[key] = resolve_secret_ref(value)
        elif value.startswith("environment:"):
            # 解析 Environment 变量
            env_var = value[12:]  # 去掉 "environment:" 前缀
            resolved[key] = get_environment_variable(env_var)
        else:
            resolved[key] = value
    return resolved
```

### 2. 引用 Environment

```python
# MCPServer 配置
{
  "env": {
    "DB_HOST": "environment:DB_HOST",        // 从 Environment 获取
    "DB_PASSWORD": "secret:db-password"       // 从 Secret 获取
  }
}

# 解析逻辑
def get_environment_variable(var_name: str) -> str:
    """从当前 Environment 获取变量"""
    # 假设有当前 Environment 上下文
    current_env = get_current_environment()
    if current_env:
        resolved_vars = environment_store.resolve_variables(current_env.environment_id)
        return resolved_vars.get(var_name, "")
    return os.getenv(var_name, "")
```

### 3. 集成到 Tool 系统

**动态加载 MCP Tools**:
```python
# Agent 执行时
async def execute_agent(agent_id: str, context: ExecutionContext):
    # 1. 获取 Agent 关联的 MCP Servers
    mcp_servers = get_agent_mcp_servers(agent_id)
    
    # 2. 确保 MCP Servers 已启动
    for server_id in mcp_servers:
        manager = get_mcp_server_manager()
        if not await manager.is_running(server_id):
            await manager.start_server(server_id)
    
    # 3. 加载 MCP Tools
    tools = []
    for server_id in mcp_servers:
        mcp_tools = await manager.list_tools(server_id)
        tools.extend(mcp_tools)
    
    # 4. 执行 Agent（tools 可用）
    result = await agent_loop.run(agent_id, tools=tools, context=context)
```

**Tool 调用**:
```python
# LLM 调用 Tool 时
async def call_tool(tool_name: str, arguments: dict):
    # 1. 查找 Tool 属于哪个 MCP Server
    server_id = find_mcp_server_by_tool(tool_name)
    
    # 2. 调用 MCP Server Tool
    manager = get_mcp_server_manager()
    result = await manager.call_tool(server_id, tool_name, arguments)
    
    return result
```

## 迁移路径

### 从硬编码 registry.py 迁移

**步骤 1: 导入现有配置**:
```python
# 脚本: migrate_mcp_registry.py
from aitest.mcp.registry import MCP_SERVER_REGISTRY
from aitest.platform.mcp_server_store import MCPServerStore

store = MCPServerStore(session)

for server_id, config in MCP_SERVER_REGISTRY.items():
    store.create_mcp_server(
        mcp_server_id=config.id,
        name=config.name,
        transport_type=config.transport_type,
        command=config.command,
        args=config.args,
        url=config.url,
        env=config.env,
        description=config.description,
    )
```

**步骤 2: 更新 mcp_client.py**:
```python
# 旧方式（从 registry.py 加载）
def _get_registry() -> dict[str, McpServerConfig]:
    from aitest.mcp.registry import MCP_SERVER_REGISTRY
    return MCP_SERVER_REGISTRY

# 新方式（从数据库加载）
def _get_registry() -> dict[str, McpServerConfig]:
    from aitest.platform.mcp_server_store import MCPServerStore
    store = MCPServerStore(get_session())
    servers = store.list_mcp_servers()
    return {s.mcp_server_id: s.to_config() for s in servers}
```

## 进程管理设计

### 启动流程

```python
async def start_server(self, mcp_server: MCPServer) -> bool:
    # 1. 更新状态为 "starting"
    store.update_status(mcp_server.mcp_server_id, "starting")
    
    # 2. 解析环境变量
    resolved_env = store.resolve_env(mcp_server.mcp_server_id)
    
    # 3. 启动进程（stdio）
    if mcp_server.transport_type == "stdio":
        process = subprocess.Popen(
            [mcp_server.command] + mcp_server.args,
            env=resolved_env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.processes[mcp_server.mcp_server_id] = process
        store.update_status(mcp_server.mcp_server_id, "running", process.pid)
    
    # 4. 连接 MCP 客户端
    config = mcp_server.to_config()
    client = await create_mcp_client(config)
    self.clients[mcp_server.mcp_server_id] = client
    
    # 5. 列出 Tools
    tools = list(client.tools.keys())
    store.update_tools(mcp_server.mcp_server_id, tools)
    
    return True
```

### 健康检查

```python
async def health_check_loop():
    """后台任务：定期健康检查所有 running 状态的 MCP Servers"""
    while True:
        servers = store.list_mcp_servers(status="running")
        for server in servers:
            try:
                # 调用 list_tools 验证连接
                tools = await manager.list_tools(server.mcp_server_id)
                store.update_last_health_check(server.mcp_server_id)
            except Exception as e:
                logger.warning(f"Health check failed for {server.mcp_server_id}: {e}")
                # 连续失败 3 次，自动重启
                failure_count = get_failure_count(server.mcp_server_id)
                if failure_count >= 3:
                    await manager.restart_server(server.mcp_server_id)
        
        await asyncio.sleep(60)  # 每分钟检查一次
```

## 未来扩展

### 1. MCP Server 版本管理

```python
# 支持多版本
{
  "mcp_server_id": "slack-connector-v2",
  "version": "2.0.0",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-slack@2.0.0"]
}
```

### 2. Tool 权限控制

```python
# 限制 Agent 可用的 Tools
{
  "agent_mcp_mappings": [
    {
      "agent_id": "qa-reviewer",
      "mcp_server_id": "slack-connector",
      "allowed_tools": ["slack_list_channels", "slack_post_message"]  // 只允许这两个
    }
  ]
}
```

### 3. MCP Server 监控

```python
# 收集指标
{
  "metrics": {
    "total_calls": 1000,
    "success_rate": 0.95,
    "avg_response_time_ms": 150,
    "error_count": 50
  }
}
```

## 相关文件

- `aitest/platform/mcp_server.py`: MCPServer 数据模型
- `aitest/platform/mcp_server_models.py`: ORM 模型
- `aitest/platform/mcp_server_store.py`: MCPServerStore CRUD
- `aitest/platform/mcp_server_manager.py`: 进程管理
- `aitest/server/api/mcp_servers_v1.py`: REST API
- `migrations/add_mcp_servers_table_sqlite.sql`: 数据库迁移
- `tests/test_mcp_server.py`: 完整测试
- `docs/MASTER_ROADMAP.md`: P6-2 任务
