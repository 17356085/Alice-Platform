# AUTO_STRATEGY — sales / contract

> 基于 TECH_ANALYSIS + TEST_CASES + 现有代码 | 2026-06-12

## 自动化目标
覆盖合同管理页面的稳定功能：页面展示、搜索筛选、表格分页、进度条渲染、状态标签、新增合同。
编辑/状态流转/审批因部分依赖 Element Plus Select Teleport，渐进式覆盖。

## 推荐策略
- 脚本层级：ContractPage（40KB PO）→ conftest.py → test_contract*.py（5个文件）
- 断言层级：页面级（元素可见/标签颜色） + 数据级（表格内容/进度条%）+ 流程级（状态流转）
- 数据策略：`_generate_contract_test_data()` + `_pick_existing_customer()` 关联已有客户
- 清理策略：API DELETE 清理 + fixture teardown
- 特殊处理：进度条断言前等待3s动画完成

## 覆盖矩阵

| 用例编号 | 标题 | 优先级 | 自动化 | 理由 |
|----------|------|--------|--------|------|
| TC-CTRT-001 | 页面正常加载 | P0 | ✅ | 冒烟必测 |
| TC-CTRT-002 | 表格列完整性 | P0 | ✅ | 8列校验 |
| TC-CTRT-003 | 无权限URL拦截 | P0 | ✅ | RBAC冒烟 |
| TC-CTRT-004~007 | 搜索筛选(4条) | P1 | ✅ | CSS placeholder 定位器 A级 |
| TC-CTRT-008 | 日期范围筛选 | P1 | 🔄 | DatePicker popper 需适配 |
| TC-CTRT-009 | 组合搜索 | P1 | 🔄 | 待开发 |
| TC-CTRT-010 | 重置搜索 | P1 | ✅ | 已实现 |
| TC-CTRT-012 | 状态标签颜色 | P1 | ✅ | STATUS_TAG_MAP 驱动 |
| TC-CTRT-013 | 进度条渲染 | P1 | ✅ | 等待3s动画后断言 |
| TC-CTRT-016 | 新增弹窗打开 | P1 | ✅ | 已实现 |
| TC-CTRT-017 | 必填项校验 | P1 | 🔄 | Select popper 问题 |
| TC-CTRT-018~019 | 新增提交/取消 | P1 | ✅ | 已实现 |
| TC-CTRT-020~021 | 金额/日期校验 | P1 | ❌ | 待开发 |
| TC-CTRT-022~023 | 分页 | P1 | ✅ | test_contract_pagination.py |
| TC-CTRT-025~027 | 编辑(回显/保存/取消) | P1 | ⚠️ | 非金额字段可用 |
| TC-CTRT-028 | 已生效金额保护 | P1 | ❌ | 待开发 |
| TC-CTRT-029 | 草稿→生效中 | P1 | ✅ | test_contract_workflow.py |
| TC-CTRT-030~037 | 状态流转/P2边缘 | P1/P2 | 🔄/❌ | 部分已覆盖，部分手工 |

## PageObject 拆分

```
ContractPage  ← 搜索区 + 表格(含进度条/标签) + 分页 + 新增弹窗（40KB）
  ├── 搜索区：编号/客户输入 + 产品/状态下拉 + 日期范围 + 查询/重置/新增
  ├── 表格区：8列（含 el-progress + el-tag）+ 行操作（详情/销售订单）
  ├── 弹窗区：新增/编辑表单（客户/产品/金额/日期/附件）
  └── 状态常量：STATE_TERMINATED/COMPLETED + STATUS_TAG_MAP

(ContractDialog) ← 编辑弹窗/审批弹窗（部分标记 TODO）
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
| select_option() | ElementPlusHelper | ⚠️ filterable 不稳定 |
| get_table_data() | ElementPlusHelper | ✅ |
| get_pagination_info() | ElementPlusHelper | ✅ |

## ROI 分析

| 指标 | 值 |
|------|----|
| 已投入开发时间 | ~4 小时（40KB PO + 5 测试文件） |
| 维护成本 | ~0.5 小时/月（状态/标签映射表可能微调） |
| 手工执行时间 | 20 分钟/次（含状态流转验证） |
| 执行频率 | 每次部署 + 每周回归 |
| 年化 ROI | 20min × 52次 − 4h − 0.5h×12 = 约 7 小时节省 |
| 当前状态 | P0/P1 稳定，编辑/审批 依赖 Select Teleport 适配 |

## 遗留技术债

1. **el-progress 动画同步**：3s 硬等待，应改为 `wait.until` 检测进度条宽度稳定
2. **日期范围选择器**：DatePicker range popper body 层渲染，需研究 ElementPlusHelper 扩展
3. **合同金额精度**：浮点数比较需统一使用 decimal 或 round()

---

<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-12 | next_phase: Phase 4 | next_agent: automation-agent -->
