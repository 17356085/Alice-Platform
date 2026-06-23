# AUTO_STRATEGY — sales / sales-order

> 基于 TECH_ANALYSIS + TEST_CASES + 现有代码 | 2026-06-12

## 自动化目标
覆盖销售订单页面的稳定功能：页面展示、搜索筛选、表格分页、新增订单（含级联下拉+超卖防护+浮点精度）、查看详情。

## 推荐策略
- 脚本层级：SalesOrderPage（31KB PO）→ conftest.py → test_sales_order*.py（4文件）
- 断言层级：页面级 + 数据级 + 业务规则级（超卖/精度/级联）
- 数据策略：`_generate_order_test_data()` 动态生成车牌号 `测A{timestamp[-6:]}`
- 清理策略：API DELETE + CleanupTracker
- 跨PO协作：test_sales_order.py 同时 import CustomerPage + ContractPage

## 覆盖矩阵

| 用例编号 | 标题 | 优先级 | 自动化 | 理由 |
|----------|------|--------|--------|------|
| TC-ORD-001 | 页面正常加载 | P0 | ✅ | 冒烟 |
| TC-ORD-002 | 客户合同级联 | P0 | ✅ | 核心业务规则 |
| TC-ORD-003 | 超卖防护 | P0 | ✅ | 核心业务规则 |
| TC-ORD-004 | 无权限URL拦截 | P0 | ✅ | RBAC |
| TC-ORD-005~007 | 搜索筛选(3条) | P1 | ✅ | placeholder A级定位 |
| TC-ORD-008~009 | 日期/组合搜索 | P1 | 🔄 | DatePicker popper |
| TC-ORD-010 | 重置搜索 | P1 | ✅ | |
| TC-ORD-012~013 | 标签颜色/列完整 | P1 | ✅ | test_sales_order_display.py |
| TC-ORD-014~017 | 新增(弹窗/提交/取消/精度) | P1 | ✅ | test_sales_order_crud.py |
| TC-ORD-018~019 | 必填项/格式校验 | P1 | 🔄/❌ | Select popper/待开发 |
| TC-ORD-020~022 | 单号点击/分页/详情 | P1 | ✅ | |
| TC-ORD-023 | 销售员权限 | P1 | 🔄 | 待多角色数据 |
| TC-ORD-024~025 | 接口超时/Token | P2 | ❌ | 手工 |

## PageObject 拆分

```
SalesOrderPage  ← 搜索区 + 表格(含el-tag) + 分页 + 新增弹窗（31KB）
  ├── 搜索区：单号/客户输入 + 产品下拉 + 日期范围 + 查询/重置/新增
  ├── 表格区：8列（单号可点击、产品el-tag）+ 详情按钮
  ├── 弹窗区：新增表单（客户→合同级联/净重/车牌）
  └── 浮点精度：round(x, 4) 统一
```

## 公共组件复用

| 方法 | 来源 | 复用状态 |
|------|------|----------|
| navigate_to() | BasePage | ✅ |
| wait_table_loaded() | BasePage | ✅ |
| wait_loading_disappear() | BasePage | ✅ |
| wait_dialog_visible() | BasePage | ✅ |
| input_text() | BasePage | ✅ |
| click_element() | BasePage | ✅ |
| select_option() | ElementPlusHelper | ⚠️ 级联场景不可靠 |

## ROI 分析

| 指标 | 值 |
|------|----|
| 已投入开发时间 | ~3 小时 |
| 维护成本 | ~0.5 小时/月 |
| 手工执行时间 | 15 分钟/次 |
| 年化 ROI | 15min × 52 − 3h − 0.5h×12 = 约 4 小时节省 |
| 当前状态 | P0/P1稳定，级联下拉/超卖防护核心已验证 |

---

<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-12 | next_phase: Phase 4 | next_agent: automation-agent -->
