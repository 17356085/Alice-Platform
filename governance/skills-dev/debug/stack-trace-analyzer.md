# Skill: debug/stack-trace-analyzer

### 目标
深度解析 JS/TS/Python 堆栈跟踪，映射到项目源文件，构建调用链图，输出 STACK_ANALYSIS.md。

### 输入
- 堆栈跟踪文本
- 项目源文件目录路径

### 输出
- `STACK_ANALYSIS.md`：含调用链、异常抛出点、关键变量状态推断

### 规则
- 区分：第三方库帧 vs 项目源文件帧
- 标注异步边界（async/await, Promise, callback）
- 对 Python 跟踪注意装饰器包装层
- 推断异常抛出前的变量状态（基于代码阅读，不猜测）

### 依赖
- debug/error-locator（可独立使用，也可接收其输出）

---

## Prompt 模板

```text
解析以下堆栈跟踪，标注调用链和异常传播路径。

## 堆栈跟踪
```
{{STACK_TRACE}}
```

## 输出
```markdown
# 堆栈分析

## 调用链（从入口到异常点）
入口: {{ENTRY_FUNCTION}}
  → {{CALLER_1}} ({{FILE}}:{{LINE}})
  → {{CALLER_2}} ({{FILE}}:{{LINE}})
  → 💥 {{EXCEPTION_POINT}} ({{FILE}}:{{LINE}})
    异常类型: {{EXCEPTION_TYPE}}
    异常消息: {{MESSAGE}}

## 关键帧分析
| # | 文件 | 行号 | 函数 | 说明 |
|---|------|------|------|------|
| 1 | src/... | 42 | handleClick | 用户点击处理入口 |
| 2 | src/... | 58 | fetchData | API 调用，此处异常抛出 |

## 状态推断
- {{VARIABLE}} 在异常前为 {{VALUE}}（根据 {{EVIDENCE}}）
```
```
<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->
<!-- Source: skill-registry -->
> **1.0** | active | debug | synced 2026-06-17 21:52

<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->