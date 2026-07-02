# CLI 交互设计

> 把 Engine Demo Guide、CLI Interrupt Handler、Phase 0 Project Setup、API 文档导入整合为一份文档
> 核心问题: **CLI 模式下，怎么启动 Engine、怎么交互、怎么演示?**

## 1. 总览

### 1.1 完整 SOP 流程

```
Phase 0: Project Setup      → 收集项目配置 → 暂停 → 确认
Phase 1: Project Init       → 生成 PROJECT_CONTEXT.md → 暂停 → 确认
Phase 2: Requirement        → 生成 MODULE_CONTEXT.md → 暂停 → 确认
Phase 3: Test Design        → 生成 TEST_DESIGN.md + TEST_CASES.md → 暂停 → 确认
Phase 4: Automation         → 生成代码 → 暂停 → 确认
Phase 5: Execute & Debug    → 执行测试 → 暂停 → 确认
Phase 6: Bug Analysis       → 分析失败 → 暂停 → 确认
Phase 7: Data Sanitization  → 扫描脏数据 → 暂停 → 确认清理
Phase 8: Report             → 生成报告 → 暂停 → 确认
Phase 9: Knowledge          → 沉淀知识 → 暂停 → 确认

✅ 全部完成
```

### 1.2 每个暂停点的通用操作

| 操作 | 按键 | 含义 | 适用阶段 |
|------|------|------|----------|
| **继续** | `Enter` | 用当前版本进入下一阶段 | 全部 |
| **查看** | `v` | 打开编辑器查看文件内容 | 全部 |
| **修改** | `e` | 打开编辑器修改文件 | 生成文档的阶段 |
| **重新生成** | `r` | 给修改意见，让 AI 重新生成 | 生成文档的阶段 |
| **跳过** | `s` | 不执行/不清理/不生成 | 执行/清理阶段 |

### 1.3 操作流程图

```
暂停点展示
    │
    ├── Enter → 继续 → 下一 Phase
    │
    ├── v → 打开编辑器查看 → 关闭编辑器 → 回到暂停点
    │
    ├── e → 打开编辑器修改 → 关闭编辑器 → 合法性检查
    │       ├── ✅ 通过 → 回到暂停点 (文件已更新)
    │       └── ❌ 不通过 → 提示错误 → 回到暂停点
    │
    ├── r → 输入修改意见 → AI 重新生成 → 合法性检查
    │       ├── ✅ 通过 → 展示新版本 → 回到暂停点
    │       └── ❌ 不通过 → 提示错误 → 回到暂停点
    │
    └── s → 跳过 → 下一 Phase
```

## 2. Phase 0: Project Setup

### 2.1 触发条件

- 有 `.tlo/project.yaml` → 跳过 Phase 0，直接进 Phase 1
- 无 `.tlo/project.yaml` → 进入 Phase 0，交互式配置

### 2.2 必填问题 (7 个)

| # | 问题 | 验证规则 | project.yaml 字段 |
|---|------|----------|-------------------|
| 1 | 项目名称 | 非空, 2-50 字符 | `project.name` |
| 2 | 技术栈 | 分类选择到框架级别 | `application.tech_stack` |
| 3 | 目标 URL | 非空, http/https 开头, **必须可访问** | `connection.base_url` |
| 4 | 环境类型 | 必须是 dev/staging/prod | `connection.environment` |
| 5 | 需要登录 | 必须是 y/n | `connection.login_required` |
| 6 | 测试框架 | 必须是 pytest-selenium/playwright/cypress | `test_project.type` |
| 7 | 模块列表 | 非空, 逗号分隔 | `.tlo/knowledge/modules/` |

### 2.3 可选问题 (有默认值)

| # | 问题 | 默认值 | project.yaml 字段 |
|---|------|--------|-------------------|
| 8 | 登录方式 | form | `connection.login_method` |
| 9 | 测试账号 | 需要填写 | `.tlo/context/test_accounts.yaml` |
| 10 | CSS 框架 | 跳过 | `application.css_framework` |
| 11 | 路由方式 | 从框架推断 | `application.routing` |
| 12 | 状态管理 | 从框架推断 | `application.state_management` |
| 13 | TypeScript | 从框架推断 | `application.typescript` |
| 14 | API 风格 | REST | `application.api_style` |
| 15 | 认证方式 | 表单登录 | `application.auth_method` |
| 16 | API 文档 | 跳过 | `.tlo/api/openapi.json` |

