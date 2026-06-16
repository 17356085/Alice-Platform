# Skill: build/package-bundler

### 目标
机械化（不调 LLM）：执行前端构建（vite build）+ 后端打包，输出 BUILD_REPORT.md。

### 输入
- 前端：vite.config.ts
- 后端：pyproject.toml / Dockerfile

### 输出
- `BUILD_REPORT.md`：构建成功/失败、产物大小、警告

### 规则
- **Mechanical** 
- 前端：npm run build，记录产物大小
- 后端：pip install --dry-run 验证依赖，或 docker build

---

## Prompt 模板（无 LLM）

```bash
cd frontend && npm run build 2>&1
cd backend && pip install -e . --dry-run 2>&1
```
