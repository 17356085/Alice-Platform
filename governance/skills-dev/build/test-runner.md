# Skill: build/test-runner

### 目标
机械化（不调 LLM）：执行 pytest / vitest，收集结果，统计通过/失败/跳过，输出 TEST_RESULTS.md。

### 输入
- 测试文件列表
- 测试框架配置

### 输出
- `TEST_RESULTS.md`：通过/失败/跳过统计 + 失败用例详情

### 规则
- **Mechanical** — 直接执行 pytest 或 vitest run
- 解析 JUnit XML 或终端输出
- 失败用例提取错误消息和前 5 行堆栈

---

## Prompt 模板（无 LLM — 纯脚本）

```bash
# Backend
cd backend && python -m pytest tests/ -v --tb=short 2>&1

# Frontend  
cd frontend && npx vitest run --reporter=verbose 2>&1
```
<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->
<!-- Source: skill-registry -->
> **1.0** | active | build | synced 2026-06-17 21:52

<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->