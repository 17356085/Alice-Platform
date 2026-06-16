# Skill: architecture/tech-stack-decider

### 目标
基于 PROJECT_STRUCTURE.md 的扫描结果，分析现有依赖，推荐最优技术栈，生成 TECH_STACK.md。

### 输入
- `PROJECT_STRUCTURE.md` — 项目结构分析结果
- 现有的 package.json / requirements.txt（如有）
- 用户偏好（可选）

### 输出
- `TECH_STACK.md`：包含推荐技术栈、版本号、决策理由

### 规则
- 优先复用项目现有依赖，避免不必要的迁移
- 每个推荐必须附带决策理由（为什么选 A 不选 B）
- 版本号必须指定具体版本或范围，不可写 "latest"
- 目标栈：Vue 3 + TypeScript + Vite (前端) / FastAPI + SQLAlchemy 2.0 + Pydantic v2 (后端)
- 如项目已有不同栈，分析兼容性而非强制迁移

### 依赖
- architecture/project-scanner（需 PROJECT_STRUCTURE.md）

### 边界
- 不安装任何依赖
- 不修改 package.json 或其他配置文件
- 不处理部署/CI 相关技术选型

### 检查清单
- [ ] 每个推荐有决策理由
- [ ] 版本号具体明确
- [ ] 前端栈和后端栈分别列出
- [ ] 考虑了项目现有依赖
- [ ] 标注了必选 vs 可选依赖
- [ ] 输出格式符合 TECH_STACK.md 模板

### 产出物
- 文件路径: `{{module_dir}}/TECH_STACK.md`
- 格式: Markdown，含 `## 前端技术栈` `## 后端技术栈` `## 共享依赖` `## 决策记录`

---

## Prompt 模板

```text
你是一个资深全栈架构师。请基于项目结构分析，推荐最优技术栈。

## 项目结构分析
{{PROJECT_STRUCTURE_CONTENT}}

## 约束条件
- 前端目标：Vue 3 + Composition API + TypeScript + Vite + Element Plus
- 后端目标：FastAPI + SQLAlchemy 2.0 + Pydantic v2 + PostgreSQL/SQLite
- 优先复用项目现有依赖

## 任务
1. 分析现有依赖的版本和兼容性
2. 为每个技术选型提供决策理由
3. 标注必选（core）vs 可选（dev/optional）依赖
4. 给出完整的 package.json dependencies 和 requirements.txt 推荐

## 输出格式
```markdown
# 技术栈 — {{PROJECT_NAME}}

## 前端技术栈
| 技术 | 版本 | 类型 | 理由 |
|------|------|------|------|
| Vue | 3.4+ | core | Composition API + TypeScript 完整支持 |
| Vite | 5.x | core | 快速 HMR，Vue 官方推荐 |
| TypeScript | 5.x | core | 类型安全 |
| Element Plus | 2.x | core | 成熟的企业级 Vue 3 UI 库 |
| Pinia | 2.x | core | Vue 3 官方状态管理 |
| Vue Router | 4.x | core | 路由管理 |
| ESLint | 9.x | dev | 代码规范检查 |
| Prettier | 3.x | dev | 代码格式化 |

## 后端技术栈
| 技术 | 版本 | 类型 | 理由 |
|------|------|------|------|
| FastAPI | 0.110+ | core | 高性能异步框架，自动 OpenAPI |
| SQLAlchemy | 2.0+ | core | 2.0 style ORM |
| Pydantic | 2.x | core | FastAPI 原生数据验证 |
| asyncpg | 0.29+ | core | 异步 PostgreSQL 驱动 |
| aiosqlite | 0.20+ | dev | 异步 SQLite (测试用) |
| pytest | 8.x | dev | 测试框架 |
| httpx | 0.27+ | dev | 异步 HTTP 测试客户端 |

## 决策记录
1. **Vue 3 vs React**: ...
2. **FastAPI vs Django Ninja**: ...
```
```
