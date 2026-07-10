# P2-4: Init 向导改进设计

> **任务**: P2-4: Init 向导改进  
> **目标**: 优化 `aitest init` 交互式项目初始化体验  
> **日期**: 2026-07-11

---

## 当前实现分析

### 现有功能（aitest/cli/commands/project/init.py）

**交互式信息收集**:
- 项目名称
- 技术栈（5 个预设 + 自定义）
- 目标 URL
- 环境类型（dev/staging/prod）
- 登录信息（form/api/sso + 测试账号）
- 测试框架（pytest-selenium/playwright/cypress）
- 模块列表

**生成文件**:
- `.tlo/project.yaml` — 项目配置
- `.tlo/context/test_accounts.yaml` — 测试账号
- `.tlo/knowledge/modules/<module>/` — 模块目录结构
- `.tlo/runtime/sop-status/` — 运行时状态目录

**注册项目**:
- 调用 `CLIConfig().register_project()` 注册到 `~/.alice/config.yaml`

### 优点

1. ✅ 双 UI 模式（InquirerPy / Rich Prompt fallback）
2. ✅ 预设技术栈模板
3. ✅ 配置摘要确认
4. ✅ 自动创建目录结构

### 缺点

1. ❌ **无自动检测**: 不检测现有项目结构（package.json、pom.xml）
2. ❌ **无路径校验**: 不检查项目路径是否已注册
3. ❌ **无恢复模式**: 不支持 `--resume` 或 `--from-config`
4. ❌ **无快速模式**: 必须回答所有问题，无法快速初始化
5. ❌ **无验证**: 不验证 URL 可访问性、测试账号格式
6. ❌ **硬编码预设**: 技术栈预设固定在代码中

---

## 改进目标

### 1. 自动检测项目结构

**检测规则**:

```python
# 前端框架检测
package.json → 读取 dependencies
  - "vue": "^3.x" → Vue 3
  - "react": "^18.x" → React
  - "@angular/core" → Angular

# UI 库检测
package.json → 读取 dependencies
  - "element-plus" → Element Plus
  - "ant-design-vue" → Ant Design Vue
  - "antd" → Ant Design
  - "@mui/material" → Material UI

# 后端框架检测（未来扩展）
pom.xml → Java/Maven
build.gradle → Java/Gradle
requirements.txt → Python
Gemfile → Ruby
```

**实现**:
```python
def detect_tech_stack(project_path: Path) -> dict:
    """自动检测项目技术栈。"""
    tech_stack = {"framework": None, "ui_library": None, "detected": False}
    
    # 检测 package.json
    package_json = project_path / "package.json"
    if package_json.exists():
        data = json.loads(package_json.read_text())
        deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
        
        # 框架检测
        if "vue" in deps:
            tech_stack["framework"] = "vue3"
        elif "react" in deps:
            tech_stack["framework"] = "react"
        elif "@angular/core" in deps:
            tech_stack["framework"] = "angular"
        
        # UI 库检测
        if "element-plus" in deps:
            tech_stack["ui_library"] = "Element Plus"
        elif "ant-design-vue" in deps:
            tech_stack["ui_library"] = "Ant Design Vue"
        elif "antd" in deps:
            tech_stack["ui_library"] = "Ant Design"
        elif "@mui/material" in deps:
            tech_stack["ui_library"] = "Material UI"
        
        tech_stack["detected"] = True
    
    return tech_stack
```

### 2. 路径校验与重复检测

**校验规则**:
- 项目路径必须存在
- 不能是已注册项目的路径
- 如果 `.tlo/project.yaml` 已存在，提示覆盖或恢复

**实现**:
```python
def validate_project_path(project_path: Path, config: CLIConfig) -> dict:
    """校验项目路径。"""
    result = {"ok": True, "warnings": [], "errors": []}
    
    # 1. 路径存在性
    if not project_path.exists():
        result["errors"].append(f"路径不存在: {project_path}")
        result["ok"] = False
        return result
    
    # 2. 重复注册检测
    registered_projects = config.get("projects", {})
    for project_id, info in registered_projects.items():
        if Path(info["path"]).resolve() == project_path.resolve():
            result["warnings"].append(f"路径已注册为项目: {project_id}")
    
    # 3. 已有配置检测
    project_yaml = project_path / ".tlo" / "project.yaml"
    if project_yaml.exists():
        result["warnings"].append(".tlo/project.yaml 已存在，可以选择覆盖或恢复")
    
    return result
```

### 3. 恢复模式（Resume）

