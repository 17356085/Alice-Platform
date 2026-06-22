# Skill: pair-seed

## 目标
结对种子场景注入——让人类结对同学在 AI 生成测试用例前提供 2-5 个核心测试场景，AI 围绕种子扩展生成完整用例集。

## 输入
- PAIR_SEEDS.md（结对同学按模板填写，存放至对应页面目录）
- 或通过 Chat 界面交互式输入的种子场景

## 输出
- 校验报告（哪些种子有效/无效/需要补充）
- 注入标记：`pipeline_context.pair_seeds` 供下游 testcase-design Skill 消费
- 有效种子场景写入上下文，标记 `source: pair`

## 规则
- 结对种子优先于 AI 生成：种子覆盖的场景 AI 不再重复生成
- 每个种子至少需要：场景名称（必填）、优先级（必填）、类型（必填）、操作步骤≥1 步（必填）、预期结果（必填）
- 校验失败的种子跳过，不阻塞流程
- 无 PAIR_SEEDS.md 时正常跳过，不影响 AI 全量生成

## 依赖
- templates/pair-seeds.template.md
- skills/test-design/testcase-design.md（下游消费方）

## 边界
- 本 Skill 不生成测试用例（那是 testcase-design 的职责）
- 本 Skill 不做业务分析（那是 page-analysis/risk-modeling 的职责）
- 本 Skill 仅做种子场景的校验和注入

---

## 触发条件

- 由人类通过 `/pair-seed --module=<m> --page=<p>` 手动触发（交互式填写）
- 或由 SOP 流程在 test-design 阶段前自动检测 PAIR_SEEDS.md 是否存在
- **SOP 集成**：test-design-agent 的 Skill 链中，`page-analysis` 之后、`risk-modeling` 之前自动执行

---

## Prompt 模板

> 以下 Prompt 可直接复制到 AI 对话中使用。替换 `{{ }}` 占位符即可。

### 交互式种子场景采集

```text
你是结对测试同学，需要为以下页面提供 2-5 个核心测试场景作为种子。

## 页面信息
- 页面名称：{{页面名}}
- 所属模块：{{模块名}}
- 页面URL：{{URL}}

## 已有上下文
PAGE_CONTEXT 摘要：{{粘贴 PAGE_CONTEXT.md 核心元素清单}}

## 任务
请提供 2-5 个你认为 AI 可能遗漏的核心测试场景。重点关注：
1. **业务关键路径**：AI 不知道哪些是核心业务流程
2. **领域特有的边界条件**：如"危化品许可证过期后仍可编辑？"
3. **隐性业务规则**：如"同一合同号不能重复提交"
4. **历史坑点**：之前出过 Bug 的场景

每个场景至少包含：
- 场景名称（简洁描述）
- 优先级（P0/P1/P2）
- 类型（positive/negative/boundary/destructive）
- 业务背景（为什么这个场景重要）
- 操作步骤（概要，≥1 步）
- 预期结果

格式参见 `templates/pair-seeds.template.md`。
```

### 校验已有 PAIR_SEEDS.md

```text
检查以下 PAIR_SEEDS.md 中的种子场景是否完整可执行。

## 输入
{{粘贴 PAIR_SEEDS.md 完整内容}}

## 校验规则
1. 每个 SEED 必须包含：场景名称、优先级、类型、操作步骤（≥1 步）、预期结果
2. 优先级必须是 P0/P1/P2 之一
3. 类型必须是 positive/negative/boundary/destructive 之一
4. 操作步骤不能为空或仅写"同上"

## 输出
| SEED ID | 场景名称 | 校验结果 | 问题说明 |
|---------|---------|---------|---------|
| SEED-001 | {{名称}} | ✅ / ⚠️ / ❌ | {{如缺失字段说明}} |

有效种子标记 `source: pair`，注入下游 testcase-design。
有问题的种子标记跳过原因，不阻塞流程。
```

---

## 检查清单

- [ ] PAIR_SEEDS.md 存在时已解析并校验
- [ ] 每个有效种子包含 5 个必填字段（名称/优先级/类型/步骤/预期）
- [ ] 校验失败的种子已标记跳过原因
- [ ] 有效种子已注入 `pipeline_context.pair_seeds`
- [ ] 注入后标记 `pair_seeds_available: true`
- [ ] PAIR_SEEDS.md 不存在时正常跳过，`pair_seeds_available: false`

---

## 降级规则

| 场景 | 行为 |
|------|------|
| PAIR_SEEDS.md 不存在 | 跳过，正常执行下游 Skill。所有用例标记 `source: ai` |
| PAIR_SEEDS.md 存在但全部校验失败 | 警告后继续。所有用例标记 `source: ai` |
| 部分种子校验失败 | 跳过失败的，使用通过的。通过种子标记 `source: pair` |
| 模板格式不兼容 | 尝试解析，失败则降级为 `source: ai` 模式 |

---

## 产出物
→ 校验报告（控制台输出或嵌入 test-design 流程日志）
→ `pipeline_context.pair_seeds` 供下游 testcase-design 消费
→ 无文件产出（种子场景融入 TEST_CASES.md 中）
