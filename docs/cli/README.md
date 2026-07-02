# Alice CLI — Engine 命令行工具

Alice CLI 是 Alice Engine 的命令行界面，用于执行测试自动化任务。

## 安装

```bash
# 从源码安装
cd /d/Desktop/Alice
pip install -e .

# 或者直接使用 python -m
python -m aitest.cli.main --help
```

## 命令概览

| 命令 | 说明 |
|------|------|
| `run` | 执行一次完整 SOP 流水线 |
| `validate` | 检查项目配置是否合法 |
| `status` | 查看执行状态 |
| `resume` | 继续中断的执行 |
| `list-projects` | 列出所有项目 |
| `list-modules` | 列出项目中的模块 |

## 快速开始

### 1. 检查项目配置

```bash
python -m aitest.cli.main validate --project-path D:/Desktop/TestingProject/ZJSN_Test-master526
```

输出:

```
                               项目配置检查
┌────────────────────┬──────┬────────────────────────────────────────────┐
│ 检查项             │ 状态 │ 说明                                       │
├────────────────────┼──────┼────────────────────────────────────────────┤
│ 项目目录           │  ✅  │ 存在                                       │
│ .tlo 目录          │  ✅  │ 存在                                       │
│ project.yaml       │  ✅  │ 存在                                       │
│ 项目 ID            │  ✅  │ web-automation                             │
│ 目标 URL           │  ✅  │ https://aiwechatminidemo.cimc-digital.com/ │
│ 应用类型           │  ✅  │ web                                        │
│ 测试框架           │  ✅  │ pytest-selenium                            │
│ test_accounts.yaml │  ✅  │ 存在                                       │
│ 模块目录           │  ✅  │ 12 个模块                                  │
│ API 文档           │  ⚠️  │ 不存在 (可选)                              │
└────────────────────┴──────┴────────────────────────────────────────────┘
```

### 2. 列出模块

```bash
python -m aitest.cli.main list-modules --project-path D:/Desktop/TestingProject/ZJSN_Test-master526
```

输出:

```
                                   模块列表
┌───────────────────┬────────┬──────────┬─────────────────────────────────────┐
│ 模块              │ 页面数 │ 已有知识 │ 路径                                │
├───────────────────┼────────┼──────────┼─────────────────────────────────────┤
│ equipment         │      4 │ ✅       │ D:\Desktop\TestingProject\ZJSN_Tes… │
│ tank              │      3 │ ✅       │ D:\Desktop\TestingProject\ZJSN_Tes… │
│ production        │      4 │ ✅       │ D:\Desktop\TestingProject\ZJSN_Tes… │
│ ...               │    ... │ ...      │ ...                                 │
└───────────────────┴────────┴──────────┴─────────────────────────────────────┘
```

### 3. 执行测试

```bash
# 使用 Mock LLM (不调用真实 API)
python -m aitest.cli.main run --project-path D:/Desktop/TestingProject/ZJSN_Test-master526 --module equipment --pages alarm-config --mock-llm

# 使用真实 LLM
python -m aitest.cli.main run --project-path D:/Desktop/TestingProject/ZJSN_Test-master526 --module equipment --pages alarm-config
```

输出:

```
┌─────────────────────────────── Alice Engine ────────────────────────────────┐
│ 项目路径: D:/Desktop/TestingProject/ZJSN_Test-master526                     │
│ 模块: equipment                                                             │
│ 页面: alarm-config                                                          │
│ 模式: full                                                                  │
└─────────────────────────────────────────────────────────────────────────────┘

  [project-agent] ████████ 4/4 skills, 4 steps
  [requirement-agent] ██ 2/2 skills, 2 steps
  [test-design-agent] ████████ 8/8 skills, 8 steps

┌───────────────────────────────── 执行结果 ──────────────────────────────────┐
│ 状态: ✅ completed                                                          │
│ Run ID: engine-06389edf                                                     │
│ 耗时: 23.0s                                                                 │
│ 完成 Phase: 2                                                               │
│ 处理页面: alarm-config                                                      │
└─────────────────────────────────────────────────────────────────────────────┘

已完成 Phase:
  ✅ Project Init
  ✅ Requirement
```

