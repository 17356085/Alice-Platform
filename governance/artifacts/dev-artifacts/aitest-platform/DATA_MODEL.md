## 工具调用结果分析

所有 RAG 相关工具均返回 `No available provider`，说明知识库服务当前不可用：

| 工具 | 结果 |
|------|------|
| `rag.search` (known_issues) | ❌ No provider |
| `rag.search` (historical_failures) | ❌ No provider |
| `rag.business_rules` | ❌ No provider |

---

## 需要你的输入

由于知识库不可用，我无法自动检索已有的功能规格文档。要生成 `DATA_MODEL.md`，请直接提供以下任一内容：

**选项 A：** 粘贴 `FEATURE_SPEC.md` 的完整内容

**选项 B：** 简要描述需求，例如：
> 这是一个仓储管理系统（WMS），核心实体包括：仓库、库位、物料、入库单、出库单、库存流水。入库单需要关联供应商，出库单关联客户。每个库位最多存放一种物料，库存变动需要记录流水。

**选项 C：** 如果已有 `API_CONTRACTS.md`，也可以一并提供，我会从中提取实体关系。

---

收到需求后，我会按以下结构产出 `DATA_MODEL.md`：

1. **Mermaid ERD 图** — 实体关系可视化
2. **实体定义表** — 字段名、类型、必填、默认值、外键引用
3. **关系标注** — 1:1 / 1:N / N:N
4. **索引建议** — 唯一索引、查询索引

请提供需求内容，我立即开始。