**场景**: 用户中断初始化，或修改已有配置

**实现**:
```python
def resume_from_existing(project_path: Path) -> Optional[dict]:
    """从已有配置恢复。"""
    project_yaml = project_path / ".tlo" / "project.yaml"
    if not project_yaml.exists():
        return None
    
    with open(project_yaml, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    # 转换为 init 向导格式
    config = {
        "project_name": data.get("project", {}).get("name", ""),
        "base_url": data.get("connection", {}).get("base_url", ""),
        "environment": data.get("connection", {}).get("environment", "staging"),
        "login_required": data.get("connection", {}).get("login_required", False),
        "login_method": data.get("connection", {}).get("login_method", "form"),
        "test_framework": data.get("test_project", {}).get("type", "pytest-selenium"),
        "tech_stack": data.get("application", {}).get("tech_stack", {}).get("frontend", {}),
    }
    
    return config
```

### 4. 快速模式（Quick Init）

**使用场景**: 测试、演示、快速原型

**实现**:
```bash
# 最小化交互（使用默认值）
aitest init --quick

# 完全非交互（仅依赖自动检测）
aitest init --yes --project-name "MyProject" --base-url "http://localhost:3000"

# 从模板初始化
aitest init --template vue3-element-plus
```

**模板系统**:
```python
TEMPLATES = {
    "vue3-element-plus": {
        "tech_stack": {"framework": "vue3", "ui_library": "Element Plus"},
        "test_framework": "playwright",
        "login_required": True,
    },
    "react-antd": {
        "tech_stack": {"framework": "react", "ui_library": "Ant Design"},
        "test_framework": "playwright",
        "login_required": True,
    },
    "minimal": {
        "tech_stack": {"framework": "custom", "ui_library": None},
        "test_framework": "pytest-selenium",
        "login_required": False,
    },
}
```

### 5. 配置验证

**验证规则**:
- URL 格式检查（http/https 开头）
- 测试账号格式检查（role:username:password）
- 可选：URL 可访问性检查（--validate-url）

**实现**:
```python
def validate_config(config: dict, validate_url: bool = False) -> dict:
    """验证配置。"""
    errors = []
    warnings = []
    
    # 1. URL 格式
    base_url = config.get("base_url", "")
    if not base_url.startswith(("http://", "https://")):
        errors.append("目标 URL 必须以 http:// 或 https:// 开头")
    
    # 2. URL 可访问性（可选）
    if validate_url and base_url:
        try:
            response = requests.head(base_url, timeout=5)
            if response.status_code >= 400:
                warnings.append(f"目标 URL 返回 {response.status_code}，可能不可访问")
        except Exception as e:
            warnings.append(f"无法访问目标 URL: {e}")
    
    # 3. 测试账号格式
    for account in config.get("test_accounts", []):
        if not all(k in account for k in ("role", "username", "password")):
            errors.append(f"测试账号格式错误: {account}")
    
    # 4. 模块名称
    modules = config.get("modules", [])
    if not modules:
        warnings.append("未配置模块，后续可能需要手动添加")
    
    return {"ok": len(errors) == 0, "errors": errors, "warnings": warnings}
```

### 6. 外部配置模板

**目标**: 技术栈预设可配置，不硬编码

**实现**:
```yaml
# ~/.alice/templates.yaml 或 governance/templates/tech_stacks.yaml
tech_stacks:
  - name: "Vue 3 + Element Plus (国内主流)"
    category: frontend
    framework: vue3
    ui: Element Plus
  - name: "React + shadcn/ui"
    category: frontend
    framework: react
    ui: shadcn/ui
  - name: "Next.js + Tailwind"
    category: frontend
    framework: nextjs
    ui: Tailwind CSS
```

---

## 新命令参数

```bash
aitest init [OPTIONS]

OPTIONS:
  --project-path PATH          项目路径（默认: 当前目录）
  --project-name NAME          项目名称（跳过交互）
  --base-url URL               目标 URL（跳过交互）
  --quick                      快速模式（使用默认值）
  --template NAME              使用模板（vue3-element-plus/react-antd/minimal）
  --yes, -y                    自动确认（跳过确认步骤）
  --resume                     从已有配置恢复
  --from-config FILE           从配置文件导入
  --validate-url               验证 URL 可访问性
  --output json|yaml|table     输出格式
```

---

## 新工作流

### 流程 1: 标准交互式初始化

