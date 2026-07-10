# Changelog

All notable changes to alice-engine will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-07-09

### Added

**Extension 体系扩展**:
- 新增 `KnowledgeExtension` — 跨 Run 知识检索与沉淀
  - 执行前调用 `search_before_run()` 检索历史知识
  - 执行后调用 `on_cycle_end()` 沉淀新知识到 `KnowledgeStore`
  - 支持任意 `KnowledgeStore` 后端（InMemory / ChromaDB / Elasticsearch）
  - 默认延迟初始化 `InMemoryKnowledgeStore`（零配置）
- 新增 `MemoryExtension` — 执行历史记忆
  - 执行后调用 `on_cycle_end()` 记录本次 `RunResult`
  - 提供 `get_last_run()` / `get_history()` 供 Engine 主动查询
  - 支持任意 `MemoryStore` 后端（InMemory / File / SQLite / PostgreSQL）
  - 默认延迟初始化 `InMemoryMemoryStore`（零配置）

**Runtime Store 接口**:
- 新增 `KnowledgeStore` 抽象接口（`alice_engine.runtime`）
  - `ingest(module, result)` — 沉淀知识
  - `search(module, page_slug, limit)` — 检索知识
  - `clear(module)` — 清除知识
- 新增 `MemoryStore` 抽象接口（`alice_engine.runtime`）
  - `remember(module, result)` — 记录执行结果
  - `get_last(module)` — 获取最近执行记录
  - `get_history(module, limit)` — 获取执行历史
  - `get_stats(module)` — 获取统计信息
  - `clear(module)` — 清除记忆
  - `get_all_modules()` — 获取所有模块列表
- 新增 `InMemoryKnowledgeStore` 默认实现（零依赖）
- 新增 `InMemoryMemoryStore` 默认实现（零依赖）

**Extensions 导出更新**:
- `alice_engine.extensions.__all__` 新增：`KnowledgeExtension`, `MemoryExtension`
- 完整 Extensions 列表：`AuditExtension`, `ComplexityExtension`, `KnowledgeExtension`, `MemoryExtension`

**SDK 独立性验证**:
- 新增 `standalone_sdk_test.py`（6 项静态验证）
- 新增 `verify_sdk_independence.py`（6 项深度 AST 分析）
- 真实 Python 3.11.11 功能测试（6/6 通过）

### Changed

**版本升级**: `0.1.0` → `1.0.0`（Extensions 体系完整）

**架构完善**:
- SDK 完整实现所有 4 个 Extensions（之前仅 2 个：Audit, Complexity）
- 平台层 `aitest/engine/extensions/` 改造为纯 re-export 兼容层

### Performance

真实环境基准测试（Python 3.11.11，`tests/benchmark/test_performance.py`）:

**Engine 创建**:
- 无 Extension（基线）: 0.605ms 中位数
- 1 个 Extension: 0.678ms（+11.9%）
- 4 个 Extension（全部）: 0.896ms（+48.0%）

**Runtime Store（InMemory）**:
- `KnowledgeStore.ingest()`: 1.79μs（558k/s）
- `KnowledgeStore.search(limit=5)`: 43.16μs（23k/s）
- `MemoryStore.remember()`: 2.06μs（485k/s）
- `MemoryStore.get_last()`: 0.17μs（5.9M/s）

**Extension 钩子**:
- `KnowledgeExtension.on_cycle_end()`: 1.20μs
- `MemoryExtension.on_cycle_end()`: 1.14μs
- 4 钩子累计 < 45μs（LLM 调用开销的 < 0.01%）

---

## [0.1.0] - 2026-07-01

### Added

Initial release.

**Core**:
- `Engine` 类，支持同步 `run()` 和异步 `run_async()` API
- `RunResult` dataclass，含类型字段和 `success` 属性
- `EventBus` — pub/sub 事件总线
- `EngineExtension` Protocol — 生命周期钩子（`on_init`, `on_phase_end`, `on_cycle_end`）
- `MockProvider` — 不调用 LLM 的测试 Provider
- `ProjectConfig` — 项目配置加载（`project.yaml` / `.tlo/` 目录）
- `ValidationResult` — 项目配置校验
- 异常层次结构：`AliceError`, `ConfigError`, `ProviderError`, `ExecutionError`
- Provider 注册表（懒加载可选依赖）

**Built-in Extensions**:
- `AuditExtension` — 执行审计（记录执行日志、统计）
- `ComplexityExtension` — 复杂度评估（18 因子评分，SIMPLE/STANDARD/COMPLEX 三档）

**Providers**:
- `MockProvider` — 测试用（无网络依赖）
- `ClaudeProvider` — Anthropic Claude（可选依赖 `[llm-anthropic]`）
- `OpenAIProvider` — OpenAI GPT（可选依赖 `[llm-openai]`）
- `DeepSeekProvider` — DeepSeek（可选依赖）
- `OllamaProvider` — 本地 Ollama（可选依赖）

**Dependencies**:
- Core: `langgraph>=0.2.0`, `pyyaml>=6.0`, `python-dotenv>=1.0`, `pydantic>=2.0`
- Optional: `anthropic`, `openai`, `typer`, `rich`

---

[1.0.0]: https://github.com/your-org/alice-engine/compare/v0.1.0...v1.0.0
[0.1.0]: https://github.com/your-org/alice-engine/releases/tag/v0.1.0
