# Skill: build/type-checker

### 目标
**Mechanical** — 执行 tsc --noEmit (前端) 或 mypy (后端)，输出类型错误清单。

### 输入
- 前端: tsconfig.json + .ts/.vue 文件
- 后端: pyproject.toml + .py 文件

### 输出
- 类型检查报告: 错误数、文件列表

### 规则
- 不调 LLM — 直接执行命令行

---

## Prompt 模板（无 LLM）

```bash
cd frontend && npx tsc --noEmit 2>&1
cd backend && mypy app/ 2>&1
```