```bash
$ aitest init

[1/8] 🔍 检测项目结构...
  ✓ 检测到 package.json
  ✓ 框架: Vue 3
  ✓ UI 库: Element Plus

[2/8] 📋 项目信息
  项目名称: [自动填充: my-project]

[3/8] 🔧 技术栈
  检测到: Vue 3 + Element Plus
  是否使用检测结果? (Y/n)

[4/8] 🌐 目标 URL
  URL: http://localhost:3000
  ✓ URL 格式正确

[5/8] 🔐 登录配置
  需要登录? (Y/n)
  登录方式: [1] form  [2] api  [3] sso

[6/8] 📦 模块配置
  模块列表 (逗号分隔): user-management, dashboard

[7/8] 📊 配置摘要
  ┌────────────┬──────────────────────┐
  │ 项目名称   │ my-project          │
  │ 技术栈     │ Vue 3 + Element Plus│
  │ 目标 URL   │ http://localhost:3000│
  │ 环境       │ staging             │
  │ 登录       │ 是 (form)           │
  │ 模块       │ 2 个                │
  └────────────┴──────────────────────┘

[8/8] ✅ 确认配置? (Y/n)

✓ 项目初始化完成！
  .tlo/project.yaml 已生成
  2 个模块目录已创建
  项目已注册: my-project

下一步:
  aitest project set --id=my-project
  aitest run create --target agent:page-observer --module user-management
```

### 流程 2: 快速模式

```bash
$ aitest init --quick --project-name "TestProject" --base-url "http://localhost:3000"

✓ 项目初始化完成（快速模式）
  使用默认配置
  项目已注册: testproject
```

### 流程 3: 从模板初始化

```bash
$ aitest init --template vue3-element-plus --project-name "MyApp"

✓ 使用模板: Vue 3 + Element Plus
✓ 项目初始化完成
```

### 流程 4: 恢复模式

```bash
$ aitest init --resume

⚠️  检测到已有配置: .tlo/project.yaml
[1] 恢复并编辑
[2] 覆盖（删除旧配置）
[3] 取消

选择: 1

✓ 已加载现有配置
  项目名称: my-project [Enter 保持不变]
  ...
```

---

## 实现计划

### Phase 1: 核心改进（本次实现）

1. ✅ 项目路径校验与重复检测
2. ✅ 自动检测技术栈（package.json）
3. ✅ 配置验证（URL 格式、账号格式）
4. ✅ 快速模式（--quick）
5. ✅ 非交互模式（--yes + CLI 参数）

### Phase 2: 高级特性（后续）

6. ⏸️ 恢复模式（--resume）
7. ⏸️ 模板系统（--template）
8. ⏸️ 外部配置文件（--from-config）
9. ⏸️ URL 可访问性验证（--validate-url）
10. ⏸️ 外部技术栈模板（templates.yaml）

---

## 文件清单

### 修改文件

1. `aitest/cli/commands/project/init.py` — 主逻辑改进（+200 行）
   - 添加自动检测函数
   - 添加路径校验
   - 添加配置验证
   - 添加快速模式

### 新增文件

2. `aitest/cli/utils/detection.py` — 项目结构检测工具（~150 行）
   - `detect_tech_stack()` — 技术栈检测
   - `detect_modules()` — 模块检测
   - `detect_test_framework()` — 测试框架检测

3. `aitest/cli/utils/validation.py` — 配置验证工具（~100 行）
   - `validate_url()` — URL 验证
   - `validate_accounts()` — 账号格式验证
   - `validate_project_path()` — 路径验证

### 测试文件

4. `aitest/tests/cli/test_init_improved.py` — 单元测试（~200 行）

---

## 成功指标

1. ✅ 自动检测技术栈准确率 > 90%
2. ✅ 重复路径注册被拦截
3. ✅ 快速模式 < 5 秒完成初始化
4. ✅ 配置验证拦截所有无效格式
5. ✅ 向后兼容（旧命令继续工作）

---

## 风险与缓解

### 风险 1: 自动检测误判

**场景**: package.json 存在但不是前端项目

**缓解**:
- 提供手动覆盖选项
- 显示检测结果，用户确认后才应用

### 风险 2: 路径校验过严

**场景**: 合法用例被拦截

**缓解**:
- 使用警告而非错误
- 提供 `--force` 参数跳过校验

---

## 参考

- **现有实现**: `aitest/cli/commands/project/init.py`
- **项目管理**: `aitest/cli/adapters/project_adapter.py`
- **配置系统**: `aitest/cli/config.py`
- **路线图**: `docs/MASTER_ROADMAP.md` — P2-4
