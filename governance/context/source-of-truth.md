# Source Of Truth

## 原则
同一类事实只能有一个主维护位置，其余文件只做引用、摘要或映射。

## 事实源分工
| 事实类型 | 主维护位置 | 当前参考资产 | 说明 |
|------|------|------|------|
| 项目级共性 | context/projects/*/PROJECT_CONTEXT.md | PROJECT_CONTEXT*.md | 稳定事实 |
| 模块级业务/测试事实 | context/projects/*/modules/*/ | 现有 contexts/<module>/ | 后续逐步对齐 |
| 流程规则 | aitest/graphs/state.py (CANONICAL_PHASES) | 统一 Phase 名称 + 顺序 | 代码为唯一事实源，文档自动生成 |
| Skill 定义 | skills/ + skill-registry.yaml | Prompt / 经验规则 | 沉淀高频能力 |
| 模板规范 | templates/ | 模板库 / Prompt 库 | 统一输入输出 |
| 过程产物 | artifacts/ | 临时分析结果 | 不做事实源 |
| SOP 运行状态 (权威) | governance/.graph_state/checkpoints.sqlite | LangGraph SqliteSaver | 断点续跑 + 时间旅行，程序以 SQLite 为准 |
| SOP 运行状态 (可读导出) | artifacts/sop-status/SOP_STATUS_<module>.json | JSON 快照 | SQLite 的人类可读导出，不作为独立门禁依据 |
| Agent 定义 | governance/agents/agent-definitions.yaml | 单一事实源 | agents/README.md + project-index.yaml 从此文件自动生成 |

## 禁止事项
- 不在多个文件重复维护同一份模块清单
- 不把临时 AI 会话记录写进项目主上下文
- 不把长 Prompt 直接当事实源长期维护
- 不在 modules/ 子目录下存放 SOP_STATUS JSON（统一位置: artifacts/sop-status/）
- 不绕过 SOP 状态检查直接进入后续 Phase
