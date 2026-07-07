# Phase 7 Acceptance Matrix

| Tracking ID | Status | ETA | 测试项 | 负责人 | Reviewer | 回滚点 |
| --- | --- | --- | --- | --- | --- | --- |
| PH7-PR-7.1 | Todo | 1 day | Kernel 契约评审、Facade 边界走查、依赖方向检查 | TL | Runtime Owner, Platform Owner | 回退 Kernel 契约与文档基线 |
| PH7-PR-7.2 | Todo | 2 days | SDK Engine 执行回归、`_internal.graph` 旁路清理检查、最小 Mock Provider smoke | Runtime Owner | TL, QA Reviewer | 回退 standalone Engine 调用链 |
| PH7-PR-7.3 | Todo | 2 days | CLI/Server/Chat 统一 Kernel 集成测试、结果语义一致性测试、平台增量语义回归 | Platform Owner | Runtime Owner, TL | 回退 Platform Facade 到旧工厂接线 |
| PH7-PR-7.4 | Todo | 3 days | Port 注入测试、Capability/Memory/Knowledge/Replay/MCP 适配测试、动态导入消除检查 | Runtime Owner | MCP Owner, Knowledge Owner, TL | 回退显式 Port 注入层，保留原 Bridge |
| PH7-PR-7.5 | Todo | 2 days | workspace package 安装测试、测试收集检查、Docker/CI 构建 smoke、最小发布链验证 | Infra Owner | QA Reviewer, TL | 回退 CI/Docker/打包链改动 |
| PH7-PR-7.6 | Todo | 2 days | clean env wheel 安装、`import alice_engine` smoke、Kernel Contract Test、无 `aitest` 独立执行验证 | QA Reviewer | Runtime Owner, Platform Owner, TL | 回退独立发布门禁与契约测试 |
