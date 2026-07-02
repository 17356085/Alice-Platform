# Phase 0: Project Setup 设计

> 架构解耦分析 — 文档 8/8
> 核心问题: 在 SOP 执行之前，怎么让引擎知道"测什么、怎么测"?

## 1. Phase 0 的位置

```
Phase 0: Project Setup (本文件)
  → 收集项目信息
  → 生成 project.yaml + test_accounts.yaml
  → 暂停: 让用户确认配置
Phase 1: Project Init
  → 生成 PROJECT_CONTEXT.md
  → 暂停
Phase 2: Requirement
  ...
```

**触发条件**:
- 有 `.tlo/project.yaml` → 跳过 Phase 0，直接进 Phase 1
- 无 `.tlo/project.yaml` → 进入 Phase 0，交互式配置

## 2. Phase 0 问题清单

### 2.1 必填问题 (7 个)

| # | 问题 | project.yaml 字段 | 默认值 |
|---|------|-------------------|--------|
| 1 | 项目名称 | `project.name` | 无 |
| 2 | 技术栈 | `application.tech_stack` | 无 |
| 3 | 目标 URL | `connection.base_url` | 无 |
| 4 | 环境类型 | `connection.environment` | `staging` |
| 5 | 需要登录 | `connection.login_required` | 无 |
| 6 | 测试框架 | `test_project.type` | `pytest-selenium` |
| 7 | 模块列表 | `.tlo/knowledge/modules/` | 自动扫描或手动输入 |

### 2.2 可选问题 (有默认值)

| # | 问题 | project.yaml 字段 | 默认值 |
|---|------|-------------------|--------|
| 8 | 架构类型 | `application.architecture` | `SPA` |
| 9 | 登录方式 | `connection.login_method` | `form` |
| 10 | 测试账号 | `.tlo/context/test_accounts.yaml` | 需要填写 |
| 11 | 浏览器 | `runtime.browser` | `chrome` |
| 12 | 运行模式 | `runtime.headless` | `true` |
| 13 | 窗口大小 | `runtime.window_size` | `1920x1080` |
| 14 | 清理策略 | `data.cleanup_strategy` | `api` |
| 15 | 通过率阈值 | `gates.pass_rate_threshold` | `80%` |
| 16 | 跳过率阈值 | `gates.skip_rate_threshold` | `10%` |
| 17 | P0 必过 | `gates.p0_must_pass` | `true` |

### 2.3 交互流程

```
━━━ Phase 0: Project Setup ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 被测系统信息:
  项目名称? > 鞍集涂源管理系统
  技术栈? > Vue 3 + Element Plus
  目标 URL? > https://aiwechatminidemo.cimc-digital.com/
  环境类型? (dev/staging/prod) [staging] >

📋 登录与账号:
  需要登录? (y/n) [y] >
  登录方式? (form/api/sso) [form] >
  测试账号 (格式: 角色:用户名:密码，留空结束):
    > admin:admin:Admin@123
    > operator:op:Op@123
    > (空行结束)

📋 测试范围:
  测试框架? (pytest-selenium/playwright/cypress) [pytest-selenium] >
  模块列表 (逗号分隔，或输入 'scan' 自动扫描):
    > equipment, tank, production

  正在生成配置...
  ✅ .tlo/project.yaml 已生成
  ✅ .tlo/context/test_accounts.yaml 已生成

┌──────────────────────────────────────────────────────────────┐
│ Phase 0: Project Setup — 配置确认                             │
│                                                               │
│ 项目: 鞍集涂源管理系统                                         │
│ URL:  https://aiwechatminidemo.cimc-digital.com/              │
│ 环境: staging                                                 │
│ 技术: Vue 3 + Element Plus                                    │
│ 框架: pytest-selenium                                         │
│ 模块: equipment, tank, production                             │
│ 账号: 2 个 (admin, operator)                                  │
│                                                               │
│ 浏览器: Chrome (无头, 1920x1080)                               │
│ 清理: 测试后清理 (API 方式)                                    │
│ 门禁: 通过率 >= 80%, P0 必过                                   │
│                                                               │
│ 操作: [Enter] 确认  [e] 修改配置  [v] 查看文件                 │
│ >                                                             │
└──────────────────────────────────────────────────────────────┘

(用户确认后进入 Phase 1)
```

## 3. 账号存储与装填

### 3.1 存储位置

```
项目根目录/
├── .tlo/
│   ├── project.yaml              ← 项目配置 (不含密码)
│   └── context/
│       └── test_accounts.yaml    ← 账号信息 (单独文件)
```

