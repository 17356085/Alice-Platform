# SDK 迁移执行清单

**目标**: 从 70% → 85% 完成度  
**时间**: 2-3 周  
**负责人**: [待填写]  
**开始日期**: [待填写]

---

## 第 1 周：审计与验证

### Day 1-2: 依赖关系审计

- [ ] **检查 1**: SDK 无平台依赖
  ```bash
  cd packages/alice-engine
  grep -r "from aitest\." alice_engine/ | grep -v "test" | grep -v "__pycache__" > /tmp/sdk-platform-deps.txt
  ```
  - [ ] 检查输出是否为空
  - [ ] 如有结果，记录到 `docs/architecture/cleanup-audit.md`

- [ ] **检查 2**: CLI 使用 SDK 公共 API
  ```bash
  cd /path/to/Alice
  grep -r "from aitest\.engine\." aitest/cli/ > /tmp/cli-engine-imports.txt
  grep -r "from aitest\.graphs\." aitest/cli/ > /tmp/cli-graphs-imports.txt
  grep -r "from aitest\.llm\." aitest/cli/ > /tmp/cli-llm-imports.txt
  ```
  - [ ] 检查所有输出是否为空
  - [ ] 如有结果，记录哪些 CLI 文件需要重构

- [ ] **检查 3**: Discovery 重复
  ```bash
  grep -r "from aitest\.discovery" . | grep -v "__pycache__" > /tmp/discovery-usage.txt
  ```
  - [ ] 统计使用次数
  - [ ] 记录哪些文件导入 `aitest.discovery`

- [ ] **检查 4**: 弃用的 providers
  ```bash
  grep -r "from aitest\.llm\.providers" . | grep -v "__pycache__" > /tmp/providers-usage.txt
  ```
  - [ ] 检查输出是否为空
  - [ ] 如为空 → 标记可删除

- [ ] **检查 5**: aitest/runtime/ 依赖分析
  ```bash
  cd aitest/runtime
  # 检查是否导入平台模块
  grep -r "^from aitest\." *.py | grep -v "from aitest.runtime" > /tmp/runtime-platform-deps.txt
  # 检查是否导入 SDK
  grep -r "^from alice_engine" *.py > /tmp/runtime-sdk-deps.txt
  ```
  - [ ] 分析 `config.py` 的依赖
  - [ ] 分析 `context.py` 的依赖
  - [ ] 分析 `error_handling.py` 的依赖
  - [ ] 分析 `paths.py` 的依赖
  - [ ] 分析 `_paths_core.py` 的依赖
  - [ ] 决策：SDK 还是 Platform？

### Day 3: 文档审计结果

- [ ] **创建审计报告**: `docs/architecture/cleanup-audit-2026-07-09.md`
  - [ ] 记录所有 grep 结果
  - [ ] 标记需要迁移的导入
  - [ ] 标记可删除的模块
  - [ ] 明确 `aitest/runtime/` 归属决策

- [ ] **更新任务清单**
  - [ ] 根据审计结果更新本清单
  - [ ] 评估工作量（是否需要调整时间估算）

---

## 第 2 周：清理与删除

### Day 4: 删除重复/弃用代码

