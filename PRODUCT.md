# Product

## Register

product

## Users

**Primary User: QA Agent Builder**

理解 Agent、Skill、Prompt、Tool 概念，能配置项目、创建 Dataset、评估失败 Run、调试 Agent 行为、改进 Prompt、提交新版本到 CI。日常工作是构建和改进测试 Agent，而非编写传统测试代码。

**Secondary User: QA Operator**

选择项目、运行已配置的 Workflow、查看测试报告、浏览失败截图和日志。不修改 Agent 内部配置，不理解 Prompt 细节。依赖 QA Agent Builder 提供的现成 Workflow。

**明确不是目标用户**：
- 非技术业务用户（需要零门槛拖拽式 Agent）
- 开发者（需要通用 Agent 平台和 Marketplace）
- 企业 IT 管理员（需要复杂权限、部署编排、审计）

单租户/小团队定位。权限分层和多租户不是 MVP 范围。

## Product Purpose

**Alice = Testing-first QA Agent Builder Platform**

让 QA Agent Builder 构建、调试、改进测试 Agent 的平台。核心差异不是"能运行测试"（传统测试平台都能），而是"能改进失败的 Agent"。

**核心循环**：
```
失败 Run → 选中失败步骤 → 查看 Trace/Screenshot/DOM/Console
          ↓
保存为 Dataset Example
          ↓
修改 Agent/Prompt
          ↓
运行 Evaluation（对比新旧版本通过率、失败类型、Token 成本）
          ↓
Experiment 决策：Promote 新版本 or Reject
```

这是 Alice 与传统测试报告系统的根本区别：**失败不是终点，而是下一轮 Agent 改进的输入**。

**核心任务**：
- 初始化项目（discover 页面结构、定义测试范围）
- 构建 Workflow（选择/配置 Agent、定义执行图）
- 运行测试（创建 Run、实时查看 Trace）
- 调试失败（查看 Artifact、保存为 Dataset）
- 改进 Agent（修改 Prompt/Skill、运行 Evaluation、对比新旧版本）
- 提交生产（Promote 到 :production alias、集成 CI）

成功 = QA Agent Builder 不需要翻日志就能定位 Agent 失败原因，不需要写代码就能改进 Prompt 质量，通过 Evaluation 数据驱动地决策是否发布新版本。

## Brand Personality

三主角主题，各自独立：

| 主题 | 角色 | 3 词 |
|------|------|------|
| Alice | 久远寺有珠 | 静謐 · 克製 · 知性 |
| Aoko | 苍崎青子 | 明快 · 直率 · 动能 |
| Soujuurou | 静希草十郎 | 素直 · 温厚 · 自然 |

整体基调：**魔法使之夜的冬夜氛围，但不是二次元。** 看过原作的用户能心领神会；没看过的用户只觉得是三套默契的配色方案。

视觉上借鉴 Apple 设计哲学：极度克制、层次清晰、内容优先、UI 退入背景。

## Anti-references

- ❌ SaaS 模板感（Inter 泛滥、紫蓝渐变、等权卡片）
- ❌ 赛博朋克霓虹美学、cyan glow
- ❌ 粗边框、重阴影
- ❌ 仪表盘杂乱感
- ❌ 过度使用强调色
- ❌ 二次元风格（角色立绘、萌系元素）

## Design Principles

1. **Calm over stimulation** — 界面应安静如操作系统，不抢夺注意力。暗黑模式是第一公民。

2. **Content first, UI disappears** — 测试数据、Agent 状态、时间线事件是主角。边框、阴影、装饰退入背景。

3. **Depth through layering, not shadow** — 用半透明层叠（8-15% opacity 渐变）和间距创造深度，非粗边框和重阴影。

4. **One focal point per screen** — 每屏一个主焦点。次要面板视觉后退。日志、图表、元数据不与主要操作竞争。

5. **Character whispers, not shouts** — 三主角差异体现于色温、字体、圆角、动画节奏的细微变化。不是 token 级别的暴力替换。

## Accessibility & Inclusion

- WCAG AA 级别
- 暗黑模式为默认，浅色模式为备选
- 支持 reduced motion
- 中文为主要界面语言，英文为备选