### 2.4 技术栈分类输入

```
技术栈分类:
  [1] 前端 (Vue/React/Angular/Svelte/...)
  [2] 后端 (Spring Boot/Django/Flask/Express/...)
  [3] 移动端 (React Native/Flutter/Swift/Kotlin/...)
  [4] 桌面端 (Electron/Qt/Tauri/...)
  [5] 小程序 (微信/支付宝/百度/...)
  [6] 自定义
```

#### 预设模板 (快速选择)

```
技术栈预设:
  [1] Vue 3 + Element Plus (国内主流)
  [2] Vue 3 + Ant Design Vue
  [3] React + Ant Design
  [4] React + Material UI
  [5] Angular + Angular Material
  [6] 自定义
```

#### 逐项选择 (详细配置)

```
前端框架:
  [1] Vue 2  [2] Vue 3  [3] React  [4] Angular
  [5] Svelte  [6] Next.js  [7] Nuxt.js  [8] 其他

UI 组件库:
  [1] Element Plus  [2] Ant Design Vue  [3] Vuetify
  [4] Naive UI  [5] 无

CSS 框架 (可选):
  [1] Tailwind CSS  [2] Bootstrap  [3] UnoCSS  [4] 跳过

路由方式 (可选, 留空用默认):
  [1] Hash 路由 (默认)  [2] History 路由  [3] 不确定

状态管理 (可选, 留空用默认):
  [1] Pinia (默认)  [2] Vuex  [3] Redux  [4] Zustand  [5] 不确定

TypeScript:
  [1] 是  [2] 否  [3] 不确定
```

#### 智能推断表

| 前端框架 | 默认路由 | 默认状态管理 | 默认语言 |
|----------|----------|-------------|----------|
| Vue 2 | Hash | Vuex | JavaScript |
| Vue 3 | Hash | Pinia | TypeScript |
| React | History | Redux | TypeScript |
| Angular | History | NgRx | TypeScript |
| Next.js | History | Redux/Zustand | TypeScript |
| Nuxt.js | History | Pinia | TypeScript |

### 2.5 测试账号

#### 存储

```
.tlo/context/test_accounts.yaml  ← 单独文件，不提交 Git
```

#### 格式

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

#### 输入方式

```
测试账号 (格式: 角色:用户名:密码，留空结束):
  > admin:admin:Admin@123
  > operator:op:Op@123
  > (空行结束)
```

#### 装填方式

Phase 4 (Automation) 生成测试脚本时，从 yaml 读取账号并注入:

```python
import yaml
from pathlib import Path

_accounts = yaml.safe_load(
    Path(".tlo/context/test_accounts.yaml").read_text()
)
ACCOUNTS = {a["role"]: a for a in _accounts["accounts"]}

class TestAlarmConfig:
    def test_add_alarm_as_admin(self, browser):
        browser.login(ACCOUNTS["admin"]["username"],
                      ACCOUNTS["admin"]["password"])
```

### 2.6 API 文档导入

#### 来源清单

| 来源 | 格式 | 说明 |
|------|------|------|
| Swagger UI / Knife4j URL | HTTP 链接 | 最常见 |
| OpenAPI 文件 | JSON/YAML | 从 Swagger 导出 |
| Postman Collection | JSON | 从 Postman 导出 |
| Apifox / RAP / YAPI | JSON | 国内常用 API 工具 |
| GraphQL Schema | SDL | GraphQL 项目 |
| HAR 文件 | JSON | 浏览器抓包导出 |
| cURL 命令 | 文本 | 复制粘贴的 cURL |
| 源码目录 | 代码 | 扫描 @RequestMapping 等注解 |
| Markdown / Excel | 文件 | 团队自写的 API 文档 |
| Confluence / Wiki | HTML | 团队协作平台 |

#### 交互

```
📋 API 文档 (可选):
  是否有 API 文档? (y/n) [n] > y

  API 文档来源:
    [1] Swagger UI / Knife4j URL
    [2] OpenAPI 文件 (JSON/YAML)
    [3] Postman Collection
    [4] Apifox / RAP / YAPI 导出
    [5] GraphQL Schema
    [6] HAR 文件 (浏览器抓包)
    [7] cURL 命令
    [8] 源码目录 (自动扫描注解)
    [9] Markdown / Excel / 其他文件
    [10] 跳过

  > 1

  Swagger UI 地址:
  > https://aiwechatminidemo.cimc-digital.com/swagger-ui.html

  🔍 正在获取 API 文档...
  ✅ 发现 47 个 API 端点
     - 用户管理: 5 个
     - 设备管理: 12 个
     - 告警管理: 8 个

  已导入到 .tlo/api/openapi.json
```

