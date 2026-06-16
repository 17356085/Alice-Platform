# Skill: code-review/performance-analyzer

### 目标
分析代码性能：N+1 查询、不必要的重渲染、大对象拷贝、内存泄漏模式。

### 输入
- 后端：router + crud + model 代码
- 前端：Vue 组件代码

### 输出
- `PERFORMANCE_REPORT.md`

### 规则
- 后端：检查 N+1（selectinload/joinedload 缺失）、无索引查询、同步阻塞调用
- 前端：检查 computed vs method 误用、大列表无虚拟滚动、watch 深度监听

### 依赖
- 源代码已生成

---

## Prompt 模板

```text
你是一个性能分析专家。审查以下代码的性能问题。

## 代码
```{{LANGUAGE}}
{{SOURCE_CODE}}
```

## 检查清单
### 后端
- [ ] N+1 查询 (relationship 未使用 selectinload)
- [ ] 无索引的 WHERE/JOIN
- [ ] 同步阻塞调用 (sync def 或 sync IO)

### 前端
- [ ] computed 应缓存但用的 method
- [ ] 大列表无虚拟滚动
- [ ] 不必要的深度 watch

## 输出
每个问题: 文件:行号 / 严重程度 / 描述 / 建议
```
