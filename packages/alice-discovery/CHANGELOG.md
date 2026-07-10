# Changelog

All notable changes to alice-discovery will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0] - 2026-07-09

### Added

**Core Features**:
- 🎯 零依赖前端项目静态分析 SDK（纯 Python stdlib）
- 🔍 框架自动检测（Vue 2/3、React、版本识别）
- 🗺️ 路由提取（Vue Router、React Router 配置解析）
- 🧩 组件分析（props、events、slots、子组件提取）
- 🌐 API 发现（axios/fetch 调用扫描，参数、响应字段提取）
- 📍 溯源追踪（每字段记录源文件、行号、置信度、证据）

**Data Models** (`schema/`):
- `ProjectKnowledge` — 项目知识聚合模型
- `PageMetadata` — 页面元数据（路由、组件、元素、API）
- `RouteMetadata` — 路由元数据（路径、组件、子路由）
- `ComponentMetadata` — 组件元数据（props、events、slots、refs）
- `ApiMetadata` — API 元数据（方法、路径、参数、响应）
- `FrameworkInfo` / `BackendInfo` — 技术栈信息
- `FieldValue[T]` — 值 + 溯源信息封装
- `Provenance` — 溯源信息（来源、文件、行号、置信度、证据）

**Source Analysis** (`source/`):
- `SourceDiscoveryPipeline` — 统一分析流水线
- `TechStackDetector` — 技术栈检测器（框架、版本、构建工具、UI 库）
- `FrameworkDetector` — 前端框架检测
- `BackendDetector` — 后端框架检测
- `FileIndexer` — 文件索引器（快速定位关键文件）
- `MetadataMergeEngine` — 多来源元数据合并引擎

**Extractors** (`source/extractors/`):
- `VueRouterExtractor` — Vue Router 配置提取
- `VueComponentExtractor` — Vue 组件元数据提取
- `ApiExtractor` — API 调用提取（axios、fetch、自定义 HTTP 封装）
- `BaseExtractor` — 提取器基类（可扩展）

**Architecture**:
- 三层架构：Schema（数据模型）← Source（分析引擎）← Base（Discovery 抽象）
- 插件式设计：提取器可独立注册、扩展
- 置信度机制：HIGH（0.9+）/ MEDIUM（0.7-0.9）/ LOW（< 0.7）
- 证据保留：每次提取保留原始代码片段，支持人工审查

**Use Cases**:
- ✅ 测试自动化上下文构建（Automation Agent 获取项目结构）
- ✅ Page Object 自动生成（基于组件元数据生成测试代码）
- ✅ API Mock 生成（基于 API 发现结果生成 Mock 响应）
- ✅ 测试覆盖率分析（对比 Discovery 结果与测试脚本）
- ✅ 文档生成（基于源码元数据生成项目文档）

### Technical Details

**Python Version**: >=3.11（利用泛型语法、dataclass 增强）

**Dependencies**: 零外部依赖（stdlib only）

**Optional Dependencies**:
- `[cli]` — Typer + Rich（命令行工具）
- `[dev]` — pytest（开发测试）

**Performance**（典型 Vue 项目：~50 页面、~200 组件）:
- 扫描时间：~2-3 秒
- 内存占用：~50 MB
- 输出大小：~500 KB（JSON）

**Design Principles**:
1. 零依赖 — 快速安装、稳定性、可移植性
2. 溯源优先 — 每字段记录来源，支持调试和可信度评估
3. 框架无关 — 插件式提取器架构，易扩展新框架

### Integration

**与 alice-engine 集成**:
```python
from alice_engine import Engine
from alice_discovery import SourceDiscoveryPipeline

knowledge = pipeline.run(project.path)
engine = Engine(project=project, context={"project_knowledge": knowledge})
```

**与 alice-governance 集成**:
```python
from alice_governance import SkillLoader
from alice_discovery import SourceDiscoveryPipeline

knowledge = pipeline.run(project_path)
skill = loader.load_skill("automation/page-object-generator")
prompt = skill.prompt.format(page_title=knowledge.pages[0].title.value)
```

### Known Limitations

- Vue Router 提取依赖正则匹配（非完整 AST），复杂嵌套路由可能准确率降低
- React 支持尚不完整（仅框架检测，提取器待扩展）
- Angular、Svelte 支持待实现
- 动态路由（如路由守卫、异步加载）暂不支持
- API 提取仅识别常见模式（axios、fetch），自定义封装需扩展

### Future Plans

**v0.2.0**（计划）:
- [ ] React Router v6 提取器
- [ ] 完整 AST 解析（可选依赖 `[ast]`）
- [ ] 并行文件扫描（性能优化）
- [ ] CLI 工具（`alice-discovery scan/detect/routes/apis`）

**v0.3.0**（规划）:
- [ ] Angular 支持
- [ ] Svelte 支持
- [ ] 动态路由分析（静态分析 + 运行时补充）
- [ ] 增量更新（基于文件变更 diff）

---

## [Unreleased]

### Roadmap
- TypeScript 定义文件生成（基于 Vue/React 组件提取）
- GraphQL Schema 发现（如项目使用 GraphQL）
- WebSocket 端点提取
- 权限矩阵构建（基于路由 meta、组件 v-if 条件）
- 测试用例自动生成（基于页面元数据 + 测试模式）

---

[0.1.0]: https://github.com/your-org/alice-discovery/releases/tag/v0.1.0
