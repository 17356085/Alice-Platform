# Skill: test-dev/coverage-checker

### 目标
机械化检查（不调 LLM）：运行 pytest --cov 或 vitest --coverage，解析覆盖率报告，标注未覆盖的函数/分支。

### 输入
- 测试运行输出或 coverage.xml / coverage.json

### 输出
- `COVERAGE_REPORT.md`：含覆盖率%、未覆盖项清单

### 规则
- **Mechanical** — 直接执行 pytest --cov 或 vitest run --coverage
- 未覆盖 <80% 标注为 ⚠️
- 未覆盖 <60% 标注为 ❌
- 列出 Top 10 未覆盖函数/分支

### 依赖
- test-dev/unit-test-generator 或 test-dev/integration-test-generator

---

## Prompt 模板（无 LLM — 纯脚本）

```bash
pytest --cov=app --cov-report=term-missing tests/ 2>&1
```
<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->
<!-- Source: skill-registry -->
> **1.0** | active | test-dev | synced 2026-06-17 21:52

<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->