#### 存储

```
.tlo/api/
├── openapi.json              ← 统一格式 (OpenAPI 3.0)
├── endpoints_summary.yaml    ← 解析后的摘要
└── raw/                      ← 原始文件备份
```

#### 各 Phase 中的用途

| Phase | 用途 |
|-------|------|
| Phase 3 | 生成 API 测试用例 |
| Phase 4 | 测试数据准备 (调 API 创建) |
| Phase 7 | 数据清理 (调 API 删除) |

#### 没有 API 文档时的降级

```
没有 API 文档:
  → 数据清理用 UI 操作 (慢但能用)
  → 测试数据准备用 UI 操作
  → 无法生成 API 测试用例
```

### 2.7 浏览器配置

Phase 0 **不问**，使用默认值:

```yaml
runtime:
  browser: chrome
  headless: true
  window_size: "1920x1080"
  screenshot_on_failure: true
```

用户可以在 `project.yaml` 中手动修改。

### 2.8 数据策略

```yaml
data:
  cleanup_strategy: "api"        # api / database / ui / none
  cleanup_after_test: true
  protected_resources:
    - "生产数据"
    - "系统配置"
  custom_cleanup_requires_confirm: true
```

### 2.9 质量门禁

```yaml
gates:
  pass_rate_threshold: 80%       # 通过率 >= 80%
  skip_rate_threshold: 10%       # 跳过率 <= 10%
  p0_must_pass: true             # P0 必须全过
  consider_bug_analysis: true    # 考虑 Bug 分析结果
```

#### 门禁判断逻辑

```
通过率 = 通过 / (总 - 跳过)
跳过率 = 跳过 / 总

通过率 >= 80% 且 P0 全过 → ✅ 通过

通过率 < 80%
  ├── Phase 6 分析: 全是系统 Bug → ⚠️ 通过 (标记已知 Bug)
  ├── Phase 6 分析: 有测试脚本问题 → ❌ 不通过
  └── Phase 6 分析: 混合 → ⚠️ 部分通过

跳过率 > 10% → ⚠️ 警告 (测试覆盖不足)

P0 有失败 → ❌ 不通过 (无论通过率)
```

### 2.10 输入验证

每个输入都验证，不合法就让用户重输:

| 问题 | 验证规则 | 不合法时 |
|------|----------|----------|
| 项目名称 | 非空, 2-50 字符 | 提示重输 |
| 技术栈 | 必须选到框架级别 | 提示重输 |
| 目标 URL | http/https 开头, **必须可访问** | **阻断**, 让用户重输 |
| 环境类型 | dev/staging/prod | 提示重输 |
| 需要登录 | y/n | 提示重输 |
| 测试账号 | 角色:用户名:密码 格式 | 提示重输 |
| 测试框架 | pytest-selenium/playwright/cypress | 提示重输 |
| 模块列表 | 非空, 逗号分隔 | 提示重输 |

### 2.11 生成的文件

```
.tlo/
├── project.yaml                ← 项目配置
├── context/
│   └── test_accounts.yaml      ← 账号信息
└── api/
    └── openapi.json            ← API 文档 (可选)
```

## 3. Phase 1-9: CLI 中断流程

### 3.1 暂停点清单

| # | Phase | 触发时机 | 展示内容 | 可用操作 |
|---|-------|----------|----------|----------|
| 1 | Project Init | PROJECT_CONTEXT.md 生成后 | 项目概览、模块数、页面数 | v/e/r/s |
| 2 | Requirement | MODULE_CONTEXT.md 生成后 | 模块概览、页面列表、业务流程 | v/e/r/s |
| 3 | Test Design | TEST_DESIGN.md + TEST_CASES.md 生成后 | 测试场景数、用例数、P0 数 | v/e/r/s |
| 4 | Automation | AUTO_STRATEGY.md + 代码生成后 | 策略摘要、生成的文件列表 | v/e/r/s |
| 5 | Execute & Debug | pytest 执行完成后 | 通过/失败/错误数、耗时、门禁结果 | v/s |
| 6 | Bug Analysis | 分析完成后 | 失败原因分类、修复建议、门禁最终判定 | v/e/s |
| 7 | Data Sanitization | 脏数据扫描完成后 | 要清理的数据清单、清理方式 | v/确认清理/s |
| 8 | Report | 报告生成后 | 报告文件路径 + 内容摘要 | v/s |
| 9 | Knowledge | 知识沉淀后 | 沉淀位置 + 内容摘要 | v/s |

