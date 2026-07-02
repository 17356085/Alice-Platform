# Skill: debug/error-locator

### 目标
读取错误日志/堆栈跟踪/测试失败输出，定位根本原因文件和行号，生成 ERROR_DIAGNOSIS.md。

### 输入
- 错误输出（pytest/tsc/eslint/浏览器控制台）
- 相关联的源文件

### 输出
- `ERROR_DIAGNOSIS.md`：含根因定位、影响范围、修复方向

### 规则
- 先读错误信息 → 再读源文件 → 最后推断根因（不可跳过读文件）
- 区分：语法错误 / 类型错误 / 逻辑错误 / 依赖错误 / 运行时错误
- 定位到具体文件和行号
- 影响范围标注（该修复会影响哪些其他文件）

### 依赖
- 无前置 Skill（输入来自 build-agent 的执行输出）

### 边界
- 不修改代码
- 不执行修复（那是 fix-suggester 的职责）
- 1 次只分析 1 类错误（相同根因的错误可合并）

---

## Prompt 模板

```text
你是一个资深调试专家。请分析以下错误输出，定位根本原因。

## 错误输出
```
{{ERROR_OUTPUT}}
```

## 相关源文件
{{SOURCE_FILES}}

## 分析步骤（严格按顺序）
1. 解析错误类型（Syntax/Type/Logic/Dependency/Runtime）
2. 定位错误文件和行号
3. 读取相关源文件（确认上下文）
4. 推断根本原因（不是表面现象）
5. 标注影响范围（哪些其他文件/函数受影响）
6. 提出修复方向（不写具体代码）

## 输出
```markdown
# 错误诊断

## 错误摘要
- 类型: {{TYPE}}
- 文件: {{FILE}}:{{LINE}}
- 错误: {{MESSAGE}}

## 根因分析
{{ROOT_CAUSE}}

## 影响范围
- 直接影响: {{FILE_LIST}}
- 间接影响: {{DEPENDENT_FILES}}

## 修复方向
1. ...
2. ...
```
```
<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->
<!-- Source: skill-registry -->
> **1.0** | active | debug | synced 2026-06-18 10:54

<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->