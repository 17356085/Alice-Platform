# Skill: page-observe

## 目标
通过 BrowserUse AI Agent 自动探索页面，提取页面结构（搜索字段/操作按钮/表格列/分页信息），
无需人工诊断 DOM 或手写选择器。作为 `page-analysis` Skill 的 BrowserUse 驱动后处理。

## 输入
- `page_hash`: Vue hash 路由，如 `#/warehouse/hazard/item`
- `page_name`: 页面中文名，如 "环保物品管理"
- `module_name`: 所属模块，如 "warehouse"

## 输出
- `PAGE_STRUCTURE.json` — 结构化页面描述
  ```json
  {
    "page_title": "物品管理",
    "search_fields": [{"label": "危废品名称", "type": "input", "html_hint": "placeholder: 请输入危废品名称"}],
    "action_buttons": [{"label": "查询", "css_hint": "button text: 查询"}],
    "table_columns": ["序号", "危废品名称", ...],
    "has_pagination": true,
    "has_checkbox_column": true
  }
  ```
- 数据注入到 `PAGE_CONTEXT.md`（`page-analysis` 后处理阶段）

## 规则
- 通过 `aitest.bu_adapter.BrowserUseSkillAdapter.observe_page_structure()` 调用
- BrowserUse 使用 hash-route 直接导航，不走侧边栏（更快更可靠）
- MiMo 默认启用 vision mode（2x 加速）
- 输出 JSON 自动校验：至少包含 1 个 search_field 和 1 个 button
- 失败时降级到现有 `page-analysis` 人工流程

## 依赖
- `aitest/bu_adapter.py` — BrowserUseSkillAdapter
- `ZJSN_Test-master526/base/bu_driver.py` — BrowserUseDriver
- Skills: `page-analysis`（前置，提供页面基本信息）
- `.env`: `BU_LLM_PROVIDER=mimo`, `MIMO_API_KEY`, `MIMO_BASE_URL`

## 边界
- 不生成代码（那是 `page-object-generator` 的职责）
- 不分析业务逻辑（那是 `requirement-analysis` 的职责）
- 不判断元素用途（那是 `tech-analysis` 的职责）
- 仅提取"页面有什么"，不提取"怎么定位"
- LLM 成本 ≤ $0.03/次（限制 max_steps=15）

## 触发方式

### 口语化触发
- "探索XX页面的元素"
- "自动分析XX页面结构"
- "用AI看看XX页面有什么"

### SOP 触发
- `test-design-agent` 的 `page-analysis` 后处理阶段自动调用
- `page-analysis` 执行完毕 → `page-observe` → 输出注入 `PAGE_CONTEXT.md`

### CLI 触发
```bash
aitest graph run --module=warehouse --pages=hazard-item --skills=page-observe
```

## Prompt 模板

```text
你是一个Web端自动化测试工程师，使用 BrowserUse AI Agent 自动探索页面。

## 任务
探索页面 {{page_name}}（路由: {{page_hash}}），提取页面结构。

## 步骤
1. 导航到 {{page_hash}}
2. 等待页面完全渲染（Vue 3 + Element Plus SPA）
3. 观察并提取：
   - 搜索/筛选区域的所有字段（label + type + html hint）
   - 所有操作按钮（文字 + CSS class hint）
   - 表格列定义（完整的列名列表）
   - 是否有分页组件
   - 是否有复选框列

## 输出格式
只输出一个 JSON 对象（不要 markdown 代码块，不要额外文字）：
{
  "page_title": "面包屑或页面标题",
  "search_fields": [{"label": "字段名", "type": "input|select|date", "html_hint": "placeholder或CSS"}],
  "action_buttons": [{"label": "按钮文字", "css_hint": "CSS class或属性"}],
  "table_columns": ["列1", "列2", ...],
  "has_pagination": true/false,
  "has_checkbox_column": true/false
}
```
<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->
<!-- Source: skill-registry -->
> **1.0** | active | test-design | synced 2026-06-18 10:54

<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->