### 3.2 Phase 1: Project Init

```
┌──────────────────────────────────────────────────────────────┐
│ Phase 1: Project Init — 完成                                  │
│                                                               │
│ 生成文件:                                                     │
│   📄 PROJECT_CONTEXT.md                                       │
│     - 项目概览: 鞍集涂源管理系统                               │
│     - 模块数: 5 个                                            │
│     - 页面数: 12 个                                           │
│                                                               │
│ 操作: [Enter] 继续  [v] 查看  [e] 修改  [r] 重新生成  [s] 跳过│
│ >                                                             │
└──────────────────────────────────────────────────────────────┘
```

**合法性检查**: 非空、包含 `#` 标题、包含模块列表

### 3.3 Phase 2: Requirement

```
┌──────────────────────────────────────────────────────────────┐
│ Phase 2: Requirement — 完成                                   │
│                                                               │
│ 生成文件:                                                     │
│   📄 MODULE_CONTEXT.md                                        │
│     - 模块: equipment (设备管理)                               │
│     - 页面: 4 个                                              │
│     - 业务流程: 3 条                                          │
│                                                               │
│ 操作: [Enter] 继续  [v] 查看  [e] 修改  [r] 重新生成  [s] 跳过│
│ >                                                             │
└──────────────────────────────────────────────────────────────┘
```

**合法性检查**: 非空、包含 `#` 标题、包含页面列表

### 3.4 Phase 3: Test Design

```
┌──────────────────────────────────────────────────────────────┐
│ Phase 3: Test Design — 完成                                   │
│                                                               │
│ 生成文件:                                                     │
│   📄 TEST_DESIGN.md (15 个测试场景, 8 个风险点)               │
│   📄 TEST_CASES.md (37 个测试用例, 3 个 P0, 12 个 P1)         │
│                                                               │
│ 操作: [Enter] 继续  [v] 查看  [e] 修改  [r] 重新生成  [s] 跳过│
│ >                                                             │
└──────────────────────────────────────────────────────────────┘
```

**合法性检查**:
- TEST_DESIGN.md: 非空、包含测试场景、有 BS-XXX 编号
- TEST_CASES.md: 非空、包含测试用例、有 TC-XXX 编号、有 P0/P1 标记

### 3.5 Phase 4: Automation

```
┌──────────────────────────────────────────────────────────────┐
│ Phase 4: Automation — 完成                                    │
│                                                               │
│ 生成文件:                                                     │
│   📄 AUTO_STRATEGY.md (定位器: CSS 优先, 等待: vue_stable)    │
│   📄 page/equipment_page/AlarmConfigPage.py                   │
│   📄 page/equipment_page/CameraPage.py                        │
│   📄 script/equipment/test_alarm_config.py (12 用例)          │
│   📄 script/equipment/test_camera.py (8 用例)                 │
│                                                               │
│ 操作: [Enter] 继续  [v] 查看  [e] 修改  [r] 重新生成  [s] 跳过│
│ >                                                             │
└──────────────────────────────────────────────────────────────┘
```

**合法性检查**:
- AUTO_STRATEGY.md: 非空、包含定位器策略、包含等待策略
- PageObject.py: Python 语法正确、能被 import
- test_*.py: Python 语法正确、能被 pytest 收集

### 3.6 Phase 5: Execute & Debug

