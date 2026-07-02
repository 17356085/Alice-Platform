## 无法完成 — 缺少必要输入

当前状态：

| 条件 | 状态 |
|------|------|
| RAG 知识库搜索 | ❌ 不可用（`No available provider for 'rag.search'`） |
| 项目目标 | ❓ 未提供 |
| PROJECT_STRUCTURE.md | ❓ 未提供 |
| TECH_STACK.md | ❓ 未提供 |

`plan/create-project-plan` 这个 Skill 依赖三个核心输入才能生成 `PROJECT_PLAN.md`：

1. **用户目标描述** — 要搭建什么、实现什么功能
2. **PROJECT_STRUCTURE.md** — 现有项目文件/目录结构
3. **TECH_STACK.md** — 技术栈约束（框架、语言、工具链）

目前这些信息都缺失，我无法凭空生成可执行的任务分解。

---

**请提供以下任一方式继续：**

- 直接粘贴目标描述 + 项目结构 + 技术栈
- 或者告诉我项目名称 / 代码仓库路径，我尝试从文件系统读取 `PROJECT_STRUCTURE.md` 和 `TECH_STACK.md`