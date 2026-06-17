# Skill: test-dev/unit-test-generator

### 目标
为给定的源文件生成 pytest + pytest-asyncio 单元测试（后端）或 Vitest 单元测试（前端）。

### 输入
- 源文件内容
- 函数/组件签名（Props、参数类型、返回值类型）
- 编码规范

### 输出
- 测试文件（`test_*.py` 或 `*.test.ts`）

### 规则
- 后端: pytest + pytest-asyncio + httpx (API) 或直接调用 (纯函数)
- 前端: Vitest + @vue/test-utils (组件) 或 vitest (纯函数)
- 覆盖：happy path / 边界值 / 错误处理 / 空/null 输入
- Mock 外部依赖（DB、网络、文件系统）
- 不要测试框架代码（如 FastAPI 的自动验证）

### 依赖
- 源文件已生成

---

## Prompt 模板

```text
你是一个资深测试工程师。为以下源文件生成完整的单元测试。

## 源文件
```python
{{SOURCE_CODE}}
```

## 覆盖目标
1. Happy path — 正常输入得到预期输出
2. Edge cases — 边界值、空值、特殊字符
3. Error handling — 异常输入的正确处理
4. 目标覆盖率: ≥80%

## 规则
- pytest + pytest-asyncio
- Mock 外部依赖（DB session, HTTP client）
- 每个测试有清晰的三段式: arrange → act → assert
- 测试函数名描述测试场景: test_<function>_<scenario>_<expected>

## 输出
只输出完整的测试文件代码。
```
<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->
<!-- Source: skill-registry -->
> **1.0** | active | test-dev | synced 2026-06-17 16:53

<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->