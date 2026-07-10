# Plugin 完整机制设计文档

> **创建时间**: 2026-07-11  
> **状态**: ✅ 设计完成  
> **相关任务**: P6-3 Plugin 完整机制

## 设计目标

1. **Provider 扩展** — 已支持 ✅（当前实现）
2. **Skill 扩展** — 支持 Plugin 提供自定义 Skill
3. **CLI 命令扩展** — 支持 Plugin 添加 CLI 子命令
4. **API 路由扩展** — 支持 Plugin 添加自定义 API 端点
5. **沙箱隔离** — 可选，限制 Plugin 权限（v2）
6. **签名验证** — 可选，验证 Plugin 完整性（v2）

## 当前实现分析

### 已支持功能

**文件**: `aitest/platform/plugin.py`

**核心类**:
- `PluginInfo` — Plugin 元数据
- `PluginManager` — 发现、加载、注册 Plugin

**当前支持**:
- ✅ Provider 扩展（通过 `providers` 字段）
- ✅ 自动发现（`AITEST_PLUGIN_PATH` / `<workstudy>/plugins` / `<project>/.tlo/plugins`）
- ✅ 动态加载（entry_point + import）
- ✅ 注册 API（`register_provider()`）

**限制**:
- ❌ 仅支持 Provider 扩展
- ❌ 无 Skill 扩展
- ❌ 无 CLI 命令扩展
- ❌ 无 API 路由扩展
- ❌ 无沙箱隔离
- ❌ 无签名验证

## Plugin 结构设计

### manifest 格式（v2.0）

```yaml
name: my-plugin
version: 1.0.0
description: A comprehensive plugin
author: Alice Team
homepage: https://github.com/alice/my-plugin

# Provider 扩展（已支持）
providers:
  - name: custom_browser
    class: my_plugin.providers:CustomBrowserProvider
    replaces: browser_use  # 可选：替换内置 Provider

# Skill 扩展（新增）
skills:
  - name: custom-skill
    file: skills/custom_skill.md
    description: A custom skill
    tags: [automation, custom]
  - name: another-skill
    file: skills/another.md

# CLI 命令扩展（新增）
cli_commands:
  - name: custom-cmd
    class: my_plugin.cli:CustomCommand
    description: Custom CLI command
    help: Run custom operations
  - name: deploy
    class: my_plugin.cli:DeployCommand

# API 路由扩展（新增）
api_routes:
  - prefix: /api/v1/custom
    class: my_plugin.api:CustomRouter
    description: Custom API endpoints
    tags: [custom]
  - prefix: /api/v1/integrations/slack
    class: my_plugin.api:SlackRouter

# Entry point（可选）
entry_point: my_plugin:register

# 依赖（可选）
dependencies:
  - aitest>=1.0.0
  - requests>=2.28.0

# 权限（v2，沙箱隔离）
permissions:
  - network:http  # 允许 HTTP 请求
  - filesystem:read  # 允许读取文件
  - database:write  # 允许写入数据库

# 签名（v2，验证完整性）
signature:
  algorithm: ed25519
  public_key: base64_encoded_key
  signature: base64_encoded_signature
```

### 目录结构

```
my-plugin/
├── aitest_plugin.yaml       # Plugin manifest
├── __init__.py               # Entry point
├── providers/                # Provider 扩展
│   ├── __init__.py
│   └── custom_browser.py
├── skills/                   # Skill 扩展
│   ├── custom_skill.md
│   └── another.md
├── cli/                      # CLI 命令扩展
│   ├── __init__.py
│   ├── custom_command.py
│   └── deploy_command.py
├── api/                      # API 路由扩展
│   ├── __init__.py
│   ├── custom_router.py
│   └── slack_router.py
├── tests/                    # Plugin 测试
│   └── test_plugin.py
└── README.md                 # Plugin 文档
```

## 核心组件设计

### 1. PluginInfo 扩展