```
━━━ Phase 5/10: Execute & Debug ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  即将执行:
    pytest script/equipment/test_*.py

┌──────────────────────────────────────────────────────────────┐
│ Phase 5: Execute & Debug — 即将执行                           │
│                                                               │
│ 测试脚本:                                                     │
│   📄 test_alarm_config.py (12 用例)                           │
│   📄 test_camera.py (8 用例)                                  │
│                                                               │
│ 操作: [Enter] 执行  [v] 查看脚本  [s] 跳过                    │
│ >                                                             │
└──────────────────────────────────────────────────────────────┘

(执行中...)

┌──────────────────────────────────────────────────────────────┐
│ Phase 5: Execute & Debug — 执行完成                           │
│                                                               │
│ 测试结果:                                                     │
│   ✅ 通过: 8 个                                               │
│   ❌ 失败: 3 个                                               │
│   ⚠️  错误: 1 个                                              │
│   ⏭️  跳过: 0 个                                              │
│   ⏱️  耗时: 45.2s                                             │
│                                                               │
│ 失败用例:                                                     │
│   ❌ test_add_alarm — AssertionError                          │
│   ❌ test_edit_alarm — TimeoutError                           │
│   ❌ test_camera_preview — ElementNotFound                    │
│   ⚠️  test_camera_settings — WebDriverError                   │
│                                                               │
│ 门禁指标:                                                     │
│   通过率: 72.7% (阈值: 80%)                                   │
│   跳过率: 0% (阈值: 10%)                                      │
│   P0 通过率: 100%                                             │
│                                                               │
│ 门禁结果: ⚠️ 待定 (需要 Phase 6 分析)                          │
│                                                               │
│ 操作: [Enter] 继续  [v] 查看详细报告                           │
│ >                                                             │
└──────────────────────────────────────────────────────────────┘
```

### 3.7 Phase 6: Bug Analysis

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
│   调整后通过率: 90.9% (排除系统 Bug 和环境问题)                 │
│                                                               │
│ 建议:                                                         │
│   - 修复 test_camera_preview 的路由跳转代码                    │
│   - 系统 Bug 已记录，建议提 Bug                                │
│                                                               │
│ 操作: [Enter] 继续  [v] 查看完整分析  [e] 修改修复建议         │
│ >                                                             │
└──────────────────────────────────────────────────────────────┘
```

**合法性检查**: 分析报告非空、每个失败用例有原因和修复建议

### 3.8 Phase 7: Data Sanitization

```
┌──────────────────────────────────────────────────────────────┐
│ Phase 7: Data Sanitization — 扫描完成                         │
│                                                               │
│ 发现测试残留数据:                                              │
│   🗑️  测试告警配置: 3 条                                      │
│      清理方式: DELETE /api/alarm/config/{id}                  │
│                                                               │
│   🗑️  测试摄像头配置: 2 条                                    │
│      清理方式: DELETE /api/camera/{id}                        │
│                                                               │
│ 受保护数据 (不会删除):                                          │
│   🔒 生产数据: 0 条                                           │
│   🔒 系统配置: 0 条                                           │
│                                                               │
│ 总计: 5 条残留数据                                              │
│                                                               │
│ 操作: [Enter] 清理  [v] 查看详情  [s] 跳过 (保留脏数据)       │
│ >                                                             │
└──────────────────────────────────────────────────────────────┘
```

### 3.9 Phase 8: Report

```
┌──────────────────────────────────────────────────────────────┐
│ Phase 8: Report — 完成                                        │
│                                                               │
│ 报告文件:                                                     │
│   📄 .tlo/runtime/reports/TEST_REPORT_equipment.md            │
│                                                               │
│ 报告摘要:                                                     │
│   总用例: 12                                                  │
│   通过: 8 (66.7%)                                             │
│   失败: 3 (25.0%) — 其中 2 个系统 Bug                         │
│   错误: 1 (8.3%)                                              │
│   耗时: 45.2s                                                 │
│                                                               │
│ 操作: [Enter] 继续  [v] 查看报告                               │
│ >                                                             │
└──────────────────────────────────────────────────────────────┘
```

### 3.10 Phase 9: Knowledge

```
┌──────────────────────────────────────────────────────────────┐
│ Phase 9: Knowledge — 完成                                     │
│                                                               │
│ 知识沉淀:                                                     │
│   📁 .tlo/knowledge/modules/equipment/                        │
│     - MODULE_CONTEXT.md (已更新)                               │
│     - pages/alarm-config/PAGE_CONTEXT.md (已更新)              │
│     - bug_patterns.json (新增: 2 条系统 Bug 模式)              │
│                                                               │
│ 操作: [Enter] 继续  [v] 查看沉淀内容                           │
│ >                                                             │
└──────────────────────────────────────────────────────────────┘
```

## 4. CLIInterruptHandler 接口

### 4.1 数据结构

```python
@dataclass
class InterruptPayload:
    """中断信息。"""
    phase: str                    # Phase 名称
    phase_index: int              # Phase 序号 (0-9)
    total_phases: int             # 总 Phase 数 (10)
    module: str                   # 模块名
    files: list[GeneratedFile]    # 生成的文件列表
    summary: dict                 # 摘要信息
    execution_result: dict = None # 执行结果 (Phase 5 专用)


