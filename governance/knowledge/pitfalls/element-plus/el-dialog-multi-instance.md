# el-dialog 多弹窗共存导致定位器选错

| 属性 | 值 |
|------|-----|
| 关联ID | EP-011, FP-003 |
| 严重度 | high |
| 复现率 | 60% |
| 出现次数 | 50+ |
| 首次发现 | 2026-01-05 |
| 最近出现 | 2026-06-10 |

## 现象

- dialog 定位器选中已关闭的隐藏弹窗
- 操作了 `display:none` 弹窗中的元素导致 `ElementNotInteractableException`
- Element Plus 2.x 升级后弹窗定位器完全失效（结构从 `el-dialog__wrapper` 变为 `el-overlay`）

## 根因

1. Element Plus 关闭弹窗后不移除 DOM，仅添加 `display:none`
2. 多弹窗叠加时，定位器可能匹配到隐藏的弹窗
3. 2.x 版本使用 `el-overlay` + `el-dialog` 结构，与 1.x 的 `el-dialog__wrapper` 不兼容

## 解决方案

1. **排除隐藏弹窗**：定位器加 `not(contains(@style,'display: none'))` 筛选
2. **双结构兼容**：
   ```
   优先: .el-overlay:not([style*='display:none']) .el-dialog
   兜底: .el-dialog__wrapper:not([style*='display:none']) .el-dialog
   ```
3. **BasePage 已封装**：`DIALOG = (By.CSS_SELECTOR, ".el-dialog:not([style*='display: none'])")`

## 预防措施

- 新增弹窗操作方法默认使用 `not(style*='display:none')` 筛选
- code-consistency-checker 检查弹窗定位器是否包含 display:none 排除条件

## 受影响模块

all (所有含弹窗的页面)
