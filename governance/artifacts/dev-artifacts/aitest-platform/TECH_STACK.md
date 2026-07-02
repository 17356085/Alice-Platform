---

## 后端技术栈

| 技术 | 版本 | 类型 | 理由 |
|------|------|------|------|
| **Python** | `>=3.11,<3.13` | core | `asyncio` 任务组 (`asyncio.TaskGroup`) 是 Agent 并发执行 Phase 的基础设施；`match-case` 优雅处理 SOP 状态分支 |
| **FastAPI** | `^0.115.0` | core | 原生 async/await、自动 OpenAPI 文档、依赖注入 (`Depends`) 完美映射 Agent → Skill → Phase 的分层依赖链 |
| **SQLAlchemy** | `^2.0.35` | core | 2.0 style (`select()` + `Result.scalars()`) 异步支持；`MappedAsDataclass` 与 Pydantic schema 双向映射 |
| **Pydantic** | `^2.9.0` | core | FastAPI 原生数据验证；`BaseModel.model_validate()` 解析 YAML 治理配置；`TypeAdapter` 校验 Skill 注册表 |
| **asyncpg** | `^0.29.0` | core | 高性能异步 PostgreSQL 驱动；连接池复用 Agent 的并行 DB 查询；速度比 psycopg2 快 3x |
| **aiosqlite** | `^0.20.0` | dev | 异步 SQLite 驱动，用于开发环境/CI 轻量测试；无需额外数据库服务 |
| **PyYAML** | `^6.0.2` | core | 解析 `skill-registry.yaml`、`sop-config.yaml`；搭配 `yaml.CLoader` 保证速度 |
| **httpx** | `^0.27.0` | core | Agent HTTP 客户端（异步）；调用外部测试目标、Selenium Grid、通知 Webhook |
| **python-multipart** | `^0.0.12` | core | FastAPI 文件上传（Skill `.md` 文件通过治理面板上传） |
| **uvicorn** | `^0.30.0` | core | ASGI 服务器；`--workers 4` 生产部署；`--reload` 开发热重载 |
| **watchfiles** | `^0.24.0` | dev | uvicorn `--reload` 的文件监听后端；比默认 `watchgod` 更快 |
| **pytest** | `^8.3.0` | dev | 异步测试 (`pytest-asyncio`) + fixture yield teardown，与项目 Fixture 治理概念天然契合 |
| **pytest-asyncio** | `^0.24.0` | dev | FastAPI `TestClient` + 异步数据库 session |
| **pytest-cov** | `^5.0.0` | dev | 覆盖率报告；SOP Gate 要求 Phase 测试覆盖 >= 80% |
| **ruff** | `^0.6.0` | dev | Rust 实现，替代 flake8 + isort + pyflakes；lint + format 一条命令；与 ESLint/Prettier 前端工具链对称 |
| **mypy** | `^1.11.0` | dev | 严格类型检查 (`strict = true`)；与前端 TypeScript 保持类型安全对称 |

### requirements.txt