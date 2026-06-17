# Review Queue

> 架构评审队列目录。当前未激活 — 评审由 ReviewAgentSubscriber 事件驱动，不通过文件队列。

## 状态

- **状态**: 未使用
- **替代机制**: `aitest/governance/event_bus.py` ReviewAgentSubscriber 直接处理事件
- **计划**: 如需批量离线评审，可启用此目录作为待处理文件队列

## 参考

- `governance/artifacts/reviews/system/ARCH_REVIEW_FULL-2026-06-17.md`
- `governance/agents/agent-definitions-dev.yaml` → architecture-review-agent
