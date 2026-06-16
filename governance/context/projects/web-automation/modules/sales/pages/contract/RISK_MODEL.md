# RISK_MODEL — sales / contract

## 页面/模块
- 名称：合同管理 | 所属模块：sales（销仓管理）
- 路由：`#/sales/contract`
- 自动化代码：`page/sales_page/ContractPage.py` (40KB) + `script/sales/test_contract*.py` (6个测试文件)

## 风险清单

| 风险ID | 维度 | 风险描述 | 影响 | 等级 | 缓解措施 | 自动化覆盖 |
|--------|------|----------|------|------|----------|-----------|
| RISK-CTRT-001 | 业务 | 合同金额计算错误导致财务数据偏差 | 高 | P0 | 金额参数化校验 + 后端精度统一(decimal)；合同金额=已执行+未执行交叉验证 | ❌ |
| RISK-CTRT-002 | 业务 | 已生效合同被误修改金额导致历史数据不一致 | 高 | P0 | 已生效合同金额字段只读；后端状态机校验拒绝修改 | ❌ |
| RISK-CTRT-003 | 业务 | 合同状态逆向流转（已完成→生效中）破坏业务规则 | 中 | P1 | 后端状态机严格单向：草稿→生效中→已完成/已终止，禁止逆向 | ❌ |
| RISK-CTRT-004 | 业务 | 销售订单超卖——订单净重超过关联合同剩余可执行量 | 高 | P0 | 后端下单时校验：累计订单量≤合同总量；前端实时显示剩余量 | ✅ test_sales_order (超卖防护) |
| RISK-CTRT-005 | 权限 | 销售员创建/修改合同（应仅销售经理+admin可操作） | 中 | P1 | 后端接口角色鉴权；前端按钮级权限控制 | ✅ test_rbac |
| RISK-CTRT-006 | 数据 | 关联客户被删除后合同客户字段成为孤儿引用 | 高 | P0 | 客户删除时级联校验是否存在生效中合同；外键约束 | ❌ |
| RISK-CTRT-007 | 数据 | 合同日期逻辑错误——有效期止早于有效期起 | 中 | P1 | 前端日期选择器 min/max 联动 + 后端校验 | ❌ |
| RISK-CTRT-008 | 数据 | 合同金额输入负数或非数字 | 中 | P1 | 前端 min=0 + number 类型校验；后端>0约束 | ❌ |
| RISK-CTRT-009 | 数据 | 合同编号重复提交 | 中 | P1 | 后端唯一索引；前端异步校验编号唯一性 | 🔄 test_contract_search |
| RISK-CTRT-010 | 接口 | 合同审批接口超时导致状态卡在"审批中" | 中 | P1 | 前端设置审批超时(30s) + 超时后轮询状态 | ❌ |
| RISK-CTRT-011 | UI/UX | el-progress 进度条 3s CSS 动画导致断言时机不准 | 中 | P1 | 等待动画完成后断言（wait for transitionend 或固定延迟） | ✅ test_contract_display |
| RISK-CTRT-012 | UI/UX | el-tag 状态标签颜色映射错误（已终止=success 颜色） | 低 | P2 | 对照 STATUS_TAG_MAP 映射表验证 | ✅ test_contract_display |
| RISK-CTRT-013 | 性能 | 合同列表大数据量(>500条)下日期范围筛选+分页卡顿 | 低 | P2 | 后端分页 + 日期索引；前端 debounce 搜索 | 🔄 test_contract_pagination |
| RISK-CTRT-014 | 接口 | 合同附件上传失败但合同已创建——数据不完整 | 中 | P1 | 附件异步上传 + 失败重试队列；合同创建与附件解耦 | ❌ |

## 高风险路径

- 合同金额变更 → 未执行额重算 → 关联订单超卖校验（全链路 P0）
- 状态流转：草稿→生效中→已完成（不可逆，需全状态覆盖测试）
- 客户删除 → 关联合约客户字段 → 数据一致性校验

## 建议覆盖策略

- **必测（P0）**：金额计算（RISK-CTRT-001）、已生效合同金额保护（RISK-CTRT-002）、超卖防护（RISK-CTRT-004）、孤儿引用（RISK-CTRT-006）
- **优先自动化**：搜索/状态流转/进度条显示（定位器 A 级>70%，已在 6 个 test_contract*.py 中覆盖）
- **手工保留**：附件上传失败恢复（RISK-CTRT-014）、大屏/小屏分辨率适配

---

<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-12 | next_phase: Phase 2 | next_agent: test-design-agent -->