```python
@dataclass
class PluginInfo:
    """Plugin 元数据（扩展版）."""
    name: str
    version: str = "0.0.0"
    description: str = ""
    author: str = ""
    homepage: str = ""
    path: Path = None
    
    # 扩展类型
    providers: list[dict] = field(default_factory=list)
    skills: list[dict] = field(default_factory=list)         # 新增
    cli_commands: list[dict] = field(default_factory=list)   # 新增
    api_routes: list[dict] = field(default_factory=list)     # 新增
    
    # 元数据
    entry_point: str = ""
    dependencies: list[str] = field(default_factory=list)    # 新增
    permissions: list[str] = field(default_factory=list)     # 新增（v2）
    signature: dict = field(default_factory=dict)            # 新增（v2）
    
    # 状态
    loaded: bool = False
    error: str = ""
```

### 2. PluginManager 扩展

```python
class PluginManager:
    """Plugin 管理器（扩展版）."""
    
    def __init__(self, search_paths: list[Path] = None):
        self._search_paths = search_paths or _default_plugin_paths()
        self._plugins: dict[str, PluginInfo] = {}
        self._providers: dict[str, type] = {}
        self._skills: dict[str, Path] = {}                # 新增
        self._cli_commands: dict[str, type] = {}          # 新增
        self._api_routes: list[tuple[str, type]] = []     # 新增
        self._lock = threading.Lock()
    
    # ── Discovery ────────────────────────────────────────────────
    
    def discover(self) -> list[PluginInfo]:
        """扫描所有搜索路径，发现 Plugin."""
        # 已实现，扩展 manifest 解析
    
    # ── Loading ──────────────────────────────────────────────────
    
    def load_all(self) -> dict[str, int]:
        """加载所有 Plugin."""
        # 已实现，扩展加载逻辑
    
    def _load_one(self, info: PluginInfo) -> int:
        """加载单个 Plugin."""
        # 扩展：加载 providers + skills + cli_commands + api_routes
    
    def _load_skills(self, info: PluginInfo) -> int:
        """加载 Skill 扩展."""
        # 新增
    
    def _load_cli_commands(self, info: PluginInfo) -> int:
        """加载 CLI 命令扩展."""
        # 新增
    
    def _load_api_routes(self, info: PluginInfo) -> int:
        """加载 API 路由扩展."""
        # 新增
    
    # ── Registration ─────────────────────────────────────────────
    
    def register_provider(self, name: str, provider_class: type):
        """注册 Provider."""
        # 已实现
    
    def register_skill(self, name: str, skill_path: Path):
        """注册 Skill."""
        # 新增
    
    def register_cli_command(self, name: str, command_class: type):
        """注册 CLI 命令."""
        # 新增
    
    def register_api_route(self, prefix: str, router_class: type):
        """注册 API 路由."""
        # 新增
    
    # ── Query ────────────────────────────────────────────────────
    
    def get_providers(self) -> dict[str, type]:
        """获取所有 Provider."""
        # 已实现
    
    def get_skills(self) -> dict[str, Path]:
        """获取所有 Skill（name → path）."""
        # 新增
    
    def get_cli_commands(self) -> dict[str, type]:
        """获取所有 CLI 命令（name → class）."""
        # 新增
    
    def get_api_routes(self) -> list[tuple[str, type]]:
        """获取所有 API 路由（[(prefix, router_class), ...]）."""
        # 新增
    
    def list_plugins(self) -> list[dict]:
        """列出所有 Plugin 状态."""
        # 已实现，扩展返回字段
```

## 集成点

### 1. Skill 扩展集成

**目标**: Plugin 提供的 Skill 自动加载到 Skill 系统

