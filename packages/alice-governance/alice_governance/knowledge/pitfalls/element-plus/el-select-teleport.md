# el-select Teleport 渲染导致定位器失效

| 属性 | 值 |
|------|-----|
| 关联ID | EP-001, EP-002 |
| 严重度 | high |
| 复现率 | 95% |
| 出现次数 | 50+ |
| 首次发现 | 2026-01-15 |
| 最近出现 | 2026-06-17 |

## 现象

- `ElementClickInterceptedException`
- `NoSuchElementException` — 选项不在组件 DOM 树内
- `is_displayed()` 对下拉选项返回 `False`
- 点击下拉框后选项未出现

## 根因

Element Plus 将 `el-select` / `el-date-picker` / `el-dialog` 的下拉选项/面板 Teleport 到 `<body>` 末尾，脱离组件内部 DOM 树。Selenium 在组件内部查找选项时找不到。

## 解决方案

1. **body 级定位器**：使用 `body > .el-popper` 等 body 级选择器
2. **JS click 降级**：`driver.execute_script("arguments[0].click()", element)`
3. **使用 BasePage 封装方法**：`select_option()` / `click_element()` 已内置多级降级
4. **弹窗 CRUD 降级为 API 层**：如 el-select filterable 在弹窗中完全不可操作，改用 API 直接创建/删除数据

## 预防措施

- tech-analysis 阶段识别所有 el-select/el-date-picker 组件
- 为每个 filterable select 预设 JS click 降级方案
- CI 中增加"弹窗元素可交互性" smoke check

## 受影响模块

equipment, system-user, system-role, personnel, sales, system-management
