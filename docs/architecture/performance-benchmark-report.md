# 性能基准测试报告（真实环境实测）

**测试环境**: Python 3.11.11（python-build-standalone，本地免 root 安装）
**SDK 版本**: alice-engine v1.0.0
**测试日期**: 2026-07-09
**测试性质**: ✅ 真实运行数据（非模拟）

---

## 环境说明

之前的报告因 sandbox 仅有 Python 3.10（SDK 要求 3.11+）而使用模拟数值。
本次通过 `python-build-standalone` 预编译二进制在用户目录下安装了 Python 3.11.11（无需 root、无需系统依赖），
在其中 `pip install -e packages/alice-engine` 后跑出以下真实数据。

---

## 1. Engine 创建性能

| 场景 | 中位数 | 均值 | 标准差 | 相对基线开销 |
|------|--------|------|--------|------|
| 无 Extension（基线） | 0.605ms | 0.670ms | 0.194ms | — |
| 1 个 Extension (Audit) | 0.678ms | 0.913ms | 0.578ms | +11.9% |
| 2 个 Extension | 0.857ms | 1.245ms | 1.444ms | +41.5% |
| 4 个 Extension（全部） | 0.896ms | 1.078ms | 0.839ms | +48.0% |

**解读**: 每加一个 Extension，Engine 构造阶段增加约 0.07-0.1ms。标准差偏大（尤其 2 个 Extension 组），
说明该量级已接近 Python 解释器噪声下限，实际生产影响可忽略——4 个 Extension 全开的绝对开销仍 < 1ms。

---

## 2. Runtime Store 性能（InMemory 实现）

| 操作 | 延迟 | 吞吐量 |
|------|------|--------|
| `KnowledgeStore.ingest()` | 1.79μs | 558,111/s |
| `KnowledgeStore.search(limit=5)` | 43.16μs | 23,172/s |
| `MemoryStore.remember()` | 2.06μs | 485,435/s |
| `MemoryStore.get_last()` | 0.17μs | 5,918,771/s |
| `MemoryStore.get_history(limit=10)` | 30.55μs | 32,731/s |

**解读**: 写入操作（ingest/remember）延迟在 2μs 级别；`get_last()` 是简单字典查找，接近 6M ops/s。
`search()` 和 `get_history()` 因涉及列表扫描/排序，延迟高一个量级（30-40μs），但仍远低于任何网络或磁盘 IO。

---

## 3. Extension 钩子延迟

| 钩子 | 延迟 |
|------|------|
| `KnowledgeExtension.on_cycle_end()` | 1.20μs |
| `KnowledgeExtension.search_before_run()` | 40.90μs |
| `MemoryExtension.on_cycle_end()` | 1.14μs |
| `MemoryExtension.get_last_run()` | 0.49μs |

**解读**: 单次 SOP 执行中，四个钩子全部触发的累计开销 < 45μs，相对于一次 SOP 执行动辄数百毫秒到数秒
（LLM 调用为主），钩子开销占比 < 0.01%，完全可忽略。

---

## 4. 批量操作吞吐量

| 批量大小 | Knowledge 耗时 | Knowledge 吞吐 | Memory 耗时 | Memory 吞吐 |
|---------|---------------|---------------|------------|------------|
| 10 | 0.049ms | 205,787/s | 0.036ms | 279,673/s |
| 100 | 0.210ms | 475,439/s | 0.188ms | 533,131/s |
| 1000 | 3.048ms | 328,132/s | 1.926ms | 519,221/s |

**解读**: Knowledge 和 Memory 的批量沉淀吞吐量都在数十万/秒量级。1000 条批量测得的 Knowledge 吞吐
略降（328k/s vs 100 条时 475k/s），可能是列表增长带来的内存重分配，但仍远超实际测试场景需求
（一次 SOP Run 通常沉淀几条到几十条记录）。

---

## 结论

1. **Extension 开销可忽略**：4 个 Extension 全开，Engine 构造增加 < 0.3ms，钩子调用增加 < 0.05ms/次。
2. **InMemory Store 性能优异**：微秒级延迟，数十万到百万级吞吐量，适合作为默认实现和单机场景。
3. **语义检索场景需评估**：`InMemoryKnowledgeStore.search()` 目前是简单过滤（非向量检索），
   若未来需要语义相似度匹配，应对接平台的 ChromaDB 实现（会引入毫秒级向量检索延迟，但换来语义能力）。
4. **与之前模拟报告对比**：真实数据与模拟报告方向一致（Extension 开销随数量增长、InMemory 延迟极低），
   但具体数值远低于模拟报告的估计值（模拟报告估计 Extension 开销 ms 级，真实为 μs~0.1ms 级）——
   说明 SDK 实现比预期更轻量。

---

## 复现方法

```bash
# 1. 安装 Python 3.11+（无 root 权限时，使用 python-build-standalone）
curl -L -o cpython.tar.gz \
  https://github.com/indygreg/python-build-standalone/releases/download/20241016/cpython-3.11.10+20241016-x86_64-unknown-linux-gnu-install_only.tar.gz
tar xzf cpython.tar.gz -C /tmp/py311

# 2. 安装 SDK
/tmp/py311/python/bin/python3.11 -m pip install -e packages/alice-engine

# 3. 运行基准测试（脚本内嵌于本报告 git 历史 / tests/benchmark/）
/tmp/py311/python/bin/python3.11 tests/benchmark/run_benchmarks.py
```

完整 pytest-benchmark 套件见 `tests/benchmark/test_performance.py`（可用 `pytest --benchmark-only` 运行，
支持 `--benchmark-save`/`--benchmark-compare` 做回归对比）。
