# Skill: requirement-analysis

## 目标
**无 PRD 模式**：从现有 Page Object 代码 + 测试脚本 + 可选 BrowserUse DOM 观测反推页面需求，生成测试视角的页面上下文文档。

**PRD 模式**（备用）：从 PRD/原型图识别需求风险。触发条件：用户提供了 PRD 文本。

## 输入
- Page Object 代码：`ZJSN_Test-master526/page/<module>_page/<PageName>Page.py`
- 测试脚本：`ZJSN_Test-master526/script/<module>/test_<page>.py`
- MODULE_CONTEXT.md（如有）
- （可选）PRD / 产品说明
- （可选）BrowserUse 页面观测结果

## 输出
- PAGE_CONTEXT.md — 页面元素清单 + 业务规则 + 测试范围（基于真实代码/DOM）
- PAGE_INTERFACE.yaml — 页面接口描述

## 执行模式

### 模式 A：代码反推（默认，无 PRD 时）
1. 读取 Page Object 代码 → 提取：搜索字段、表格列、操作按钮、弹窗字段
2. 读取测试脚本 → 理解：测试场景、断言、数据流
3. （可选）调用 page-observe → 获取实时 DOM 结构
4. 生成 PAGE_CONTEXT.md

### 模式 B：PRD 分析（有 PRD 时）
1. 阅读 PRD → 提取业务规则
2. 生成需求分析文档
3. 标记"待产品确认"项

## 规则
- **禁止编造元素**：所有 UI 元素必须从 PO 代码或 DOM 观测中提取
- 元素类型识别：el-input / el-select / el-date-picker / el-table / el-button 等
- 定位器来源标注：代码提取 / DOM 观测 / 待确认
- 不确定的业务规则标注"代码中未体现，待确认"
- **优先代码，其次 DOM 观测，最后才标注"待确认"**

## 依赖
- workflows/sop-summary.md (§ Phase 0.8)
- skills/test-design/page-observe.md（BrowserUse DOM 观测，可选）

## 边界
- 本 Skill 不产出 MODULE_CONTEXT.md（那是 module-modeling 的职责）
- 本 Skill 不产出详细测试用例（那是 testcase-design 的职责）
- 本 Skill 不产出代码（那是 page-object-generator 的职责）
- **无 PRD 时不虚构需求，从代码实事求是反推**

---

## Prompt 模板

### 模式 A：从代码反推页面上下文（无 PRD）

```text
你是一个测试工程师。该项目**没有 PRD**。

## 重要提示
**Page Object 代码和测试脚本已自动注入到你的上下文中**（见下方分隔线后的代码块）。
请直接分析这些代码，提取真实的页面元素、定位器和测试场景。
**禁止编造**任何不存在于代码中的元素名、选择器或页面结构。

## 任务
为页面 `{{page}}`（模块 `{{module}}`）生成 PAGE_CONTEXT.md 和 PAGE_INTERFACE.yaml。

## 步骤

### 第一步：分析已注入的代码
在下方分隔线后，你会找到：
1. **[Page Object 代码]** — 包含真实的定位器、方法、URL 注释
2. **[测试脚本]** — 包含真实的测试场景、fixture、断言
3. **[模块上下文]** — MODULE_CONTEXT.md（如有）

从这些代码中提取：
- 所有定位器常量（如 `FILTER_XXX`, `BTN_XXX`）→ 识别页面元素
- `navigate()` 方法 → 识别页面路由和菜单路径
- `click_*()` / `input_*()` 方法 → 识别操作
- 测试函数名和断言 → 识别验证点

### 第二步：逐区域分析
基于代码中的真实定位器，分析：

#### 搜索/筛选区
- 列出每个输入控件：标签名、控件类型（从 Element Plus 组件推断）、定位器
- 列出操作按钮：查询、重置、新增等

#### 表格/列表区
- 列出所有列标题（从 PO 的表格列定义提取）
- 每列的数据类型
- 操作列按钮：编辑、删除、详情等

#### 弹窗/对话框
- 弹窗标题、触发方式
- 弹窗内表单字段
- 弹窗按钮

#### 分页区
- 是否有分页组件

### 第三步：生成 PAGE_CONTEXT.md

输出到 `governance/context/projects/web-automation/modules/{{module}}/pages/{{page}}/PAGE_CONTEXT.md`。

格式：
```markdown
# {{page_name}} — 页面上下文

## 页面信息
- 路由: {{从 PO 注释提取}}
- Page Object: {{PageName}}Page
- 测试脚本: test_{{page_underscore}}.py

## 搜索/筛选区
| 序号 | 元素 | 标签 | 类型 | 定位器 | 来源 |
|-----|------|-----|------|-------|------|
| 1 | {{字段名}} | {{标签}} | el-input | {{定位器}} | 代码 |

## 表格列定义
| 序号 | 列标题 | 数据类型 | 来源 |
|-----|-------|---------|------|
| 1 | {{列名}} | 文本 | 代码 |

## 操作按钮
| 按钮 | 触发动作 | 来源 |
|------|---------|------|
| 查询 | 触发搜索 | 代码 |

## 弹窗
（如 PO 中有弹窗定义）
| 弹窗 | 触发方式 | 表单字段 | 来源 |
|------|---------|---------|------|

## 业务规则（从代码推断）
| 规则 | 推断依据 | 置信度 |
|------|---------|-------|
| {{规则描述}} | PO 代码行 N / test 断言 | 高/中/低 |

## 测试场景映射
（从 test_*.py 提取）
| 测试函数 | 场景描述 | 验证点 |
|---------|---------|-------|
| test_xxx | {{场景}} | {{断言}} |
```

### 第四步：生成 PAGE_INTERFACE.yaml

```yaml
page: {{page}}
route: {{从 PO 提取}}
elements:
  search:
    - name: {{字段名}}
      label: {{标签}}
      type: el-input
      locator: {{定位器}}
  table_columns: [...]
  buttons: [...]
```

## 约束
- 所有元素必须有代码依据（标注来源行号）
- 无法从代码确定的标注"代码未体现，待 DOM 观测"
- 不确定的业务规则标注"待确认"
- Element Plus 组件类型必须准确（el-input / el-select / el-date-picker / el-switch 等）
```

---

## 检查清单

- [ ] PAGE_CONTEXT.md 中所有元素有代码依据
- [ ] 搜索区字段完整（从 PO 提取）
- [ ] 表格列定义完整（从 PO 提取）
- [ ] 操作按钮完整
- [ ] 弹窗/对话框完整（如存在）
- [ ] 业务规则有推断依据
- [ ] 测试场景映射从 test_*.py 实际提取
- [ ] 不确定项已标注"待确认"
- [ ] PAGE_INTERFACE.yaml 生成正确
- [ ] 无编造内容

---

## 产出物
→ `PAGE_CONTEXT.md` + `PAGE_INTERFACE.yaml`，存放至 `governance/context/projects/web-automation/modules/<module>/pages/<page>/`。
<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->
<!-- Source: skill-registry -->
> **1.1** | active | requirements | synced 2026-06-17
<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->
