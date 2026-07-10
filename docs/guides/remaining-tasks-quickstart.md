# SDK 迁移 - 剩余任务快速指南

**当前状态**: Extension 迁移完成 ✅  
**剩余任务**: 3 项（按你的原始清单）

---

## ✅ 任务 1: Extension 迁移（Knowledge、Memory → SDK）

**状态**: 已完成  
**交付物**:
- SDK 新增: `knowledge.py`, `memory.py`
- 平台改造: re-export 兼容层
- CLI 更新: 统一 SDK 导入
- 验证: `standalone_sdk_test.py` 全部通过

---

## 📋 任务 2: SDK PyPI 发布

**目标**: 将 alice-engine 发布到 PyPI，供外部用户安装使用。

**操作指南**: 见 `docs/guides/sdk-pypi-publishing.md`

**快速步骤**（由你执行）:

```bash
# 1. 环境准备（需要 Python 3.11+）
python3.11 -m venv venv-publish
source venv-publish/bin/activate
pip install build twine

# 2. 版本号确认
cd packages/alice-engine
# 编辑 pyproject.toml，设置 version = "0.1.0"

# 3. 构建
rm -rf dist/ build/ *.egg-info
python -m build

# 4. TestPyPI 试发布（推荐首次）
# 配置 ~/.pypirc（见 sdk-pypi-publishing.md）
twine upload --repository testpypi dist/*

# 5. 验证 TestPyPI 安装
pip install --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ \
    alice-engine

python -c "from alice_engine import Engine; print('✅ OK')"

# 6. 生产 PyPI 发布
twine upload dist/*

# 7. 验证生产安装
pip install alice-engine
python -c "from alice_engine.extensions import KnowledgeExtension, MemoryExtension; print('✅ OK')"
```

