# RISK_MODEL — sales / sales-order

## 页面/模块
- 名称：销售订单 | 所属模块：sales（销仓管理）
- 路由：`#/sales/order`
- 自动化代码：`page/sales_page/SalesOrderPage.py` (31KB) + `script/sales/test_sales_order*.py` (4个测试文件)

## 风险清单

| 风险ID | 维度 | 风险描述 | 影响 | 等级 | 缓解措施 | 自动化覆盖 |
|--------|------|----------|------|------|----------|-----------|
| RISK-ORD-001 | 业务 | 超卖——订单净重超过关联合同剩余可执行量 | 高 | P0 | 后端下单时实时校验：Σ订单量 ≤ 合同总量；前端显示剩余量 | ✅ test_sales_order (超卖防护) |
| RISK-ORD-002 | 业务 | 关联合同被终止/删除后历史订单数据失去关联 | 中 | P1 | 合同终止时校验是否存在未完成订单；保留历史关联只读 | ❌ |
| RISK-ORD-003 | 业务 | 客户选择后合同下拉未过滤——选了非该客户的合同 | 中 | P1 | 前端级联过滤：选择客户后合同下拉仅显示该客户合同 | ✅ test_sales_order (级联下拉) |
| RISK-ORD-004 | 数据 | 浮点数精度问题——净重0.0001吨差异导致汇总不一致 | 中 | P1 | 后端使用 decimal 类型；前端 round 到4位小数 | ✅ test_sales_order (浮点精度) |
| RISK-ORD-005 | 数据 | 车牌号输入格式不规范（含特殊字符或超长） | 低 | P2 | 前端车牌号正则校验；后端格式验证 | ❌ |
| RISK-ORD-006 | 数据 | 销售单号重复提交 | 中 | P1 | 后端唯一索引；前端异步校验 | 🔄 test_sales_order_search |
| RISK-ORD-007 | 权限 | 销售员删除/修改他人创建的订单 | 中 | P1 | 后端按创建人鉴权；前端按钮级控制 | 🔄 |
| RISK-ORD-008 | 接口 | 下单接口超时但后端已创建——重复提交风险 | 中 | P1 | 前端幂等键（idempotency key）防重复；后端去重 | ❌ |
| RISK-ORD-009 | UI/UX | 产品类型 el-tag 颜色映射错误（LNG=primary, 焦油=warning） | 低 | P2 | 对照颜色映射表验证 | ✅ test_sales_order_display |
| RISK-ORD-010 | 性能 | 订单列表大数据量+日期范围筛选性能 | 低 | P2 | 后端分页+日期索引；前端 debounce | 🔄 test_sales_order_search |
| RISK-ORD-011 | 业务 | 订单净重为0或负数仍可提交 | 中 | P1 | 前端 min>0 校验；后端>0约束 | ❌ |

## 高风险路径

- 新增订单 → 选客户 → 级联过滤合同 → 填净重 → 超卖校验 → 提交（全链路 P0）
- 订单汇总 → 合同已执行量更新 → 未执行额重算 → 超卖阈值动态变化
- 浮点精度：0.0001t 累计误差场景

## 建议覆盖策略

- **必测（P0）**：超卖防护（RISK-ORD-001）、级联下拉（RISK-ORD-003）、浮点精度（RISK-ORD-004）
- **优先自动化**：搜索/新增/显示/分页（定位器 A级>70%，已在4个test文件中覆盖）
- **手工保留**：接口超时幂等（RISK-ORD-008）、大屏/小屏适配

---

<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-12 | next_phase: Phase 2 | next_agent: test-design-agent -->