**为什么单独文件**:
- `project.yaml` 可能提交到 Git，密码不能明文提交
- `test_accounts.yaml` 加入 `.gitignore`
- 分离关注点: 配置和凭证分开

### 3.2 test_accounts.yaml 格式

```yaml
# .tlo/context/test_accounts.yaml
# ⚠️ 此文件包含敏感信息，请勿提交到 Git

accounts:
  - role: admin
    username: admin
    password: "Admin@123"
    description: "系统管理员，拥有全部权限"

  - role: operator
    username: operator01
    password: "Op@123"
    description: "普通操作员，有设备管理权限"

  - role: viewer
    username: viewer01
    password: "View@123"
    description: "只读用户，只能查看"
```

### 3.3 装填方式

Phase 4 (Automation) 生成测试脚本时，从 `test_accounts.yaml` 读取账号并注入:

```python
# 生成的测试脚本示例
import yaml
from pathlib import Path

# 从 test_accounts.yaml 加载账号
_accounts = yaml.safe_load(
    Path(".tlo/context/test_accounts.yaml").read_text()
)
ACCOUNTS = {a["role"]: a for a in _accounts["accounts"]}

class TestAlarmConfig:
    def test_add_alarm_as_admin(self, browser):
        """管理员添加告警"""
        browser.login(ACCOUNTS["admin"]["username"],
                      ACCOUNTS["admin"]["password"])
        # ... 测试逻辑

    def test_add_alarm_as_operator(self, browser):
        """操作员添加告警"""
        browser.login(ACCOUNTS["operator"]["username"],
                      ACCOUNTS["operator"]["password"])
        # ... 测试逻辑
```

### 3.4 多账号输入方式

Phase 0 交互中，支持逐个输入和批量输入:

```
测试账号 (格式: 角色:用户名:密码，留空结束):
  > admin:admin:Admin@123
  > operator:op:Op@123
  > viewer:viewer:View@123
  > (空行结束)
```

高级选项: 从文件读取

```
测试账号文件路径? (留空手动输入) > ./test_accounts.yaml
  ✅ 读取到 3 个账号 (admin, operator, viewer)
```

## 4. 浏览器配置

### 4.1 配置维度

| 维度 | 选项 | 默认值 |
|------|------|--------|
| 浏览器类型 | Chrome / Firefox / Edge | Chrome |
| 运行模式 | 无头(headless) / 有头(headed) | 无头 |
| 窗口大小 | 1920x1080 / 1280x720 / 自定义 | 1920x1080 |
| 代理 | 无 / HTTP 代理 / SOCKS5 | 无 |

### 4.2 为什么需要这些配置

```
浏览器类型:
  → Selenium 需要知道启动哪个浏览器
  → 不同浏览器的兼容性不同

运行模式:
  → 无头: 不弹浏览器窗口，CI 环境用，速度快
  → 有头: 弹浏览器窗口，调试时用，可以看到操作过程

窗口大小:
  → 固定窗口大小，避免响应式布局导致元素位置变化
  → 1920x1080 是最常用的桌面分辨率

代理:
  → 内网环境可能需要代理才能访问被测系统
```

### 4.3 决策

Phase 0 **不问浏览器配置**，使用默认值:

```yaml
# project.yaml
runtime:
  browser: chrome
  headless: true
  window_size: "1920x1080"
```

用户可以在 `project.yaml` 中手动修改。

### 4.4 project.yaml 中的浏览器配置

```yaml
runtime:
  browser: chrome           # chrome / firefox / edge
  headless: true            # true = 无头, false = 有头
  window_size: "1920x1080"  # 窗口大小
  proxy: null               # null = 无代理, "http://proxy:8080"
  screenshot_on_failure: true  # 失败时截图
```

## 5. 数据策略

### 5.1 清理策略

| 策略 | 原理 | 优点 | 缺点 | 适用场景 |
|------|------|------|------|----------|
| **API 调用** | 调用被测系统的 API 删除数据 | 快、干净、不依赖 UI | 需要 API 文档 | 有 REST API 的系统 |
| **数据库操作** | 直连数据库 DELETE | 最彻底、最快 | 需要数据库权限、风险高 | 测试环境、有 DBA 支持 |
| **UI 操作** | 通过浏览器点击删除 | 最接近真实用户操作 | 慢、容易失败 | 没有 API 的系统 |
| **不清理** | 保留脏数据 | 无风险 | 数据越积越多 | 手动清理、一次性测试 |

### 5.2 决策

