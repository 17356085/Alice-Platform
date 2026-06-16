# TECH_ANALYSIS — personnel / contractor-personnel

## 分析对象
- 模块：personnel
- 页面：承包商人员
- 自动化目标：覆盖搜索/CRUD/分页的 Page Object（`ContractorPersonnelPage`），**含特殊侧边栏导航逻辑**
- 路由：`#/personnel/contractor`（与单位共用，侧边栏切换视图）

## 技术要点

### Element Plus 组件识别
| 组件类型 | 用途 | 特殊性 |
|----------|------|--------|
| el-input | 姓名/身份证搜索框 | card 搜索区内 |
| el-select | 所属承包商下拉、入场状态下拉 | card 搜索区内 |
| el-card (search-wrapper) | 搜索区容器 | 非标准表格搜索区，**.search-wrapper** class |
| el-table | 承包商人员列表 | card+table 混合布局 |
| el-dialog | 新增/编辑弹窗 | 含姓名/身份证/单位/岗位/手机等字段 |
| el-pagination | 分页器 | 标准 |
| el-menu-item.nest-menu | 侧边栏-承包商人员 | **无独立href**，点击切换内部视图 |

### 定位器设计表
| 元素 | 策略 | 定位值 | 稳定性 | 备注 |
|------|------|--------|--------|------|
| 姓名搜索框 | XPATH | `//input[contains(@placeholder,"姓名") or contains(@placeholder,"身份证")]` | A | card区内 |
| 所属单位下拉 | XPATH | `//div[contains(@class,"search-wrapper")]//div[contains(@class,"el-select")][.//span[contains(.,"承包商") or contains(.,"单位")]]` | B | 限定 search-wrapper 范围 |
| 入场状态下拉 | XPATH | `//div[contains(@class,"search-wrapper")]//div[contains(@class,"el-select")][.//span[contains(.,"入场状态") or contains(.,"状态")]]` | B | |
| 侧边栏-承包商人员 | XPATH | `//li[contains(@class,"el-menu-item")][contains(.,"承包商人员")]` | B | **必须先展开父级 sub-menu** |
| 搜索按钮 | BasePage | `self.click_search_button()` | A | |
| 重置按钮 | BasePage | `self.click_reset_button()` | A | |
| 新增按钮 | XPATH | `//button[contains(.,"新增")]` | A | |
| 表格行 | BasePage | `self.TABLE_ROWS` | A | |
| 弹窗操作 | BasePage | 继承 `fill_dialog_input/select_dialog_dropdown/click_dialog_save` | A | |

### 侧边栏导航策略（关键）
```
Step 1: JS hash → #/personnel/contractor
Step 2: SidebarNavigator.navigate_to("人员管理", "承包商管理", "承包商人员")
        → 展开 人员管理 → 展开 承包商管理 → 点击 nest-menu 承包商人员
```

**失败回退**：
- 如果直接 DOM click 失败（子菜单未展开），conftest 调用 `nav.navigate_to()` 走完整 sidebar 展开路径
- `navigate_to` 无 HREF_TO_PATH 映射时会回退到侧边栏点击逻辑

### 异步等待策略
| 场景 | 等待条件 | 代码 |
|------|----------|------|
| 视图切换 | Vue稳定 + loading消失 | `wait_vue_stable()` + `_wait_loading_gone(10)` |
| 页面加载 | 表格出现 | `is_page_loaded()` 检查 `.el-table` |
| 侧边栏展开 | sub-menu title 可点击 | `SidebarNavigator._click_submenu_title()` |
| 弹窗 | 标准 dialog 等待 | `wait_dialog_open/close` |

## 实现建议
- Page Object：`ContractorPersonnelPage(BasePage)`，navigate() 包含两步导航
- conftest 特殊处理：`_navigate_for_module` 中为 `test_contractor_personnel` 添加 sidebar click 逻辑
- 清理策略：`conftest._teardown_contractor_personnel()` 导航+搜索+删除，finally 执行

## 风险与限制
- **导航依赖 DOM 状态**：侧边栏 nest-menu 项的可见性依赖父级 sub-menu 展开状态
- **card 搜索区**：与标准表格搜索区结构不同，定位器需限定 `.search-wrapper` 范围
- **无独立路由**：JS hash 直接跳转始终显示单位视图，人员视图必须 sidebar 辅助
- **所属单位下拉依赖**：选择承包商单位时需要目标数据已存在
