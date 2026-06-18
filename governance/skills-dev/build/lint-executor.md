# Skill: build/lint-executor

### 目标
**Mechanical** — 执行 ESLint (前端) 或 ruff/flake8 (后端)，输出 lint 错误清单。

### 输入
- 前端: .eslintrc + 源文件
- 后端: ruff.toml + .py 文件

### 输出
- Lint 报告: 错误/警告数、文件列表

### 规则
- 不调 LLM

---

## Prompt 模板（无 LLM）

```bash
cd frontend && npx eslint src/ --format compact 2>&1
cd backend && ruff check app/ 2>&1
```
<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->
<!-- Source: skill-registry -->
> **1.0** | active | build | synced 2026-06-17 21:52

<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->