@dataclass
class GeneratedFile:
    """生成的文件信息。"""
    path: Path                    # 文件路径
    file_type: str                # 文件类型 (md/py/json)
    stats: dict = None            # 统计信息


@dataclass
class InterruptDecision:
    """用户决策。"""
    action: str                   # continue / edit / regenerate / skip
    feedback: str = None          # 修改意见 (regenerate 时)


@dataclass
class ValidationResult:
    """合法性检查结果。"""
    ok: bool                      # 是否通过
    errors: list[str] = None      # 错误列表
```

### 4.2 接口定义

```python
class CLIInterruptHandler:
    """CLI 模式下的中断处理器。"""

    def handle(self, payload: InterruptPayload) -> InterruptDecision:
        """处理中断，返回用户决策。"""
        ...

    def validate(self, file_path: Path, phase: str) -> ValidationResult:
        """验证修改后的文件是否合法。"""
        ...

    def open_editor(self, file_path: Path) -> None:
        """打开编辑器查看/修改文件。"""
        ...
```

## 5. 合法性检查规则

| Phase | 文件 | 检查项 |
|-------|------|--------|
| 1 | PROJECT_CONTEXT.md | 非空、包含 `#` 标题、包含模块列表 |
| 2 | MODULE_CONTEXT.md | 非空、包含 `#` 标题、包含页面列表 |
| 3 | TEST_DESIGN.md | 非空、包含测试场景、有 BS-XXX 编号 |
| 3 | TEST_CASES.md | 非空、包含测试用例、有 TC-XXX 编号、有 P0/P1 标记 |
| 4 | AUTO_STRATEGY.md | 非空、包含定位器策略、包含等待策略 |
| 4 | PageObject.py | Python 语法正确、能被 import |
| 4 | test_*.py | Python 语法正确、能被 pytest 收集 |
| 6 | Bug 分析报告 | 非空、每个失败用例有原因和修复建议 |

## 6. CLI 命令

```bash
# 新项目: 进入 Phase 0 交互式配置
python demo.py --project-path D:\...\MyNewProject

# 已有项目: 跳过 Phase 0
python demo.py --project-path D:\...\ZJSN_Test-master526 --module equipment

# 指定页面
python demo.py --project-path D:\...\ZJSN_Test-master526 --module equipment --pages alarm-config camera

# 强制重新配置
python demo.py --project-path D:\...\ZJSN_Test-master526 --reconfigure

# Mock LLM (不调 API)
python demo.py --project-path D:\...\ZJSN_Test-master526 --module equipment --mock-llm

# Dry run (只看计划)
python demo.py --project-path D:\...\ZJSN_Test-master526 --module equipment --dry-run
```

## 7. 最终结果展示

```
╔══════════════════════════════════════════════════════════════╗
║  ✅ 全部完成!                                                 ║
║                                                               ║
║  Run ID: engine-a1b2c3d4                                      ║
║  总耗时: 92.4s                                                ║
║  模块: equipment                                              ║
║  页面: alarm-config, camera, key-param, maintenance            ║
║                                                               ║
║  门禁结果: ⚠️ 部分通过 (调整后通过率 90.9%)                     ║
║                                                               ║
║  产物:                                                        ║
║    📄 .tlo/runtime/reports/TEST_REPORT_equipment.md            ║
║    📄 .tlo/runtime/sop-status/SOP_STATUS_equipment.json        ║
║    📄 .tlo/knowledge/modules/equipment/ (已更新)               ║
║                                                               ║
║  下一步:                                                      ║
║    - 查看报告: cat .tlo/runtime/reports/TEST_REPORT_equipment.md│
║    - 提 Bug: 2 个系统 Bug 已记录                               ║
║    - 测试其他模块: python demo.py --project-path ... --module tank║
╚══════════════════════════════════════════════════════════════╝
```

## 8. project.yaml 完整示例

```yaml
# .tlo/project.yaml

project:
  id: "web-automation"
  name: "鞍集涂源管理系统"

application:
  type: "web"
  tech_stack:
    frontend:
      framework: "vue3"
      ui_library: "element-plus"
      css_framework: "tailwindcss"
      routing: "hash"
      state_management: "pinia"
      typescript: true
    backend:
      api_style: "rest"
  auth:
    method: "form"

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
