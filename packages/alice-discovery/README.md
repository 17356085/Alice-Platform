# Alice Discovery

**AI 测试自动化 — 前端项目静态分析 SDK**

从 Vue/React 源码中自动提取路由、组件、API 调用，构建结构化知识模型，为测试自动化提供项目上下文。

---

## 核心能力

- **零依赖**: 纯 Python 标准库实现，无外部依赖
- **框架识别**: 自动检测 Vue 2/3、React、框架版本、构建工具
- **路由提取**: 解析 Vue Router、React Router 配置，构建路由树
- **组件分析**: 提取组件元数据（props、events、slots、refs）
- **API 发现**: 扫描 axios/fetch 调用，提取 API 端点和参数
- **溯源追踪**: 每个数据字段记录来源文件、行号、置信度

---

## 安装

```bash
# 最小安装（核心 SDK）
pip install alice-discovery

# 带 CLI 工具
pip install alice-discovery[cli]

# 开发环境
pip install alice-discovery[dev]
```

**Python 要求**: 3.11+

---

## 快速开始

### 1. 项目扫描

```python
from alice_discovery import SourceDiscoveryPipeline
from pathlib import Path

# 扫描 Vue 项目
pipeline = SourceDiscoveryPipeline()
knowledge = pipeline.run(Path("./my-vue-app"))

# 查看识别结果
print(f"框架: {knowledge.framework.framework}")  # FrameworkType.VUE_3
print(f"路由数: {len(knowledge.routes)}")
print(f"页面数: {len(knowledge.pages)}")
print(f"API 端点数: {len(knowledge.apis)}")
```

### 2. 框架检测

```python
from alice_discovery import TechStackDetector

detector = TechStackDetector()
tech = detector.detect(Path("./my-vue-app"))

print(tech.framework)         # FrameworkType.VUE_3
print(tech.framework_version) # "3.3.4"
print(tech.ui_framework)      # "element-plus"
print(tech.build_tool)        # "vite"
```

### 3. 路由提取

```python
from alice_discovery import VueRouterExtractor

extractor = VueRouterExtractor()
routes = extractor.extract(Path("./src/router/index.js"))

for route in routes:
    print(f"{route.path.value} → {route.component.value}")
    print(f"  来源: {route.path.provenance.file}:{route.path.provenance.line}")
    print(f"  置信度: {route.path.provenance.confidence.value}")
```

**输出示例**:
```
/equipment/alarm-config → views/Equipment/AlarmConfig.vue
  来源: src/router/index.js:42
  置信度: 0.95
```

### 4. 组件分析

```python
from alice_discovery import VueComponentExtractor

extractor = VueComponentExtractor()
component = extractor.extract(Path("./src/views/Equipment/AlarmConfig.vue"))

print(f"组件名: {component.name.value}")
print(f"Props: {[p.name for p in component.props]}")
print(f"事件: {[e.name for e in component.events]}")
print(f"子组件: {[c.tag for c in component.children]}")
```

### 5. API 发现

```python
from alice_discovery import ApiExtractor

extractor = ApiExtractor()
apis = extractor.extract(Path("./src/api/equipment.js"))

for api in apis:
    print(f"{api.method.value} {api.path.value}")
    print(f"  参数: {[p.name for p in api.params]}")
    print(f"  响应字段: {[f.name for f in api.response_fields]}")
```

---

## 数据模型

### ProjectKnowledge（项目知识）

```python
@dataclass
class ProjectKnowledge:
    framework: FrameworkInfo         # 框架信息（Vue 3/React 18/...）
    backend: BackendInfo | None      # 后端信息（FastAPI/Spring Boot/...）
    routes: list[RouteMetadata]      # 路由列表
    pages: list[PageMetadata]        # 页面元数据
    components: list[ComponentMetadata]  # 组件列表
    apis: list[ApiMetadata]          # API 端点列表
```

### FieldValue（字段值 + 溯源）

Discovery SDK 的核心特性：**每个数据字段都记录来源**。

```python
@dataclass
class FieldValue[T]:
    value: T                # 实际值（如 "/equipment/alarm-config"）
    provenance: Provenance  # 溯源信息

@dataclass
class Provenance:
    source: Source          # 数据来源类型（SOURCE_CODE/RUNTIME/...）
    file: str | None        # 源文件路径
    line: int | None        # 行号
    confidence: Confidence  # 置信度（HIGH/MEDIUM/LOW）
    evidence: str | None    # 证据片段（原始代码）
```

