# TECH_ANALYSIS — personnel / entry-confirm

## 分析对象
- 模块：personnel
- 页面：入场确认
- 自动化目标：覆盖列表/搜索/确认入场（单条+批量）的 Page Object（`EntryConfirmPage`）
- 路由：`#/personnel/contractor/confirm`

## 技术要点

### Element Plus 组件识别
| 组件类型 | 用途 | 特殊性 |
|----------|------|--------|
| el-input | 承包商名称搜索、人员姓名搜索 | 标准搜索区 |
| el-button | 搜索/重置/批量确认入场/确认入场/清空缓存 | 文字区分 |
| el-table | 入场确认列表 | 9列含复选框 |
| el-checkbox | 行复选框 | 第1列，批量选择 |
| el-tag | 未读/已读状态标签 | 未读=橙色/已读=绿色 |
| el-pagination | 分页器 | 标准 |
| el-dialog | 确认弹窗 | 确认入场时可能弹出确认框 |

### 定位器设计表
| 元素 | 策略 | 定位值 | 稳定性 | 备注 |
|------|------|--------|--------|------|
| 承包商名称搜索框 | XPATH | `//input[contains(@placeholder,"承包商名称") or contains(@placeholder,"承包商")]` | A | |
| 人员姓名搜索框 | XPATH | `//input[contains(@placeholder,"人员姓名") or contains(@placeholder,"人员")]` | A | |
| 搜索按钮 | XPATH | `//button[.//span[contains(text(),"搜索")]]` | A | |
| 重置按钮 | XPATH | `//button[.//span[contains(text(),"重置")]]` | A | |
| 批量确认入场按钮 | XPATH | `//button[.//span[contains(text(),"批量确认入场")]]` | A | |
| 确认入场按钮(行内) | JS | `_js_click_by_text("确认入场")` | B | 同 contractor 页面模式 |
| 表格列头 | XPATH | `//div[contains(@class,"el-table__header-wrapper")]//th//div[contains(@class,"cell")]` | A | |
| 行复选框 | XPATH | `//tr[contains(@class,"el-table__row")][.//td[contains(.,"{name}")]]//input[@type="checkbox"]` | B | 动态参数化 |
| 分页器 | CSS | `.el-pagination` | A | |

### 异步等待策略
| 场景 | 等待条件 | 代码 |
|------|----------|------|
| 页面加载 | 表格出现 | `is_page_loaded()` 检查 `.el-table` |
| 确认操作完成 | toast + Vue稳定 | `get_toast_text(10)` + `wait_vue_stable()` |
| 搜索刷新 | Vue稳定 | `wait_vue_stable()` |
| 翻页 | 表格内容变化 | `wait_vue_stable()` |

## 实现建议
- Page Object：`EntryConfirmPage(BasePage)`，专注确认操作
- **无CRUD操作**：不创建/编辑/删除，仅确认已有入场记录
- 数据依赖：需线上存在"未读"记录，无则跳过确认用例
- 清理策略：无（确认操作不可逆）
- 复选框交互：使用 JS click 绕过 Element UI checkbox 遮挡

## 风险与限制
- **数据依赖**：确认入场依赖"未读"记录存在，线上数据变化可能导致用例跳过
- **不可逆操作**：确认入场后无法撤销，批量确认需谨慎
- **批量确认**：需先确认有≥2条"未读"记录，否则用例跳过
- **el-checkbox**：可能有 Element Plus 原生点击拦截，需 JS click 绕过