默认用 **API 调用**，如果没有 API 则用 **UI 操作**:

```yaml
# project.yaml
data:
  cleanup_strategy: "api"        # api / database / ui / none
  cleanup_after_test: true
  protected_resources:
    - "生产数据"
    - "系统配置"
  custom_cleanup_requires_confirm: true
```

### 5.3 Phase 7 交互流程

```
┌──────────────────────────────────────────────────────────────┐
│ Phase 7: Data Sanitization — 扫描完成                         │
│                                                               │
│ 发现测试残留数据:                                              │
│   🗑️  测试告警配置: 3 条 (API 删除)                           │
│   🗑️  测试摄像头配置: 2 条 (API 删除)                         │
│   🗑️  测试用户账号: 1 个 (API 删除)                           │
│                                                               │
│ 受保护数据 (不会删除):                                          │
│   🔒 生产数据: 0 条                                           │
│   🔒 系统配置: 0 条                                           │
│                                                               │
│ 总计: 6 条残留数据，预计清理耗时 3.2s                           │
│                                                               │
│ 操作: [Enter] 清理  [v] 查看详情  [s] 跳过 (保留脏数据)       │
│ >                                                             │
└──────────────────────────────────────────────────────────────┘
```

### 5.4 自定义清理确认

如果用户在 `protected_resources` 中添加了自定义项，清理前需要确认:

```
┌──────────────────────────────────────────────────────────────┐
│ ⚠️  自定义清理确认                                             │
│                                                               │
│ 以下数据不在默认保护名单中，是否清理?                            │
│   - 测试工单数据: 5 条                                         │
│   - 测试审批记录: 3 条                                         │
│                                                               │
│ 操作: [Enter] 全部清理  [1] 只清理工单  [2] 只清理审批  [s] 跳过│
│ >                                                             │
└──────────────────────────────────────────────────────────────┘
```

## 6. 质量门禁

### 6.1 门禁指标

| 指标 | 含义 | 默认阈值 |
|------|------|----------|
| **通过率** | 通过 / (总 - 跳过) | >= 80% |
| **跳过率** | 跳过 / 总 | <= 10% |
| **P0 通过率** | P0 通过 / P0 总数 | 100% |

### 6.2 通过率计算

```
总用例: 12
通过: 8
失败: 3
跳过: 1

通过率 = 通过 / (总 - 跳过) = 8 / (12 - 1) = 72.7%
跳过率 = 跳过 / 总 = 1 / 12 = 8.3%
```

**为什么跳过不计入分母**:
- 跳过的用例可能是前置条件不满足、环境不支持、或用户主动跳过
- 它们不应该拉低通过率
- 但跳过太多说明测试覆盖不足，所以有跳过率阈值

### 6.3 被测系统 Bug 的处理

通过率低于 80% 不一定是测试的问题，可能是被测系统本身有 Bug。

**Phase 6 (Bug Analysis) 的作用**:

```
Phase 5 执行完成
    │
    ▼
Phase 6: Bug Analysis
    │
    ├── 分析每个失败用例的原因
    │     ├── 断言失败 → 可能是系统 Bug
    │     ├── 超时 → 可能是系统慢
    │     ├── 元素未找到 → 可能是页面变更
    │     └── 驱动错误 → 测试环境问题
    │
    └── 分类: 系统 Bug vs 测试问题
```

### 6.4 门禁判断逻辑

```
通过率 >= 80% 且 P0 全过 → ✅ 通过

通过率 < 80%
    │
    ▼
Phase 6 分析结果:
    ├── 全是系统 Bug → ⚠️ 通过 (标记为"已知 Bug")
    │     "通过率 72.7%，但 3 个失败均为被测系统 Bug"
    │
    ├── 有测试脚本问题 → ❌ 不通过
    │     "通过率 72.7%，其中 2 个失败为测试脚本问题，需要修复"
    │
    └── 混合 → ⚠️ 部分通过
          "通过率 72.7%，2 个系统 Bug，1 个脚本问题"

跳过率 > 10% → ⚠️ 警告
    "跳过率 15%，测试覆盖不足，建议检查用例设计"

P0 有失败 → ❌ 不通过 (无论通过率)
    "P0 用例 test_critical_flow 失败，门禁不通过"
```

### 6.5 project.yaml 中的门禁配置

```yaml
gates:
  pass_rate_threshold: 80%       # 通过率 >= 80%
  skip_rate_threshold: 10%       # 跳过率 <= 10%
  p0_must_pass: true             # P0 必须全过
  consider_bug_analysis: true    # 考虑 Bug 分析结果
```