**示例**:
```python
route = routes[0]
print(route.path.value)                  # "/equipment/alarm-config"
print(route.path.provenance.file)        # "src/router/index.js"
print(route.path.provenance.line)        # 42
print(route.path.provenance.confidence)  # Confidence.HIGH
print(route.path.provenance.evidence)    # "path: '/equipment/alarm-config'"
```

---

## 架构

```
alice_discovery/
├── schema/              数据模型（ProjectKnowledge, PageMetadata, ...）
│   ├── schema.py        核心模型定义
│   └── provenance.py    溯源机制（FieldValue, Provenance）
├── source/              源码分析引擎
│   ├── pipeline.py      分析流水线（统一入口）
│   ├── framework_detector.py  框架检测
│   ├── backend_detector.py    后端检测
│   ├── file_indexer.py        文件索引器
│   ├── merger.py        元数据合并引擎
│   └── extractors/      提取器（Vue/React/API/...）
│       ├── vue_router.py       Vue Router 提取
│       ├── vue_component.py    Vue 组件提取
│       ├── api_extractor.py    API 调用提取
│       └── base.py             提取器基类
└── base.py              Discovery 基础类

依赖关系: schema (零依赖) ← source (依赖 schema) ← base (依赖 source)
```

---

## 使用场景

### 1. 测试自动化上下文构建

```python
# Automation Agent 使用 Discovery 了解项目结构
knowledge = pipeline.run(project_path)

for page in knowledge.pages:
    print(f"页面: {page.title.value}")
    print(f"路由: {page.route.value}")
    print(f"组件: {page.component.value}")
    print(f"API: {[api.path.value for api in page.related_apis]}")
    print()
```

### 2. Page Object 自动生成

```python
# Page Object Generator Skill 基于 Discovery 结果生成测试代码
from alice_discovery import VueComponentExtractor

component = extractor.extract(Path("AlarmConfig.vue"))

# 生成 Page Object
class_name = to_pascal_case(component.name.value)
print(f"class {class_name}Page(BasePage):")

for element in component.elements:
    locator = element.locator.value
    print(f"    {element.id.value} = (By.CSS_SELECTOR, '{locator}')")
```

### 3. API Mock 数据生成

```python
# 基于 API 发现结果生成 Mock 响应
for api in knowledge.apis:
    mock_response = {}
    for field in api.response_fields:
        mock_response[field.name] = generate_mock_value(field.type)
    
    print(f"{api.method.value} {api.path.value}")
    print(json.dumps(mock_response, indent=2))
```

### 4. 测试覆盖率分析

```python
# 对比 Discovery 结果与测试脚本，计算覆盖率
tested_pages = set(extract_tested_pages(test_scripts))
all_pages = {page.route.value for page in knowledge.pages}

untested = all_pages - tested_pages
coverage = len(tested_pages) / len(all_pages) * 100

print(f"覆盖率: {coverage:.1f}%")
print(f"未覆盖页面: {untested}")
```

---

## CLI 工具

```bash
# 安装 CLI
pip install alice-discovery[cli]

# 扫描项目
alice-discovery scan ./my-vue-app --output=knowledge.json

# 查看框架信息
alice-discovery detect ./my-vue-app

# 提取路由树
alice-discovery routes ./my-vue-app --format=tree

# 统计 API 端点
alice-discovery apis ./my-vue-app --group-by=module
```

---

## 与其他 SDK 集成

### 与 alice-engine 集成

```python
from alice_engine import Engine, Project
from alice_discovery import SourceDiscoveryPipeline

# 1. 扫描项目（Discovery）
pipeline = SourceDiscoveryPipeline()
knowledge = pipeline.run(project.path)

# 2. 注入到 Engine 上下文
engine = Engine(
    project=project,
    context={
        "project_knowledge": knowledge,
        "pages": [p.to_dict() for p in knowledge.pages],
        "apis": [a.to_dict() for a in knowledge.apis],
    }
)

# 3. Automation Agent 可以读取上下文
result = engine.run("equipment", pages=["alarm-config"])
```

### 与 alice-governance 集成

```python
from alice_governance import get_pack_path, SkillLoader
from alice_discovery import SourceDiscoveryPipeline

# Discovery 结果作为 Skill 输入
knowledge = pipeline.run(project_path)

loader = SkillLoader(governance_path=get_pack_path())
skill = loader.load_skill("automation/page-object-generator")

# Skill 使用 Discovery 元数据
page = knowledge.pages[0]
prompt = skill.prompt.format(
    page_title=page.title.value,
    route=page.route.value,
    elements=[e.to_dict() for e in page.elements.buttons + page.elements.inputs],
)
```

