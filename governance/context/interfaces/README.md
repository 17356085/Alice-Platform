# Agent 间结构化接口

> 替代「下游 Agent 通读上游 Markdown 文档」模式，
> 减少 Token 消耗，提升信息传递准确性。

## 已实现

- [page-to-automation.schema.yaml](page-to-automation.schema.yaml) — test-design-agent → automation-agent
  - 字段: meta (模块/页面元信息) + elements (核心交互元素) + test_scenarios (场景摘要) + page_behaviors (行为特征)
  - 版本: 1.0 (2026-06-12)
  - 生成: test-design-agent 在每个页面分析完成后自动生成 `PAGE_INTERFACE.yaml`
  - 消费: automation-agent 优先消费 `PAGE_INTERFACE.yaml`，不存在时降级到 Markdown

## 规划中

- `execution-to-bug-analysis.schema.yaml` — execution-agent → bug-analysis-agent（失败用例摘要）
  - 待实现: 结构化的失败用例信息 (测试名/异常类型/报错摘要/失败截图路径)
  - 预期收益: bug-analysis-agent Token 节省 30%

- `automation-to-execution.schema.yaml` — automation-agent → execution-agent（测试清单）
  - 待实现: 结构化的测试执行清单 (测试文件路径/pytest mark/预期耗时/依赖项)
  - 预期收益: execution-agent 运行策略优化

## 设计原则

1. **增量产物**：结构化接口文件是 Markdown 文档的**补充**，不是替代
2. **向后兼容**：消费方检测接口文件存在时优先使用，不存在时降级到 Markdown
3. **只包含消费方实际需要的字段**：避免过度设计，按需迭代
4. **YAML 格式**：人类可读 + 机器可解析，无需额外工具

## 如何新增接口

1. 识别高频 Agent 对（test-design→automation 是最频繁的一对）
2. 分析下游 Agent 实际需要哪些信息（不需要完整 Markdown）
3. 在 `governance/context/interfaces/` 下创建 `.schema.yaml`
4. 修改上游 Agent 的 workflow 增加接口产出步骤
5. 修改下游 Agent 的 workflow 增加接口优先消费逻辑
6. 更新 `governance/context/source-of-truth.md`