- [ ] **删除 aitest/llm/providers/** （如果审计确认未使用）
  ```bash
  # 备份（以防万一）
  tar -czf aitest-llm-providers-backup.tar.gz aitest/llm/providers/
  
  # 删除
  rm -rf aitest/llm/providers/
  
  # 提交
  git add -A
  git commit -m "chore: 删除弃用的 llm providers（已迁移至 alice-engine）"
  ```
  - [ ] 运行测试确认无破坏
  - [ ] 推送到远程分支

- [ ] **删除 aitest/discovery/** （如果审计确认可迁移）
  - [ ] 先迁移所有 `from aitest.discovery` → `from alice_discovery`
  - [ ] 运行测试确认迁移正确
  - [ ] 删除目录
    ```bash
    tar -czf aitest-discovery-backup.tar.gz aitest/discovery/
    rm -rf aitest/discovery/
    git add -A
    git commit -m "chore: 删除重复的 discovery 模块（使用 alice-discovery 包）"
    ```

### Day 5-6: 解决 aitest/runtime/ 归属

#### 选项 A: 移至 SDK（如果是 SDK 级别工具）

- [ ] 创建目标目录
  ```bash
  mkdir -p packages/alice-engine/alice_engine/runtime/utils
  ```

- [ ] 移动文件
  ```bash
  mv aitest/runtime/config.py packages/alice-engine/alice_engine/runtime/utils/
  mv aitest/runtime/context.py packages/alice-engine/alice_engine/runtime/utils/
  mv aitest/runtime/error_handling.py packages/alice-engine/alice_engine/runtime/utils/
  mv aitest/runtime/paths.py packages/alice-engine/alice_engine/runtime/utils/
  mv aitest/runtime/_paths_core.py packages/alice-engine/alice_engine/runtime/utils/
  ```

- [ ] 更新所有导入（自动化脚本或手动）
  ```bash
  # 示例：更新 config 导入
  find . -name "*.py" -type f -exec sed -i 's/from aitest\.runtime\.config/from alice_engine.runtime.utils.config/g' {} \;
  ```

- [ ] 运行测试
  ```bash
  pytest aitest/tests/
  pytest packages/alice-engine/tests/
  ```

- [ ] 提交
  ```bash
  git add -A
  git commit -m "refactor: 将 runtime 工具移至 alice-engine SDK"
  ```

#### 选项 B: 移至平台（如果仅平台使用）

- [ ] 创建目标目录
  ```bash
  mkdir -p aitest/infra/runtime
  ```

- [ ] 移动并更新导入（类似选项 A）

- [ ] 提交
  ```bash
  git commit -m "refactor: 将 runtime 工具移至平台 infra"
  ```

#### 选项 C: 拆分（如果混合使用）

- [ ] 按依赖分析结果拆分文件
- [ ] SDK 级别 → `alice-engine/runtime/utils/`
- [ ] 平台级别 → `aitest/infra/runtime/`

### Day 7: 明确 aitest/graphs/ 归属

- [ ] **比较文件**
  ```bash
  diff aitest/graphs/state.py packages/alice-engine/alice_engine/workflow/state.py
  diff aitest/graphs/checkpoint.py packages/alice-engine/alice_engine/workflow/checkpoint.py
  ```

- [ ] **决策路径 A**: 如果重复 → 合并到 SDK
  - [ ] 删除 `aitest/graphs/`
  - [ ] 更新导入为 `from alice_engine.workflow import ...`
  - [ ] 测试

- [ ] **决策路径 B**: 如果是平台包装器 → 重命名
  ```bash
  mv aitest/graphs/ aitest/platform/workflow_utils/
  # 更新导入
  git commit -m "refactor: 重命名 graphs 为 platform/workflow_utils 以明确归属"
  ```

---

## 第 3 周：重构与验证

### Day 8-10: CLI 导入重构

- [ ] **列出需要重构的 CLI 文件**（根据 Day 1-2 审计结果）
  - [ ] `aitest/cli/commands/graph/run.py` （示例）
  - [ ] `aitest/cli/commands/...` （其他文件）

- [ ] **逐文件重构**（每个文件一次提交）

  示例：`aitest/cli/commands/graph/run.py`
  
  - [ ] 备份原文件
  - [ ] 替换导入
    ```python
    # 之前
    from aitest.graphs.sop_graph import build_graph
    from aitest.engine.executor import AgentLoop
    
    # 之后
    from alice_engine import Engine
    from alice_engine.workflow import WorkflowBuilder
    ```
  - [ ] 调整代码逻辑以使用 SDK 公共 API
  - [ ] 运行该命令测试
    ```bash
    aitest graph run --module equipment --pages alarm-config
    ```
  - [ ] 提交
    ```bash
    git commit -m "refactor(cli): graph/run 使用 SDK 公共 API"
    ```

- [ ] **所有 CLI 文件重构完成后**
  - [ ] 运行完整 CLI 测试套件
  - [ ] 手动测试所有主要命令

### Day 11: 独立 SDK 验证

- [ ] **创建测试环境**
  ```bash
  mkdir /tmp/sdk-standalone-test
  cd /tmp/sdk-standalone-test
  python -m venv .venv
  source .venv/bin/activate  # Windows: .venv\Scripts\activate
  ```

- [ ] **安装 SDK（仅 SDK）**
  ```bash
  pip install /path/to/Alice/packages/alice-engine
  pip install /path/to/Alice/packages/alice-governance
  pip install /path/to/Alice/packages/alice-discovery
  ```

- [ ] **编写测试脚本**
  ```python
  # test_sdk_standalone.py
  from alice_engine import Engine, Project
  from alice_engine.providers import get_provider
  
  print("✓ SDK 导入成功")
  
  # 测试创建 Engine
  project = Project("./test-project")
  engine = Engine(project=project, mock_llm=True)
  print("✓ Engine 创建成功")
  
  # 测试运行（mock 模式）
  result = engine.run("equipment", pages=["alarm-config"])
  print(f"✓ 执行完成: {result['status']}")
  
  print("\n=== SDK 独立性验证通过 ===")
  ```

- [ ] **运行测试**
  ```bash
  python test_sdk_standalone.py
  ```
  - [ ] 验证无 `aitest.*` 导入错误
  - [ ] 验证可以创建 Engine
  - [ ] 验证可以执行（mock 模式）

- [ ] **记录结果**
  - [ ] 截图或日志保存到 `docs/architecture/sdk-standalone-test-result.md`

### Day 12: 更新文档

- [ ] **更新 ADR**
  - [ ] `docs/adr/ADR_002_SDK_ARCHITECTURE.md`
  - [ ] 记录最终的模块归属
  - [ ] 更新依赖关系图

- [ ] **SDK README**
  - [ ] `packages/alice-engine/README.md`
  - [ ] 添加快速开始示例
  - [ ] 添加公共 API 文档链接
  - [ ] 添加安装说明

- [ ] **创建迁移指南**
  - [ ] `docs/guides/platform-to-sdk-migration.md`
  - [ ] 说明如何从 `aitest.*` 迁移到 `alice_engine`
  - [ ] 提供常见导入的替换示例

- [ ] **更新主 README**
  - [ ] `README.md`
  - [ ] 更新架构说明
  - [ ] 添加 SDK 使用示例

---

## 最终验证

### Day 13: 完整性检查

- [ ] **运行所有自动检查**
  ```bash
  # 1. SDK 无平台依赖
  cd packages/alice-engine
  test $(grep -r "from aitest\." alice_engine/ | grep -v test | grep -v __pycache__ | wc -l) -eq 0
  echo "✓ SDK 无平台依赖"
  
  # 2. CLI 无内部导入
  cd /path/to/Alice
  test $(grep -r "from aitest\.engine\." aitest/cli/ | wc -l) -eq 0
  test $(grep -r "from aitest\.graphs\." aitest/cli/ | wc -l) -eq 0
  echo "✓ CLI 使用 SDK 公共 API"
  
  # 3. 无重复模块
  test ! -d aitest/discovery
  test ! -d aitest/llm/providers
  echo "✓ 无重复/弃用模块"
  ```

- [ ] **运行完整测试套件**
  ```bash
  # SDK 测试
  cd packages/alice-engine
  pytest tests/
  
  # 平台测试
  cd /path/to/Alice
  pytest aitest/tests/
  
  # 集成测试
  pytest tests/
  ```

- [ ] **手动冒烟测试**
  - [ ] CLI: `aitest server start`
  - [ ] CLI: `aitest graph run --module equipment`
  - [ ] Web: 访问 http://localhost:8000/chat
  - [ ] SDK: 独立项目测试（Day 11 的测试）

- [ ] **代码审查**
  - [ ] 创建 Pull Request
  - [ ] 标题：`refactor: SDK 迁移清理（70% → 85%）`
  - [ ] 描述包含：
    - [ ] 审计报告链接
    - [ ] 完成的任务清单
    - [ ] 测试结果
    - [ ] 破坏性变更说明（如有）

---

## 成功标准核对

### 必须完成（Must-Have）

- [ ] SDK 从 `aitest.*` 零导入（测试除外）
- [ ] Platform/CLI 仅通过 SDK 公共 API 导入
- [ ] 无重复模块（discovery、providers 已删除）
- [ ] 无弃用代码（或已记录保留原因）
- [ ] 独立 SDK 项目验证通过

### 建议完成（Should-Have）

- [ ] `aitest/runtime/` 归属已明确（已移动）
- [ ] `aitest/graphs/` 关系已记录/重构
- [ ] 文档已更新（ADR、README、迁移指南）

### 可选完成（Nice-to-Have）

- [ ] SDK 发布到内部 PyPI
- [ ] 创建 SDK 示例项目目录
- [ ] 添加公共 API 参考文档

---

## 回滚计划

如果在任何阶段遇到严重问题：

### 紧急回滚步骤

1. **恢复备份文件**
   ```bash
   # 如果删除了 providers
   tar -xzf aitest-llm-providers-backup.tar.gz
   
   # 如果删除了 discovery
   tar -xzf aitest-discovery-backup.tar.gz
   ```

2. **回退 Git 提交**
   ```bash
   git log --oneline  # 找到问题提交之前的 commit
   git revert <commit-hash>
   # 或硬回退（谨慎）
   git reset --hard <commit-hash>
   ```

3. **通知团队**
   - 在 #architecture 频道说明回滚原因
   - 记录遇到的问题
   - 重新评估时间计划

---

## 进度跟踪

| 阶段 | 任务数 | 已完成 | 进度 | 负责人 | 状态 |
|------|--------|--------|------|--------|------|
| 第 1 周：审计 | 8 | 0 | 0% | [填写] | 未开始 |
| 第 2 周：清理 | 4 | 0 | 0% | [填写] | 未开始 |
| 第 3 周：重构 | 5 | 0 | 0% | [填写] | 未开始 |
| 最终验证 | 3 | 0 | 0% | [填写] | 未开始 |

---

## 附录：常用命令

### 批量搜索替换导入

```bash
# 示例：替换 aitest.runtime.config → alice_engine.runtime.utils.config
find . -name "*.py" -type f -not -path "./.venv/*" -not -path "./__pycache__/*" \
  -exec sed -i 's/from aitest\.runtime\.config/from alice_engine.runtime.utils.config/g' {} \;

# 示例：替换 aitest.graphs → alice_engine.workflow
find . -name "*.py" -type f -not -path "./.venv/*" \
  -exec sed -i 's/from aitest\.graphs/from alice_engine.workflow/g' {} \;
```

### 运行特定模块测试

```bash
# 仅测试 SDK
pytest packages/alice-engine/tests/ -v

# 仅测试 CLI
pytest aitest/tests/cli/ -v

# 仅测试 Platform
pytest aitest/tests/platform/ -v
```

### 生成依赖关系图

```bash
# 安装 pydeps
pip install pydeps

# 生成 SDK 依赖图
cd packages/alice-engine
pydeps alice_engine --max-bacon=2 -o alice-engine-deps.svg

# 生成平台依赖图
cd /path/to/Alice
pydeps aitest --max-bacon=2 --exclude aitest.tests -o aitest-deps.svg
```

---

## 联系与支持

- **Slack 频道**: #architecture
- **负责人**: [填写]
- **审查人**: [填写]
- **紧急联系**: [填写]

---

**最后更新**: 2026-07-09  
**版本**: 1.0
