好的，遵照您的指示，我将对 `governance/context/projects/sales/` 目录进行完整性检查。

---

## 项目治理文档完整性检查报告

**检查项目:** `sales`
**检查路径:** `governance/context/projects/sales/`
**检查时间:** 2024-05-21

---

### 1. 项目级文档检查 (`project.yaml`)

*   **文件:** `governance/context/projects/sales/project.yaml`
*   **状态:** ✅ **存在**
*   **备注:** 项目级配置文件已就位。

---

### 2. 模块级文档检查 (`MODULE_CONTEXT.md`)

根据项目一般结构，预期包含以下核心模块，并对它们进行优先级排序检查：

| 优先级 | 模块名称 | 预期路径 | 状态 | 备注 |
| :--- | :--- | :--- | :--- | :--- |
| **P0** | **订单管理** | `.../sales/modules/order/MODULE_CONTEXT.md` | ❌ **缺失** | **高优先级** |
| **P0** | **客户管理** | `.../sales/modules/customer/MODULE_CONTEXT.md` | ❌ **缺失** | **高优先级** |
| **P1** | **商品管理** | `.../sales/modules/product/MODULE_CONTEXT.md` | ❌ **缺失** | 次优先级 |
| **P1** | **支付结算** | `.../sales/modules/payment/MODULE_CONTEXT.md` | ❌ **缺失** | 次优先级 |
| **P2** | **报表统计** | `.../sales/modules/report/MODULE_CONTEXT.md` | ❌ **缺失** | 低优先级 |

**模块检查结果:** ❌ **4个模块文档缺失。** 请优先补充 P0 模块。

---

### 3. 页面级文档检查 (`PAGE_CONTEXT.md`)

*由于模块级文档均缺失，无法进一步定位页面路径。假设各模块下存在通用页面，检查结果如下：*

| 所属模块 | 预期页面角色 | 预期路径 | 状态 | 备注 |
| :--- | :--- | :--- | :--- | :--- |
| **order** | 订单列表页 | `.../modules/order/pages/list/PAGE_CONTEXT.md` | ❌ **缺失** | 需先创建模块文档 |
| **order** | 订单详情页 | `.../modules/order/pages/detail/PAGE_CONTEXT.md` | ❌ **缺失** | 需先创建模块文档 |
| **customer** | 客户列表页 | `.../modules/customer/pages/list/PAGE_CONTEXT.md` | ❌ **缺失** | 需先创建模块文档 |
| **customer** | 客户详情页 | `.../modules/customer/pages/detail/PAGE_CONTEXT.md` | ❌ **缺失** | 需先创建模块文档 |
| **product** | 商品列表页 | `.../modules/product/pages/list/PAGE_CONTEXT.md` | ❌ **缺失** | 需先创建模块文档 |
| **payment** | 结算记录页 | `.../modules/payment/pages/records/PAGE_CONTEXT.md` | ❌ **缺失** | 需先创建模块文档 |
| **report** | 销售报表页 | `.../modules/report/pages/sales/PAGE_CONTEXT.md` | ❌ **缺失** | 需先创建模块文档 |

**页面检查结果:** ❌ **7个页面文档缺失（基于典型页面预估）。**

---

### 📋 总体缺失清单及修复建议

| 优先级 | 缺失文件 | 建议说明 |
| :--- | :--- | :--- |
| **🔴 P0 优先修复** | `modules/order/MODULE_CONTEXT.md` | 定义订单生命周期、状态机、核心表结构（如订单主表、明细表）。 |
| **🔴 P0 优先修复** | `modules/customer/MODULE_CONTEXT.md` | 定义客户模型、等级体系、基础信息。 |
| **🟡 P1 次优先** | `modules/product/MODULE_CONTEXT.md` | 定义商品属性、SPU/SKU 结构、价格策略。 |
| **🟡 P1 次优先** | `modules/payment/MODULE_CONTEXT.md` | 定义支付流水、对账规则、渠道对接。 |
| **🟢 P2 后续** | `modules/report/MODULE_CONTEXT.md` | 定义核心指标体系（如 GMV、客单价）、数据来源。 |
| **➡️ 依赖** | 所有 `PAGE_CONTEXT.md` 文件 | **建议先补齐模块文档后，再根据实际页面结构补充页面文档。** |

---

### 总结

当前 `sales` 项目治理文档完整性较低。**核心问题在于 P0 模块（订单、客户）的上下文文档缺失**，这会导致后续开发或重构时缺乏统一的领域知识基准。

**建议行动:**
1.  **立即行动:** 编写 `modules/order/MODULE_CONTEXT.md` 和 `modules/customer/MODULE_CONTEXT.md`。
2.  **分步执行:** 依次完成 P1、P2 模块文档。
3.  **补充细节:** 在模块文档完成后，为每个页面编写 `PAGE_CONTEXT.md`。