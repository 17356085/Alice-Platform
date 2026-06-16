# Skill: debug/regression-verifier

### 目标
修复完成后，验证：(1) 原始错误不再出现，(2) 未引入新回归，(3) 相关测试通过。输出 REGRESSION_REPORT.md。

### 输入
- fix 涉及的源文件列表
- 关联的测试文件
- 构建/测试运行输出

### 输出
- `REGRESSION_REPORT.md`：含原始错误状态、新回归检查、测试结果

### 规则
- 必须重新运行原始错误触发场景
- 运行关联测试文件（pytest/test runner）
- 检查 fix 影响的文件是否有新的 lint/type 错误
- 如果有回归，标注严重程度

### 依赖
- debug/fix-suggester（修复已完成）
- build-agent 的执行输出

### 边界
- 不修改代码
- 只报告结果，不自动回滚

---

## Prompt 模板

```text
验证以下修复方案是否正确实施且无回归。

## 修复方案
{{FIX_PROPOSAL}}

## 构建/测试输出
```
{{BUILD_OUTPUT}}
```

## 验证清单
- [ ] 原始错误不再出现
- [ ] 无新增 lint/type 错误
- [ ] 关联测试全部通过
- [ ] 受影响文件无退化

## 输出
```markdown
# 回归验证报告

## 原始错误状态
- 错误: {{ORIGINAL_ERROR}}
- 状态: ✅已修复 / ❌仍存在

## 新回归检查
| 检查项 | 结果 | 详情 |
|--------|------|------|
| lint | ✅/❌ | N errors |
| type check | ✅/❌ | N errors |
| 单元测试 | ✅/❌ | X/Y passed |

## 结论
- ✅ 修复成功，无回归
- ⚠️ 修复成功，有非阻塞警告
- ❌ 修复引入回归，需要重新修复
```
```