### 6.6 Phase 5 门禁展示

```
┌──────────────────────────────────────────────────────────────┐
│ Phase 5: Execute & Debug — 门禁结果                           │
│                                                               │
│ 测试结果:                                                     │
│   ✅ 通过: 8 个                                               │
│   ❌ 失败: 3 个                                               │
│   ⚠️  错误: 1 个                                              │
│   ⏭️  跳过: 0 个                                              │
│   ⏱️  耗时: 45.2s                                             │
│                                                               │
│ 门禁指标:                                                     │
│   通过率: 72.7% (阈值: 80%)                                   │
│   跳过率: 0% (阈值: 10%)                                      │
│   P0 通过率: 100%                                             │
│                                                               │
│ 门禁结果: ⚠️ 待定 (需要 Phase 6 分析失败原因)                  │
│                                                               │
│ 操作: [Enter] 继续分析  [v] 查看详细报告                       │
│ >                                                             │
└──────────────────────────────────────────────────────────────┘
```

### 6.7 Phase 6 门禁最终判定

```
┌──────────────────────────────────────────────────────────────┐
│ Phase 6: Bug Analysis — 门禁最终判定                          │
│                                                               │
│ 失败原因分析:                                                  │
│   ❌ test_add_alarm — 系统 Bug (保存后数据不一致)              │
│   ❌ test_edit_alarm — 系统 Bug (编辑弹窗加载异常)             │
│   ❌ test_camera_preview — 测试问题 (路由跳转代码错误)         │
│   ⚠️  test_camera_settings — 环境问题 (WebDriver 崩溃)        │
│                                                               │
│ 分类统计:                                                     │
│   🐛 系统 Bug: 2 个                                           │
│   🔧 测试问题: 1 个                                           │
│   🌐 环境问题: 1 个                                           │
│                                                               │
│ 门禁最终判定: ⚠️ 部分通过                                      │
│   通过率: 72.7% → 调整后: 90.9% (排除系统 Bug 和环境问题)      │
│   P0 通过率: 100%                                             │
│                                                               │
│ 建议:                                                         │
│   - 修复 test_camera_preview 的路由跳转代码                    │
│   - 系统 Bug 已记录，建议提 Bug                                │
│                                                               │
│ 操作: [Enter] 继续  [v] 查看完整分析  [e] 修改修复建议         │
│ >                                                             │
└──────────────────────────────────────────────────────────────┘
```

## 7. 完整 Phase 0 输出

### 7.1 生成的 project.yaml

```yaml
# .tlo/project.yaml

project:
  id: "web-automation"
  name: "鞍集涂源管理系统"

application:
  type: "web"
  tech_stack: "Vue 3 + Element Plus"
  architecture: "SPA"

connection:
  base_url: "https://aiwechatminidemo.cimc-digital.com/"
  environment: "staging"
  login_required: true
  login_method: "form"

runtime:
  browser: chrome
  headless: true
  window_size: "1920x1080"
  screenshot_on_failure: true

test_project:
  type: "pytest-selenium"
  code_path: "../ZJSN_Test-master526"
  page_objects_path: "page/"
  scripts_path: "script/"

data:
  cleanup_strategy: "api"
  cleanup_after_test: true
  protected_resources:
    - "生产数据"
    - "系统配置"
  custom_cleanup_requires_confirm: true

gates:
  pass_rate_threshold: 80%
  skip_rate_threshold: 10%
  p0_must_pass: true
  consider_bug_analysis: true
```

### 7.2 生成的 test_accounts.yaml

```yaml
# .tlo/context/test_accounts.yaml
# ⚠️ 此文件包含敏感信息，请勿提交到 Git

accounts:
  - role: admin
    username: admin
    password: "Admin@123"
    description: "系统管理员，拥有全部权限"

  - role: operator
    username: operator01
    password: "Op@123"
    description: "普通操作员，有设备管理权限"
```

### 7.3 生成的 .gitignore 条目

```
# 账号信息
.tlo/context/test_accounts.yaml
```

## 8. Phase 0 的 CLI 命令

```bash
# 新项目: 进入 Phase 0 交互式配置
python demo.py --project-path D:\...\MyNewProject

# 已有项目: 跳过 Phase 0，直接进 Phase 1
python demo.py --project-path D:\...\ZJSN_Test-master526 --module equipment

# 强制重新配置 (覆盖已有 project.yaml)
python demo.py --project-path D:\...\ZJSN_Test-master526 --reconfigure
```
