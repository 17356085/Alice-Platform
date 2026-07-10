# Runtime → Infra 迁移计划

**执行日期**: 2026-07-09  
**任务**: Day 5-6 — 移动 `aitest/runtime/` → `aitest/infra/`

---

## 迁移文件清单

| 源文件 | 目标文件 | 依赖分析 | 优先级 |
|--------|---------|---------|--------|
| `aitest/runtime/_paths_core.py` | `aitest/infra/_paths_core.py` | 零依赖（叶子） | 1 |
| `aitest/runtime/config.py` | `aitest/infra/config.py` | 零依赖 | 2 |
| `aitest/runtime/context.py` | `aitest/infra/context.py` | 依赖 `_paths_core` | 3 |
| `aitest/runtime/paths.py` | `aitest/infra/paths.py` | 依赖 `_paths_core`, `platform.context` | 4 |
| `aitest/runtime/error_handling.py` | `aitest/infra/error_handling.py` | 依赖 `paths` | 5 |

---

## 导入更新清单（19 处）

### 使用 `aitest.runtime.config`

1. `aitest/adapters/llm/interface.py`
2. `aitest/adapters/llm/provider_base.py`
3. `aitest/config.py`
4. `aitest/llm/provider_base.py`

### 使用 `aitest.runtime.paths`

5. `aitest/adapters/audit/state.py`
6. `aitest/adapters/audit/sop.py`
7. `aitest/platform/ecosystem.py`
8. `aitest/platform/versioning.py`
9. `aitest/platform/_paths_core.py`
10. `aitest/platform/paths.py`
11. `aitest/platform/context.py`
12. `aitest/infra/paths.py`
13. `aitest/infra/error_logger.py`
14. `aitest/graphs/checkpoint.py`
15. `aitest/runtime/paths.py` (内部)

### 使用 `aitest.runtime.context`

16. `aitest/platform/context.py`
17. `aitest/runtime/context.py` (内部)

### 使用 `aitest.runtime.error_handling`

18. `aitest/runtime/error_handling.py` (内部)

### 使用 `aitest.runtime._paths_core`

19. `aitest/runtime/context.py`

### 测试文件

20. `aitest/tests/platform/test_provider_adapter.py`
21. `aitest/adapters/event/interface.py`

---

## 执行步骤

### Step 1: 移动文件（按依赖顺序）

```bash
# 1. 叶子模块（零依赖）
git mv aitest/runtime/_paths_core.py aitest/infra/_paths_core.py
git mv aitest/runtime/config.py aitest/infra/config.py

# 2. 依赖叶子的模块
git mv aitest/runtime/context.py aitest/infra/context.py
git mv aitest/runtime/paths.py aitest/infra/paths.py
git mv aitest/runtime/error_handling.py aitest/infra/error_handling.py

# 3. 删除空目录
rmdir aitest/runtime
```

### Step 2: 批量更新导入

```bash
# config.py
find aitest -name "*.py" -type f -exec sed -i 's/from aitest\.runtime\.config/from aitest.infra.config/g' {} \;
find aitest -name "*.py" -type f -exec sed -i 's/from aitest\.runtime import config/from aitest.infra import config/g' {} \;

# paths.py
find aitest -name "*.py" -type f -exec sed -i 's/from aitest\.runtime\.paths/from aitest.infra.paths/g' {} \;

# context.py
find aitest -name "*.py" -type f -exec sed -i 's/from aitest\.runtime\.context/from aitest.infra.context/g' {} \;

# error_handling.py
find aitest -name "*.py" -type f -exec sed -i 's/from aitest\.runtime\.error_handling/from aitest.infra.error_handling/g' {} \;

# _paths_core.py
find aitest -name "*.py" -type f -exec sed -i 's/from aitest\.runtime\._paths_core/from aitest.infra._paths_core/g' {} \;
```

### Step 3: 验证导入

```bash
# 检查是否还有残留的 aitest.runtime 导入
grep -rn "from aitest\.runtime" aitest/ | grep -v "__pycache__"

# 预期输出：空
```

### Step 4: 运行测试

```bash
# 单元测试
pytest aitest/tests/platform/ -v

# 集成测试
pytest aitest/tests/ -v
```

---

## 风险评估

### 高风险

- **循环导入**: `paths.py` 导入 `platform.context`，而 `context.py` 可能导入 `paths.py`
  - **缓解**: 已有 `_paths_core.py` 打破循环
  - **验证**: 检查 `platform/context.py` 的导入

### 中风险

- **内部相对导入**: `runtime/` 内部文件互相导入
  - **缓解**: 按依赖顺序迁移
  - **验证**: 移动后检查每个文件的导入

### 低风险

- **测试失败**: 路径变化可能影响测试
  - **缓解**: 运行完整测试套件
  - **回滚**: Git 保留历史，可快速回退

---

## 回滚计划

如果遇到问题：

```bash
# 回退文件移动
git mv aitest/infra/_paths_core.py aitest/runtime/_paths_core.py
git mv aitest/infra/config.py aitest/runtime/config.py
git mv aitest/infra/context.py aitest/runtime/context.py
git mv aitest/infra/paths.py aitest/runtime/paths.py
git mv aitest/infra/error_handling.py aitest/runtime/error_handling.py

# 回退导入更新
git checkout aitest/**/*.py
```

---

## 验证标准

- [ ] 所有 5 个文件已移动到 `aitest/infra/`
- [ ] `aitest/runtime/` 目录已删除
- [ ] 零处 `from aitest.runtime` 导入残留
- [ ] 所有测试通过
- [ ] 无导入错误

---

**预计工作量**: 2-3 小时  
**风险等级**: 中（循环导入风险）  
**回滚时间**: < 5 分钟