### 4. 新项目配置

当项目不存在时，会自动触发 Phase 0 配置:

```bash
python -m aitest.cli.main run --project-path D:/Desktop/NewProject --module equipment
```

交互流程:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Phase 0: Project Setup                                                      │
└─────────────────────────────────────────────────────────────────────────────┘

项目名称: 我的测试项目
技术栈配置:
  [1] Vue 3 + Element Plus (国内主流)
  [2] Vue 3 + Ant Design Vue
  [3] React + Ant Design
  [4] React + Material UI
  [5] Angular + Angular Material
  [6] 自定义
选择 [1]: 1

目标 URL: https://my-app.com/
🔍 检查 URL 可访问性...
✅ URL 可访问

环境类型:
  [1] dev (开发)
  [2] staging (预发布)
  [3] prod (生产)
选择 [2]:

需要登录? [Y/n]: y
登录方式:
  [1] form (表单登录)
  [2] api (API 登录)
  [3] sso (SSO 单点登录)
选择 [1]:

测试账号 (格式: 角色:用户名:密码，留空结束):
> admin:admin:Admin@123
✅ 已添加: admin (admin)
>

测试框架:
  [1] pytest-selenium (Python + Selenium)
  [2] playwright (Python + Playwright)
  [3] cypress (JavaScript + Cypress)
选择 [1]:

模块列表 (逗号分隔):
模块: equipment, tank, production

是否有 API 文档? [Y/n]: n

┌─────────────────────────────────────────────────────────────────────────────┐
│ 配置摘要                                                                    │
├────────────────────┬────────────────────────────────────────────────────────┤
│ 项目名称           │ 我的测试项目                                           │
│ 技术栈             │ Vue 3 + Element Plus                                   │
│ 目标 URL           │ https://my-app.com/                                    │
│ 环境               │ staging                                                │
│ 登录               │ 是                                                     │
│ 登录方式           │ form                                                   │
│ 测试账号           │ 1 个                                                   │
│ 测试框架           │ pytest-selenium                                        │
│ 模块               │ equipment, tank, production                            │
│ API 文档           │ 无                                                     │
└────────────────────┴────────────────────────────────────────────────────────┘

确认配置? [Y/n]: y
  ✅ .tlo/project.yaml 已生成
  ✅ .tlo/context/test_accounts.yaml 已生成
  ✅ 3 个模块目录已创建
```

### 5. 查看执行状态

```bash
python -m aitest.cli.main status --project-path D:/Desktop/TestingProject/ZJSN_Test-master526 --module equipment
```

输出:

```
                                    执行状态