**实现**:
```python
# packages/alice-governance/alice_governance/skill_loader.py

def load_skills_from_plugins() -> dict[str, Path]:
    """从 Plugin 加载 Skill."""
    from aitest.platform.plugin import get_plugin_manager
    
    pm = get_plugin_manager()
    pm.load_all()
    
    # 获取所有 Plugin Skill
    plugin_skills = pm.get_skills()
    
    # 合并到全局 Skill 注册表
    return plugin_skills


# packages/alice-engine/alice_engine/core/skill_executor_impl.py

def _load_skill_content(skill_id: str) -> str:
    """加载 Skill 内容（优先级：Plugin > 内置）."""
    # 1. 尝试从 Plugin 加载
    plugin_skills = load_skills_from_plugins()
    if skill_id in plugin_skills:
        skill_path = plugin_skills[skill_id]
        return skill_path.read_text(encoding="utf-8")
    
    # 2. 回退到内置 Skill
    return _load_builtin_skill(skill_id)
```

**manifest 示例**:
```yaml
skills:
  - name: custom-browser-automation
    file: skills/custom_browser_automation.md
    description: Custom browser automation skill
    tags: [automation, browser]
    version: "1.0.0"
```

**Skill 文件示例** (`skills/custom_browser_automation.md`):
```markdown
---
id: custom-browser-automation
name: Custom Browser Automation
version: 1.0.0
tags: [automation, browser]
---

# Custom Browser Automation Skill

This skill provides custom browser automation capabilities.

## Usage

Use this skill when you need to...

## Tools

- `browser_navigate(url: str)` — Navigate to URL
- `browser_click(selector: str)` — Click element

## Examples

...
```

### 2. CLI 命令扩展集成

**目标**: Plugin 提供的 CLI 命令自动注册到 `aitest` CLI

**实现**:
```python
# aitest/cli/main.py

import click
from aitest.platform.plugin import get_plugin_manager

@click.group()
def cli():
    """AITest CLI."""
    pass

def register_plugin_commands():
    """注册 Plugin 提供的 CLI 命令."""
    pm = get_plugin_manager()
    pm.load_all()
    
    for cmd_name, cmd_class in pm.get_cli_commands().items():
        # 动态注册 Click 命令
        cli.add_command(cmd_class.create_command(), name=cmd_name)

# 在 CLI 启动时自动注册
register_plugin_commands()

if __name__ == "__main__":
    cli()
```

**Plugin CLI 命令示例**:
```python
# my_plugin/cli/custom_command.py

import click

class CustomCommand:
    """Custom CLI command."""
    
    @staticmethod
    def create_command():
        """创建 Click 命令."""
        @click.command()
        @click.option("--verbose", is_flag=True, help="Verbose output")
        def custom_cmd(verbose: bool):
            """Run custom operations."""
            click.echo("Running custom command...")
            if verbose:
                click.echo("Verbose mode enabled")
        
        return custom_cmd
```

**manifest 示例**:
```yaml
cli_commands:
  - name: custom
    class: my_plugin.cli:CustomCommand
    description: Custom CLI command
  - name: deploy
    class: my_plugin.cli:DeployCommand
    description: Deploy to production
```

### 3. API 路由扩展集成

**目标**: Plugin 提供的 API 路由自动注册到 FastAPI

**实现**:
```python
# aitest/server/main.py

from fastapi import FastAPI
from aitest.platform.plugin import get_plugin_manager

app = FastAPI()

def register_plugin_routes():
    """注册 Plugin 提供的 API 路由."""
    pm = get_plugin_manager()
    pm.load_all()
    
    for prefix, router_class in pm.get_api_routes():
        # 实例化 Router
        router = router_class().create_router()
        
        # 注册到 FastAPI
        app.include_router(router, prefix=prefix)

# 在启动时自动注册
register_plugin_routes()
```

**Plugin API 路由示例**:
```python
# my_plugin/api/custom_router.py

from fastapi import APIRouter

class CustomRouter:
    """Custom API router."""
    
    def create_router(self) -> APIRouter:
        """创建 FastAPI Router."""
        router = APIRouter(tags=["custom"])
        
        @router.get("/hello")
        async def hello():
            """Hello endpoint."""
            return {"message": "Hello from plugin!"}
        
        @router.post("/process")
        async def process(data: dict):
            """Process data."""
            return {"result": "processed", "data": data}
        
        return router
```

