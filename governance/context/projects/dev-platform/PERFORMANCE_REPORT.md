## ⚠️ 缺少源代码输入

`code-review/performance-analyzer` Skill 需要**后端代码**（router/crud/model）和/或**前端代码**（Vue 组件）才能执行分析。你目前只提供了模块名 `aitest-platform`。

---

### 请提供以下任一内容：

```text
1. 后端文件：FastAPI router / SQLAlchemy model / CRUD service 代码
2. 前端文件：Vue 组件代码
3. 或者直接粘贴需要审查的代码片段
```

---

### 我会输出：

`PERFORMANCE_REPORT.md` — 按文件:行号标注性能问题，含严重程度和建议，覆盖：

| 后端 | 前端 |
|------|------|
| N+1 查询（`selectinload` 缺失） | `computed` vs `method` 误用 |
| 无索引 WHERE/JOIN | 大列表无虚拟滚动 |
| 同步阻塞调用 | 不必要的深度 `watch` |
| 大对象拷贝 / 内存泄漏模式 | 重复渲染触发 |

请粘贴代码，我即刻开始分析。