┌──────────┬─────────────────┬──────────┬──────────┬─────────────────────────┐
│ 模块     │ 状态            │ 完成Phase│ 失败Phase│ 更新时间                │
├──────────┼─────────────────┼──────────┼──────────┼─────────────────────────┤
│ equipment│ ✅ 完成         │ 9        │ -        │ 2026-07-01T21:13:05    │
└──────────┴─────────────────┴──────────┴──────────┴─────────────────────────┘
```

### 6. 继续中断的执行

```bash
python -m aitest.cli.main resume --project-path D:/Desktop/TestingProject/ZJSN_Test-master526 --module equipment
```

## 命令详解

### run

执行一次完整 SOP 流水线。

```bash
python -m aitest.cli.main run [OPTIONS]
```

选项:

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `--project-path, -p` | 项目路径 | 必填 |
| `--module, -m` | 模块名 | 必填 |
| `--pages` | 页面列表 (逗号分隔) | 自动发现 |
| `--mode` | 执行模式 | full |
| `--extensions, -e` | Extensions (逗号分隔) | 无 |
| `--mock-llm` | 使用 Mock LLM | False |
| `--llm` | LLM Provider | 自动检测 |
| `--verbose, -v` | 详细输出 | False |

执行模式:

| 模式 | 说明 |
|------|------|
| `full` | 完整执行 (默认) |
| `resume` | 从上次中断处继续 |
| `from-automation` | 从自动化阶段开始 |
| `from-test-design` | 从测试设计阶段开始 |
| `from-requirement` | 从需求阶段开始 |
| `status` | 只查看状态，不执行 |

Extensions:

| 名称 | 说明 |
|------|------|
| `audit` | 状态漂移 + SOP 合规审计 |
| `complexity` | 按复杂度选择 SOP 流水线 |
| `knowledge` | 跨 Run 知识复用 |
| `memory` | ChromaDB 向量记忆 |

### validate

检查项目配置是否合法。

```bash
python -m aitest.cli.main validate --project-path PATH
```

### status

查看执行状态。

```bash
python -m aitest.cli.main status --project-path PATH [--module MODULE]
```

### resume

继续中断的执行。

```bash
python -m aitest.cli.main resume --project-path PATH --module MODULE [OPTIONS]
```

### list-projects

列出所有项目。

```bash
python -m aitest.cli.main list-projects --workspace PATH
```

### list-modules

列出项目中的模块。

```bash
python -m aitest.cli.main list-modules --project-path PATH
```

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `MOCK_LLM` | 使用 Mock LLM | 0 |
| `LLM_PROVIDER` | LLM Provider | 自动检测 |
| `ANTHROPIC_API_KEY` | Anthropic API Key | 无 |
| `OPENAI_API_KEY` | OpenAI API Key | 无 |
| `DEEPSEEK_API_KEY` | DeepSeek API Key | 无 |

## 配置文件

### .env

```bash
# LLM API Keys
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
DEEPSEEK_API_KEY=sk-...

# Mock LLM (测试用)
# MOCK_LLM=1
```

### .tlo/project.yaml

```yaml
project:
  id: "my-project"
  name: "我的测试项目"

application:
  type: "web"
  tech_stack:
    frontend:
      framework: "vue3"
      ui_library: "element-plus"

connection:
  base_url: "https://my-app.com/"
  environment: "staging"
  login_required: true
  login_method: "form"

test_project:
  type: "pytest-selenium"
```

### .tlo/context/test_accounts.yaml

```yaml
accounts:
  - role: admin
    username: admin
    password: "Admin@123"
    description: "系统管理员"
```

## 常见问题

### Q: 没有 API Key 怎么办?

使用 `--mock-llm` 参数:

```bash
python -m aitest.cli.main run --project-path ... --module equipment --mock-llm
```

### Q: 项目不存在怎么办?

直接运行 `run` 命令，会自动触发 Phase 0 配置:

```bash
python -m aitest.cli.main run --project-path D:/Desktop/NewProject --module equipment
```

### Q: 执行中断了怎么办?

使用 `resume` 命令继续:

```bash
python -m aitest.cli.main resume --project-path ... --module equipment
```

### Q: 怎么查看详细日志?

使用 `--verbose` 参数:

```bash
python -m aitest.cli.main run --project-path ... --module equipment --verbose
```

## 示例脚本

### 一键演示

```bash
#!/bin/bash
# demo.sh — 一键演示 Alice Engine

echo "=== Alice Engine Demo ==="

# 1. 检查配置
echo "1. 检查项目配置..."
python -m aitest.cli.main validate --project-path D:/Desktop/TestingProject/ZJSN_Test-master526

# 2. 列出模块
echo "2. 列出模块..."
python -m aitest.cli.main list-modules --project-path D:/Desktop/TestingProject/ZJSN_Test-master526

# 3. 执行测试 (Mock LLM)
echo "3. 执行测试 (Mock LLM)..."
python -m aitest.cli.main run --project-path D:/Desktop/TestingProject/ZJSN_Test-master526 --module equipment --pages alarm-config --mock-llm

echo "=== Demo 完成 ==="
```

## 开发

### 添加新命令

1. 在 `aitest/cli/commands/` 创建新文件
2. 实现命令函数
3. 在 `aitest/cli/main.py` 注册命令

### 添加新 Extension

1. 在 `aitest/engine/extensions/` 创建新文件
2. 实现 Extension 类
3. 在 `aitest/cli/commands/run.py` 注册 Extension
