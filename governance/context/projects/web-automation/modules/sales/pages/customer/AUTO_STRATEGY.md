# AUTO_STRATEGY — sales / customer

> 基于 TECH_ANALYSIS + TEST_CASES + 现有代码 | 2026-06-12

## 自动化目标
覆盖客户管理页面的稳定功能：页面展示、搜索筛选、表格分页、查看详情。
弹窗 CRUD（新增/编辑/必填校验）因 Element Plus Select popper Teleport 渲染时序问题，当前标记 TODO，待 ElementPlusHelper 扩展方案。

## 推荐策略
- 脚本层级：CustomerPage（主页面 PO）→ conftest.py（fixture 工厂）→ test_customer*.py（4个测试文件）
- 断言层级：页面级（元素可见/按钮权限）+ 数据级（表格内容/列数据）+ API级（弹窗CRUD绕过UI验证）
- 数据策略：`_generate_customer_test_data()` 动态生成 `C{timestamp}` 编码 + `测试客户_{timestamp}` 名称
- 清理策略：module 级变量传递标识 → API DELETE 清理 → 失败只 warn
- 特殊处理：`retry_on_stale(max_retries=2)` 装饰器处理 Vue SPA keep-alive StaleElement

## 覆盖矩阵

| 用例编号 | 标题 | 优先级 | 自动化 | 理由 |
|----------|------|--------|--------|------|
| TC-CUST-001 | 页面正常加载 | P0 | ✅ | 冒烟必测，navigate() + wait_table_loaded() |
| TC-CUST-002 | 表格列完整性 | P0 | ✅ | 表头 data-driven 校验 |
| TC-CUST-003 | 删除确认弹窗 | P0 | ✅ | 删除前二次确认，定位器稳定 |
| TC-CUST-004 | 无权限URL拦截 | P0 | ✅ | RBAC冒烟，test_rbac |
| TC-CUST-005~008 | 搜索筛选(4条) | P1 | ✅ | placeholder/CSS定位器 A级稳定 |
| TC-CUST-009 | 组合搜索 | P1 | 🔄 | 待开发 |
| TC-CUST-010 | 重置搜索 | P1 | ✅ | 已实现 |
| TC-CUST-011 | 无结果搜索 | P2 | ✅ | 已实现 |
| TC-CUST-012 | 空数据加载 | P1 | 🔄 | 需清空数据环境 |
| TC-CUST-013 | 仅查看权限加载 | P1 | ✅ | 已有角色差异验证 |
| TC-CUST-014 | 新增弹窗-打开 | P1 | ✅ | 已实现 |
| TC-CUST-015 | 必填项校验 | P1 | 🔄 | Select popper 问题，标记 TODO |
| TC-CUST-016 | 新增提交成功 | P1 | ⚠️ 部分 | Select 下拉可用时通过，否则标记 TODO |
| TC-CUST-017 | 新增取消 | P1 | ✅ | 已实现 |
| TC-CUST-018 | 新增编码重复 | P1 | 🔄 | 待开发 |
| TC-CUST-019~020 | 分页 | P1 | ✅ | test_customer_pagination.py |
| TC-CUST-021 | 新增按钮可见 | P1 | ✅ | 元素存在性断言 |
| TC-CUST-022~024 | 编辑操作(3条) | P1 | ⚠️ 部分 | 同新增，Select 下拉制约 |
| TC-CUST-025 | 查看详情 | P1 | ✅ | 已实现 |
| TC-CUST-026 | 角色菜单差异 | P1 | 🔄 | 待多角色数据 |
| TC-CUST-027~035 | P2边缘场景 | P2 | ❌ | 手工或暂不需要 |

## PageObject 拆分

```
CustomerPage  ← 搜索区 + 表格 + 分页 + 查看详情（44KB，稳定已验证）
  ├── 搜索区：关键词输入 + 等级/状态下拉 + 查询/重置/新增按钮
  ├── 表格区：7列数据 + 行操作（查看/编辑/删除/资质维护）
  ├── 弹窗区：新增/编辑表单（11字段）+ 详情弹窗（只读）
  └── 分页区：总条数 + 每页条数 + 翻页

(CustomerDialog) ← 弹窗CRUD（标记 TODO，待 Element Plus 2.x Select Teleport 适配）
```

## 公共组件复用

| 方法 | 来源 | 复用状态 |
|------|------|----------|
| navigate_to() | BasePage | ✅ |
| wait_table_loaded() | BasePage | ✅ |
| wait_loading_disappear() | BasePage | ✅ |
| wait_dialog_visible() | BasePage | ✅ |
| input_text() | BasePage | ✅ |
| click_element() | BasePage (3级降级) | ✅ |
| select_option() | ElementPlusHelper | ⚠️ filterable Select 不可靠 |
| get_table_data() | ElementPlusHelper | ✅ |
| get_pagination_info() | ElementPlusHelper | ✅ |
| get_column_data() | BasePage | ✅ |

## 等待策略建议

- 搜索后：`wait_loading_disappear()` + `WebDriverWait` for `.el-table__row`
- 弹窗打开：`wait_dialog_visible()` + 额外等待弹窗内表单渲染
- Select 下拉：`WebDriverWait` for `.el-select-dropdown:not(.is-hidden)` in body
- Vue keep-alive：切换到其他标签页再回来时，`retry_on_stale` 自动重试

## ROI 分析

| 指标 | 值 |
|------|----|
| 已投入开发时间 | ~5 小时（44KB PO + 4 测试文件） |
| 维护成本 | ~0.5 小时/月（定位器稳定性 A级>70%） |
| 手工执行时间 | 15 分钟/次 |
| 执行频率 | 每次部署 + 每周回归 |
| 年化 ROI | 15min × 52次 − 5h − 0.5h×12 = 约 7 小时节省 |
| 当前状态 | P0/P1 稳定，弹窗CRUD 受限于 Element Plus Select Teleport |

## 遗留技术债

1. **el-select filterable + Teleport**：弹窗新增/编辑方法标记 TODO，需研究 ElementPlusHelper 扩展（JS 直接操作 body 层选项）
2. **多弹窗DOM共存**：新增/编辑/详情弹窗均保留在DOM中（display:none），需持续维护 `:not([style*="display: none"])` 过滤
3. **Vue keep-alive StaleElement**：`retry_on_stale` 装饰器是临时方案，长期应研究 `wait_vue_stable()` 统一处理

---

<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-12 | next_phase: Phase 4 | next_agent: automation-agent -->
