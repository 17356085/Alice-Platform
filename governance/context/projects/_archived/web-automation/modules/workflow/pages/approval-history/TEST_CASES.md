好的，收到您的任务。为了产出高质量、可直接用于测试的 `TEST_DESIGN.md` 和 `TEST_CASES.md`，我需要基于您提供的真实上下文，而不是通用示例。

请您提供以下**核心输入**：

1.  **`MODULE_CONTEXT.md`**: 描述 `workflow` 模块的整体业务、该页面在模块中的定位、上下游页面关系。
2.  **`PAGE_CONTEXT.md`**: 描述 `approval-history` 页面的具体UI、功能、交互方式、数据来源。
3.  **`BUSINESS_SCENARIOS.md`**: （您提到的P2-5风险建模输出），描述该页面的核心业务目标、角色旅程、工作流、业务规则和数据流。
4.  **需求说明**：最新的、明确的业务和功能需求。
5.  **历史缺陷**：该页面或模块之前出现的典型bug。

一旦您提供上述材料，我将严格按照您提供的 System Prompt 和 `templates/test-design.template.md`、`templates/test-cases.template.md` 格式，为您产出：

-   **`TEST_DESIGN.md`**：包含9个测试维度的完整设计方案（含业务场景验证与Risk Model映射）。
-   **`TEST_CASES.md`**：可执行的详细测试用例表（含具体的测试数据、P0/P1/P2覆盖率检查、自动化状态标注）。
-   **自动化优先级建议**：哪些场景适合自动化，哪些不适合。

**请直接粘贴上述文档内容或提供文件路径，我将立即开始工作。**