**前置条件**:
- [ ] PyPI 账号 (https://pypi.org/account/register/)
- [ ] API Token (https://pypi.org/manage/account/token/)
- [ ] Python 3.11+ 环境

**预期耗时**: 1-2 小时

---

## 🔍 任务 3: 验证 SDK 能否独立发布

**目标**: 确认 SDK 在零平台依赖情况下可独立运行。

**状态**: 静态检查已通过 ✅  
**剩余工作**: Python 3.11+ 环境运行测试

**操作步骤**（由你执行）:

```bash
# 1. Python 3.11+ 环境
python3.11 -m venv venv-sdk-test
source venv-sdk-test/bin/activate

# 2. 安装 SDK（本地开发版）
cd packages/alice-engine
pip install -e .

# 3. 导入测试
python << 'EOF'
from alice_engine import Engine, Project, RunResult
from alice_engine.extensions import (
    AuditExtension,
    ComplexityExtension,
    KnowledgeExtension,
    MemoryExtension,
)
from alice_engine.providers import get_provider, list_providers
from alice_engine.runtime import (
    KnowledgeStore,
    InMemoryKnowledgeStore,
    MemoryStore,
    InMemoryMemoryStore,
)

print("✅ 所有导入成功")
print(f"✅ 可用 Providers: {list_providers()}")
EOF

# 4. 创建测试项目
mkdir -p /tmp/sdk-test-project
cat > /tmp/sdk-test-project/project.yaml << 'EOF'
version: 1
project:
  id: sdk-test
  name: SDK Independence Test
EOF

# 5. 运行 Engine（Mock 模式）
python << 'EOF'
from alice_engine import Engine, Project
from alice_engine.extensions import KnowledgeExtension, MemoryExtension
from alice_engine.providers import get_provider

project = Project("/tmp/sdk-test-project")
mock_provider = get_provider("mock")

engine = Engine(
    project=project,
    llm_provider=mock_provider,
    extensions=[
        KnowledgeExtension(),
        MemoryExtension(),
    ],
)

print("✅ Engine 创建成功")
print(f"  - Project: {engine.project.project_id}")
print(f"  - Extensions: {len(engine.extensions)} 个")

# 测试 Provider
response = mock_provider.complete(
    system_prompt="You are a test assistant",
    user_prompt="Hello",
)
print(f"✅ Mock Provider 响应: {response.content[:50]}...")
EOF

# 6. 检查零平台依赖
grep -r "from aitest\." alice_engine/ | grep -v __pycache__ || echo "✅ 零平台依赖"
```

**检查项**:
- [ ] 导入成功（Engine, Extensions, Providers, Runtime）
- [ ] Engine 创建成功（Mock 模式）
- [ ] Extensions 正常初始化
- [ ] 零平台依赖（无 `from aitest.` 导入）

**预期耗时**: 30 分钟

---

## 📊 任务 4: 性能基准测试

**目标**: 对比 SDK vs 平台集成的性能差异。

**测试场景**:

### 场景 1: Extension 开销

```python
# test_extension_overhead.py
import time
from alice_engine import Engine, Project
from alice_engine.extensions import KnowledgeExtension, MemoryExtension

project = Project("./test-project")

# 无 Extension
start = time.time()
engine_bare = Engine(project=project)
result1 = engine_bare.run(module="user", pages=["user-list"])
time_bare = time.time() - start

# 有 Extension
start = time.time()
engine_ext = Engine(
    project=project,
    extensions=[KnowledgeExtension(), MemoryExtension()]
)
result2 = engine_ext.run(module="user", pages=["user-list"])
time_ext = time.time() - start

print(f"无 Extension: {time_bare:.2f}s")
print(f"有 Extension: {time_ext:.2f}s")
print(f"开销: {(time_ext - time_bare) / time_bare * 100:.1f}%")
```

### 场景 2: 存储后端对比

```python
# test_storage_backends.py
from alice_engine.extensions import KnowledgeExtension
from alice_engine.runtime import InMemoryKnowledgeStore

# SDK InMemory
ext_inmem = KnowledgeExtension(store=InMemoryKnowledgeStore())

# 平台 ChromaDB（需要平台安装）
# from aitest.knowledge.rag_engine import RAGEngine
# ext_chroma = KnowledgeExtension(store=RAGEngine(chroma_path="./chroma"))

# 对比检索延迟、内存占用
```

### 场景 3: 多 Extension 并发

```python
# test_multi_extension.py
from alice_engine import Engine, Project
from alice_engine.extensions import (
    AuditExtension,
    ComplexityExtension,
    KnowledgeExtension,
    MemoryExtension,
)

engine = Engine(
    project=Project("./test-project"),
    extensions=[
        AuditExtension(),
        ComplexityExtension(),
        KnowledgeExtension(),
        MemoryExtension(),
    ]
)

# 测试 4 个 Extension 同时运行的性能
```

**工具**:
```bash
pip install pytest-benchmark memory-profiler

# 运行基准测试
pytest tests/benchmark/ --benchmark-only

# 内存分析
python -m memory_profiler test_extension_overhead.py
```

**指标**:
- 执行时间（总时长、Phase 平均、Extension 钩子）
- 内存使用（峰值、平均、增长率）
- 吞吐量（Pages/秒）
- Extension 开销（有/无对比）

**预期耗时**: 4-6 小时

---

## 优先级建议

按实际需求选择执行顺序：

### 优先级 1: 发布为主

```
任务 2 (PyPI 发布) → 任务 3 (独立验证) → 任务 4 (性能测试)
```

**适用场景**: 尽快对外发布 SDK，吸引外部用户。

---

### 优先级 2: 质量为主

```
任务 3 (独立验证) → 任务 4 (性能测试) → 任务 2 (PyPI 发布)
```

**适用场景**: 充分验证后再发布，降低发布风险。

---

### 优先级 3: 最小验证

```
任务 3 (独立验证) → 任务 2 (PyPI 发布) [跳过任务 4]
```

**适用场景**: 快速发布 Alpha 版本，性能优化留待后续。

---

## 当前建议

**推荐顺序**: 任务 3 → 任务 2 → 任务 4

**理由**:
1. **任务 3** (30 分钟) — 最快验证 SDK 可用性，排除基础问题
2. **任务 2** (1-2 小时) — 发布到 PyPI，开始收集外部反馈
3. **任务 4** (4-6 小时) — 后续优化，基于真实使用场景调整

---

## 检查清单

### 发布前

- [ ] `standalone_sdk_test.py` 通过 ✅
- [ ] Python 3.11+ 功能测试通过
- [ ] `pyproject.toml` 版本号、依赖正确
- [ ] `README.md` 包含安装、快速开始
- [ ] `CHANGELOG.md` 记录 v0.1.0 变更
- [ ] Git tag 创建: `git tag v0.1.0`

### 发布后

- [ ] PyPI 页面正常: https://pypi.org/project/alice-engine/
- [ ] `pip install alice-engine` 成功
- [ ] GitHub Release 创建
- [ ] 文档更新（指向 PyPI 安装）
- [ ] 通知用户/团队

---

## 快速参考

| 文档 | 路径 |
|------|------|
| PyPI 发布指南 | `docs/guides/sdk-pypi-publishing.md` |
| Extension 迁移报告 | `docs/architecture/extension-migration-report.md` |
| 验证脚本 | `standalone_sdk_test.py` |
| 本指南 | `docs/guides/remaining-tasks-quickstart.md` |

---

**最后更新**: 2026-07-09  
**下一步**: 执行任务 3（独立验证）
