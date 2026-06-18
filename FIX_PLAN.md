# 库管模块失败修复计划

## Phase 1: 定位器稳定性修复（XPath → browser-use 诊断）

### 问题
- `click_row_button` XPath 行 794 使用 `contains(normalize-space(.),"{row_identifier}")`
- 新增用例生成带时间戳的名字（如 `测试人员_20260615163745`）
- 删除时搜索 `updated_name`（`测试人员_20260615163745_已修改`）
- **问题**: td 内可能有换行/空格，XPath 匹配不到

### 修复
1. 改 XPath: `translate(normalize-space(.), ' ', '') contains translate(...)`
2. 增等待: 从 10s → 15s + 重试 3 次
3. 强制滚动: 删除前滚动表格确保按钮可见

## Phase 2: Toast 消息可靠性改进

### 问题
- `wait_for_toast_text` 轮询间隔固定，可能 miss Toast（Vue 异步）
- 返回空串时，用例断言 `assert toast` 失败

### 修复
1. 增 retry: 主轮询 + 2 次重新等待（共 3 轮）
2. 改间隔: 从 0.5s → 0.2s + adaptive 等待
3. 改超时: 从 6s → 10s（给 Vue 更多时间）

## Phase 3: 表单项定位器修复

### 问题
- `_get_dialog_form_item` 查找失败
- 弹窗表单结构可能变化（Element Plus 升级后）

### 修复
1. 增备选选择器: label → div.el-form-item__label
2. 支持 i18n: 标签文本可能有隐藏字符
3. 滚动 form 项确保可见

## Phase 4: 稳定性改进

### 整体
1. 所有 click 都 scroll_into_view
2. 所有 wait 都 + 重试逻辑
3. 所有 find 失败都打 DEBUG 日志

---

## 优先级
1. **最紧急**: XPath 修复（超时 24.6% 失败）
2. **重要**: Toast 改进（断言失败 13.9%）
3. **后续**: 表单项修复（其他 5.6%）

## 预期效果
- 超时失败: 24.6% → 5%（XPath 改进后）
- 断言失败: 13.9% → 3%（Toast 改进后）
- 总通过率: 36.1% → 70%+

---

## 实施方式
1. 修改 `ZJSN_Test-master526/base/base_page.py` 的 3 个关键方法
2. 测试 3 个失败最多的用例
3. 全量 SOP 再跑一次
