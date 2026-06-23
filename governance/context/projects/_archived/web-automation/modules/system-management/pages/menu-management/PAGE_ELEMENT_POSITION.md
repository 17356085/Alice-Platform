# PAGE_ELEMENT_POSITION — system-management / menu-management

> 从 MenuManagePage.py 重构版代码提取 | 2026-06-11
> 页面类型: 树形表格 + Tab切换(PC/小程序)

## 搜索区

| 元素 | 策略 | 定位值 | 等级 |
|------|------|--------|:--:|
| 菜单名称输入 | XPATH | `//input[contains(@placeholder, "请输入菜单名称")]` | A |
| 搜索按钮 | XPATH | `//button[.//span[normalize-space(.)="搜索" or normalize-space(.)="查询"]]` | A |
| 重置按钮 | XPATH | `//button[.//span[normalize-space(.)="重置"]` | A |

## Tab 切换

| 元素 | 策略 | 定位值 | 等级 |
|------|------|--------|:--:|
| PC端菜单 | XPATH | `//span[contains(@class,"el-radio-button__inner") and normalize-space(.)="PC端菜单"]/ancestor::label[1]` | A |
| 小程序菜单 | XPATH | `//span[contains(@class,"el-radio-button__inner") and normalize-space(.)="小程序菜单"]/ancestor::label[1]` | A |

## 工具栏

| 元素 | 策略 | 定位值 | 等级 |
|------|------|--------|:--:|
| 新增 | XPATH | `//button[.//span[normalize-space(.)="新增"]]` | A |
| 展开全部 | XPATH | `//button[.//span[normalize-space(.)="展开全部"]]` | A |

## 树形表格

| 元素 | 策略 | 定位值 | 等级 |
|------|------|--------|:--:|
| 表头 | XPATH | `//div[contains(@class,"el-table__header-wrapper")]//th//div` | A |
| 表格行 | XPATH | `//div[contains(@class,"el-table__body-wrapper")]//table/tbody/tr` | B |
| 首行名称 | XPATH | `(//div[contains(@class,"el-table__body-wrapper")]//table/tbody/tr[1]/td[1]//div[contains(@class,"cell")])[1]` | B |
| 展开节点 | XPATH | 行内展开图标 | B |

## 复用 BasePage 定位器

| 元素 | 来源 |
|------|------|
| LOADING_MASK | BasePage |
| TOAST | BasePage |
| DIALOG | BasePage |

<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-11 -->
