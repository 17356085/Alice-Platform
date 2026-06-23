# AUTO_STRATEGY — personnel / entry-confirm

## 自动化范围
- **目标**: 入场确认页面自动化测试，覆盖列表/搜索/确认操作
- **优先级**: P0 — 承包商入场流程关键节点
- **预计用例数**: 8–10 条
- **预计开发时间**: 1 小时

## 自动化策略

### 用例选择
| 优先级 | 用例数 | 覆盖场景 |
|--------|:-----:|----------|
| P0 | 4 | 页面加载、搜索(承包商+人员)、单条确认入场、批量确认入场 |
| P1 | 3 | 组合搜索、重置、翻页 |
| P2 | 1 | 未选择记录点击批量确认 |

### 跳过策略
- 若表格中无"未读"记录，跳过 TC-EC-010（单条确认）和 TC-EC-011（批量确认）
- 若数据不足2条，跳过 TC-EC-011（批量确认）
- 若数据只有1页，跳过 TC-EC-006（翻页）

### 数据策略
- **不创建测试数据**（该页面无新增按钮）
- 依赖线上已审批通过的入场申请
- 确认操作**不可逆**，每次运行会消耗可确认记录

## Page Object 设计
```
EntryConfirmPage(BasePage)
├── 导航
│   └── navigate() → hash 导航
├── 搜索
│   ├── input_contractor_name(text)
│   ├── input_personnel_name(text)
│   ├── click_search()
│   └── click_reset()
├── 确认操作
│   ├── click_confirm_entry(name) → 行内确认入场
│   └── click_batch_confirm() → 批量确认入场
├── 复选框
│   ├── select_rows(names[]) → 勾选指定行
│   └── select_all_rows() → 全选
├── 读取
│   ├── get_table_headers() → 列头文本列表
│   ├── get_row_count() → 当前页行数
│   ├── get_cell(row, col) → 单元格文本
│   ├── get_personnel_names() → 所有人员姓名列表
│   └── get_unread_count() → 未读记录数
└── 等待
    └── is_page_loaded() → 表格+搜索区可见
```

## 定位器优先级
1. **placeholder 文本匹配** → 输入框（最稳定）
2. **按钮文本匹配** → 操作按钮
3. **JS textContent 搜索** → 行内操作（防 Element UI 遮挡）
4. **CSS class selector** → 分页器

## 风险缓释
- **不可逆操作** → 优先测试只读操作（搜索/列表），确认操作用例放在最后
- **数据依赖** → 每个确认操作用例前检查是否有可用记录
- **Element UI 遮挡** → 使用 `_js_click_by_text()` 绕过
