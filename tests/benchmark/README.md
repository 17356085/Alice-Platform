# 性能基准测试

## 概述

对比 SDK vs 平台集成的性能差异，包括：

1. **Extension 开销测试** — 有/无 Extension 的执行时间对比
2. **存储后端对比** — InMemory vs 平台特定实现（ChromaDB）
3. **Extension 钩子延迟** — 各 Extension 生命周期钩子的性能
4. **批量操作性能** — 大规模数据沉淀/检索的吞吐量
5. **内存占用** — Extension 的内存开销

---

## 环境要求

**Python 3.11+** （SDK 要求）

依赖安装：

```bash
pip install pytest pytest-benchmark memory-profiler psutil
```

---

## 快速开始

### 运行所有基准测试

```bash
cd tests/benchmark
pytest --benchmark-only
```

### 保存基线

```bash
pytest --benchmark-only --benchmark-save=baseline
```

### 对比基线

```bash
# 修改代码后重新运行
pytest --benchmark-only --benchmark-save=optimized

# 对比
pytest-benchmark compare baseline optimized
```

---

## 测试场景

### 1. Extension 开销测试

**场景**:
- 无 Extension（基线）
- 单个 Extension（Audit）
- 4 个 Extension（Audit, Complexity, Knowledge, Memory）

**指标**: 执行时间（平均、最小、最大、标准差）

**运行**:

```bash
pytest test_performance.py::test_engine_no_extension --benchmark-only
pytest test_performance.py::test_engine_single_extension --benchmark-only
pytest test_performance.py::test_engine_all_extensions --benchmark-only
```

**预期结果**:

| 场景 | 预期时间 | 开销 |
|------|----------|------|
| 无 Extension | < 10ms | 基线 |
| 单个 Extension | < 15ms | +50% |
| 4 个 Extension | < 30ms | +200% |

---

### 2. 存储后端对比

**场景**:
- InMemory KnowledgeStore（SDK）
- InMemory MemoryStore（SDK）
- ChromaDB RAGEngine（平台，需要单独测试）

**指标**: 沉淀 + 检索的往返时间

**运行**:

```bash
pytest test_performance.py::test_inmemory_knowledge_store --benchmark-only
pytest test_performance.py::test_inmemory_memory_store --benchmark-only
```

**预期结果**:

| 存储后端 | 沉淀 10 条 | 检索 5 条 | 总延迟 |
|----------|-----------|----------|--------|
| InMemory Knowledge | < 1ms | < 1ms | < 2ms |
| InMemory Memory | < 1ms | < 1ms | < 2ms |
| ChromaDB (平台) | ~50ms | ~20ms | ~70ms |

**说明**: ChromaDB 提供语义检索能力，延迟增加是合理的权衡。

---

### 3. Extension 钩子延迟

**场景**:
- KnowledgeExtension: `on_cycle_end()` + `search_before_run()`
- MemoryExtension: `on_cycle_end()` + `get_last_run()`

**指标**: 单次钩子调用延迟

**运行**:

```bash
pytest test_performance.py::test_knowledge_extension_hooks --benchmark-only
pytest test_performance.py::test_memory_extension_hooks --benchmark-only
```

**预期结果**:

| Extension | 钩子 | 预期延迟 |
|-----------|------|----------|
| Knowledge | on_cycle_end | < 5ms |
| Knowledge | search_before_run | < 3ms |
| Memory | on_cycle_end | < 2ms |
| Memory | get_last_run | < 1ms |

---

### 4. 批量操作性能

**场景**:
- 批量沉淀 10/50/100 条 Knowledge
- 批量记录 10/50/100 条 Memory

**指标**: 吞吐量（条/秒）

**运行**:

```bash
pytest test_performance.py::test_knowledge_batch_ingest --benchmark-only
pytest test_performance.py::test_memory_batch_remember --benchmark-only
```

**预期结果**:

| 批量大小 | Knowledge 吞吐量 | Memory 吞吐量 |
|----------|------------------|---------------|
| 10 条 | > 1000/s | > 2000/s |
| 50 条 | > 500/s | > 1000/s |
| 100 条 | > 200/s | > 500/s |

---

### 5. 内存占用

**场景**:
- Engine（无 Extension）
- Engine（4 个 Extension）

**指标**: RSS 内存增量（MB）

**运行**:

```bash
pytest test_performance.py::test_memory_footprint_no_extension -s
pytest test_performance.py::test_memory_footprint_all_extensions -s
```

**预期结果**:

| 场景 | 内存增量 |
|------|----------|
| 无 Extension | < 50 MB |
| 4 个 Extension | < 100 MB |

---

## 使用 memory_profiler 分析

### 逐行内存分析

```bash
# 安装
pip install memory-profiler

# 创建测试脚本
cat > profile_extension.py << 'EOF'
from memory_profiler import profile
from alice_engine import Engine, Project
from alice_engine.extensions import KnowledgeExtension, MemoryExtension

@profile
def create_engine_with_extensions():
    engine = Engine(
        project=Project("./test-project"),
        extensions=[KnowledgeExtension(), MemoryExtension()]
    )
    return engine

if __name__ == "__main__":
    create_engine_with_extensions()
EOF

# 运行
python profile_extension.py
```

---

## 性能报告生成

### HTML 报告

```bash
# 生成 HTML 报告
pytest --benchmark-only --benchmark-save=report \
    --benchmark-autosave \
    --benchmark-save-data

# 查看
pytest-benchmark compare --histogram report
```

### JSON 导出

```bash
pytest --benchmark-only --benchmark-json=results.json
```

---

## CI/CD 集成

### GitHub Actions 示例

```yaml
name: Performance Benchmarks

on:
  pull_request:
    branches: [main]

jobs:
  benchmark:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -e packages/alice-engine
          pip install pytest pytest-benchmark psutil
      
      - name: Run benchmarks
        run: |
          cd tests/benchmark
          pytest --benchmark-only --benchmark-json=results.json
      
      - name: Compare with baseline
        run: |
          # 下载 main 分支基线
          # 对比并检查回归
          pytest-benchmark compare results.json baseline.json
```

---

## 性能优化建议

### 减少 Extension 开销

1. **延迟初始化**: 只在需要时创建 Store
2. **批量操作**: 合并多次钩子调用
3. **异步处理**: 将沉淀操作移到后台

### 存储后端选择

| 场景 | 推荐 |
|------|------|
| 轻量级测试 | InMemoryStore |
| 语义检索 | ChromaDB |
| 持久化 | FileStore + SQLite |
| 分布式 | Elasticsearch |

### 内存优化

1. **定期清理**: Memory 历史记录保留上限
2. **惰性加载**: Knowledge 按需加载
3. **LRU 缓存**: 热数据缓存

---

## 故障排查

### ImportError: No module named 'alice_engine'

**原因**: SDK 未安装或 Python < 3.11

**解决**:

```bash
python --version  # 检查版本
pip install -e packages/alice-engine
```

### pytest-benchmark not found

**原因**: 未安装 benchmark 插件

**解决**:

```bash
pip install pytest-benchmark
```

### 内存占用测试 SKIP

**原因**: `psutil` 未安装

**解决**:

```bash
pip install psutil
```

---

## 参考资料

- [pytest-benchmark 文档](https://pytest-benchmark.readthedocs.io/)
- [memory_profiler 文档](https://pypi.org/project/memory-profiler/)
- [性能优化最佳实践](../../docs/guides/performance-optimization.md)

---

**最后更新**: 2026-07-09  
**维护者**: AITest Team