**manifest 示例**:
```yaml
api_routes:
  - prefix: /api/v1/custom
    class: my_plugin.api:CustomRouter
    description: Custom API endpoints
    tags: [custom]
```

## 沙箱隔离设计（v2）

### 权限模型

```yaml
permissions:
  - network:http              # 允许 HTTP 请求
  - network:https             # 允许 HTTPS 请求
  - filesystem:read:/tmp      # 允许读取 /tmp
  - filesystem:write:/output  # 允许写入 /output
  - database:read             # 允许读取数据库
  - database:write            # 允许写入数据库
  - env:read                  # 允许读取环境变量
  - process:spawn             # 允许启动子进程
```

### 沙箱实现

```python
class PluginSandbox:
    """Plugin 沙箱（限制权限）."""
    
    def __init__(self, permissions: list[str]):
        self.permissions = self._parse_permissions(permissions)
    
    def _parse_permissions(self, perms: list[str]) -> dict:
        """解析权限列表."""
        # network:http → {"network": ["http"]}
        # filesystem:read:/tmp → {"filesystem": {"read": ["/tmp"]}}
    
    def check_permission(self, action: str, resource: str = None) -> bool:
        """检查是否有权限执行操作."""
        # 例如: check_permission("network:http")
        # 例如: check_permission("filesystem:read", "/tmp/file.txt")
    
    def wrap_module(self, module):
        """包装模块，拦截危险操作."""
        # 拦截 open(), requests.get(), subprocess.run() 等
        # 在调用前检查权限
```

### 使用示例

```python
# Plugin 加载时创建沙箱
sandbox = PluginSandbox(info.permissions)

# 在沙箱中执行 Plugin 代码
with sandbox:
    # Plugin 的所有操作都受限制
    plugin_module = importlib.import_module(module_name)
    plugin_module.register(pm)
```

## 签名验证设计（v2）

### 签名流程

1. **Plugin 开发者签名**:
```bash
# 使用私钥签名 Plugin
aitest plugin sign my-plugin/ --key private.pem
# → 生成 aitest_plugin.yaml 中的 signature 字段
```

2. **AITest 验证签名**:
```python
def verify_signature(info: PluginInfo) -> bool:
    """验证 Plugin 签名."""
    sig_data = info.signature
    
    if not sig_data:
        # 无签名，跳过验证（开发模式）
        return True
    
    algorithm = sig_data.get("algorithm")  # "ed25519"
    public_key = sig_data.get("public_key")  # base64
    signature = sig_data.get("signature")  # base64
    
    # 计算 Plugin 文件哈希
    plugin_hash = _compute_plugin_hash(info.path)
    
    # 验证签名
    return _verify_ed25519(plugin_hash, public_key, signature)
```

### manifest 示例

```yaml
signature:
  algorithm: ed25519
  public_key: "base64_encoded_public_key"
  signature: "base64_encoded_signature_of_plugin_hash"
```

## 向后兼容

1. **manifest v1.0 → v2.0**:
   - v1.0: 仅支持 `providers`
   - v2.0: 支持 `providers` + `skills` + `cli_commands` + `api_routes`
   - 自动识别版本（通过字段存在判断）

2. **权限和签名可选**:
   - 无 `permissions` 字段 → 无沙箱隔离（v1 行为）
   - 无 `signature` 字段 → 无签名验证（开发模式）

3. **现有 Plugin 无需修改**:
   - 现有 Plugin 仅使用 `providers`，继续工作

## 相关文件

- `aitest/platform/plugin.py` — PluginManager 核心实现
- `aitest/platform/plugin_sandbox.py` — 沙箱隔离（v2）
- `aitest/platform/plugin_signature.py` — 签名验证（v2）
- `aitest/tests/integration/test_plugin_system.py` — 测试
- `docs/plugin_system_design.md` — 本设计文档
- `docs/MASTER_ROADMAP.md` — P6-3 任务
