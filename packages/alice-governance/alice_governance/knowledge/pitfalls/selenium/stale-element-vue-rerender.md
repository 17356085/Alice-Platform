# Vue 响应式更新导致 StaleElementReferenceException

| 属性 | 值 |
|------|-----|
| 关联ID | SE-001, FP-001 |
| 严重度 | high |
| 复现率 | 40% |
| 出现次数 | 28+ |
| 首次发现 | 2026-01-10 |
| 最近出现 | 2026-06-17 |

## 现象

- `StaleElementReferenceException`
- Vue 数据更新后，持有的 WebElement 引用失效
- 表格/列表刷新后元素无法继续操作

## 根因

Vue 3 响应式更新导致 DOM 节点被替换（而非原地修改），Selenium 持有的 `WebElement` 引用指向已销毁的 DOM 节点。

## 解决方案

1. **重新定位**：操作后重新 `find` 元素，避免持有长期引用
2. **BasePage 内置重试**：`click_element()` / `input_text()` 等方法已内置 retry 逻辑
3. **WebDriverWait + EC.refresh()**：等待 stale 恢复

## 预防措施

- Page Object 方法返回 `self`（链式调用时自动重新定位）
- 关键断言前用 `WebDriverWait` 确保 DOM 稳定

## 受影响模块

all