---

## 设计原则

### 1. 零依赖

Discovery SDK 仅依赖 Python 标准库，无外部依赖。这确保：
- ✅ 快速安装（无依赖下载）
- ✅ 稳定性（无版本冲突）
- ✅ 可移植性（任何 Python 3.11+ 环境）

### 2. 溯源优先

每个数据字段都记录来源文件、行号、置信度、证据片段。这支持：
- ✅ 调试（快速定位源码）
- ✅ 可信度评估（根据置信度过滤）
- ✅ 增量更新（跟踪变更）

### 3. 框架无关

虽然当前实现侧重 Vue，但架构设计支持任意前端框架：
- ✅ 插件式提取器（BaseExtractor 接口）
- ✅ 统一数据模型（ProjectKnowledge）
- ✅ 框架检测器（自动选择提取器）

---

## 扩展

### 添加新框架支持

```python
from alice_discovery import BaseExtractor, RouteMetadata, FieldValue, Provenance

class ReactRouterExtractor(BaseExtractor):
    """React Router v6 提取器。"""
    
    def extract(self, file_path: Path) -> list[RouteMetadata]:
        routes = []
        content = file_path.read_text()
        
        # 解析 React Router 配置
        # <Route path="/equipment" element={<Equipment />} />
        for match in re.finditer(r'<Route\s+path="([^"]+)"\s+element=\{<(\w+)', content):
            path, component = match.groups()
            line = content[:match.start()].count('\n') + 1
            
            routes.append(RouteMetadata(
                path=FieldValue(
                    value=path,
                    provenance=Provenance(
                        source=Source.SOURCE_CODE,
                        file=str(file_path),
                        line=line,
                        confidence=Confidence.HIGH,
                        evidence=match.group(0),
                    )
                ),
                component=FieldValue(value=f"{component}.jsx", provenance=...),
            ))
        
        return routes
```

注册到 Pipeline:
```python
from alice_discovery import SourceDiscoveryPipeline

pipeline = SourceDiscoveryPipeline()
pipeline.register_extractor("react", ReactRouterExtractor())
```

---

## 常见问题

### Q: Discovery 与运行时 Browser-Use 的区别？

**Discovery（静态分析）**:
- 扫描源码，构建知识模型
- 运行前执行（一次性，增量更新）
- 适用场景：测试规划、Page Object 生成、覆盖率分析

**Browser-Use（运行时探索）**:
- 浏览器中动态观察页面
- 运行时执行（每次测试）
- 适用场景：元素定位、页面交互、自愈

**协同**：Discovery 提供全局视图（所有页面、路由），Browser-Use 提供局部细节（当前页面元素）。

---

### Q: 为何不直接用 AST 解析？

当前实现使用正则表达式 + 启发式规则，而非完整 AST 解析。原因：

1. **零依赖约束**：AST 解析需要 `esprima`/`babel` 等外部依赖
2. **够用原则**：正则匹配对于路由/API 提取已足够准确（置信度 > 90%）
3. **性能**：正则匹配比 AST 解析快 10x+

未来可选：提供 `alice-discovery[ast]` 可选依赖，使用完整 AST 解析提升准确性。

---

### Q: 支持哪些前端框架？

**当前支持**:
- Vue 2/3（Router、组件、API）
- 部分支持 React（需扩展）

**计划支持**:
- React Router v6
- Angular（路由、组件）
- Svelte（路由、组件）

欢迎贡献 Extractor 实现！

---

## 性能

典型 Vue 项目（~50 页面，~200 组件）:
- **扫描时间**: ~2-3 秒
- **内存占用**: ~50 MB
- **输出大小**: ~500 KB（JSON）

瓶颈：文件 I/O（读取源文件）。可通过并行扫描优化（未来版本）。

---

## 开发

```bash
# 克隆仓库
git clone https://github.com/your-org/alice-discovery.git
cd alice-discovery

# 安装开发依赖
pip install -e ".[dev,cli]"

# 运行测试
pytest

# 类型检查
mypy alice_discovery
```

---

## License

MIT

---

## 相关项目

- [alice-engine](../alice-engine/) — 测试自动化执行引擎
- [alice-governance](../alice-governance/) — Skill 库 + 知识库
- [AITest 平台](../../README.md) — 完整 AI 测试自动化平台
