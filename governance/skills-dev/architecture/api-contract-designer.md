# Skill: architecture/api-contract-designer

### 目标
基于组件树和数据模型，设计完整的 REST API 契约，包含端点列表、请求/响应 Schema、错误码、分页规范，生成 API_CONTRACTS.md。

### 输入
- `COMPONENT_TREE.md` — 组件树和数据流向
- `DATA_MODEL.md` — 数据模型定义（如有）
- 功能需求描述

### 输出
- `API_CONTRACTS.md`：含端点列表、Schema 定义、错误码规范

### 规则
- 遵循 RESTful 命名规范（复数名词、层级资源）
- 每个端点必须指定：Method、Path、Auth、Request Body、Response Body、Error Codes
- 使用 OpenAPI 3.0 风格的伪 Schema 描述
- 分页接口统一格式：`{ items: [], total: int, page: int, page_size: int }`

### 依赖
- architecture/component-tree-designer（需 COMPONENT_TREE.md）

### 边界
- 不实现 API 代码
- 不设计数据库表结构（那是 DATA_MODEL.md 的职责）
- 不定义具体的业务逻辑

### 检查清单
- [ ] 每个资源的 CRUD 端点完整
- [ ] 请求和响应的 Schema 字段完整
- [ ] 错误码覆盖 400/401/403/404/409/500
- [ ] 分页接口统一格式
- [ ] 认证标注（哪些端点需要 auth）
- [ ] 输出格式符合 API_CONTRACTS.md 模板

### 产出物
- 文件路径: `{{module_dir}}/API_CONTRACTS.md`
- 格式: Markdown，含 `## 资源端点` `## Schema 定义` `## 错误码` `## 通用规范`

---

## Prompt 模板

```text
你是一个资深后端架构师。请设计完整的 REST API 契约。

## 组件树和数据流向
{{COMPONENT_TREE_CONTENT}}

## 数据模型
{{DATA_MODEL_CONTENT}}

## 功能需求
{{FEATURE_DESCRIPTION}}

## 任务
1. 为每个资源（如 users, products, orders）列出完整的 CRUD 端点
2. 定义请求和响应的 JSON Schema
3. 定义错误码规范
4. 定义分页、排序、过滤的通用参数规范

## 输出格式
```markdown
# API 契约 — {{PROJECT_NAME}}

## 基础 URL
`/api/v1`

## 认证
Header: `Authorization: Bearer {{token}}`

## 资源端点

### Users
| Method | Path | Auth | 描述 | Request | Response |
|--------|------|------|------|---------|----------|
| GET | /users | Yes | 用户列表 | Query: page, page_size, sort_by, q | PaginatedResponse<User> |
| GET | /users/{id} | Yes | 用户详情 | - | UserResponse |
| POST | /users | Yes | 创建用户 | UserCreate | UserResponse |
| PUT | /users/{id} | Yes | 更新用户 | UserUpdate | UserResponse |
| DELETE | /users/{id} | Yes | 删除用户 | - | 204 No Content |

## Schema 定义

### UserResponse
` ` `json
{
  "id": "uuid",
  "username": "string",
  "email": "string",
  "role": "admin | user",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
` ` `

### UserCreate
` ` `json
{
  "username": "string (required, 3-50 chars)",
  "email": "string (required, valid email)",
  "password": "string (required, min 8 chars)",
  "role": "user (default)"
}
` ` `

### UserUpdate
` ` `json
{
  "username": "string (optional)",
  "email": "string (optional)",
  "role": "admin | user (optional)",
  "is_active": true (optional)
}
` ` `

### PaginatedResponse<T>
` ` `json
{
  "items": ["T[]"],
  "total": 100,
  "page": 1,
  "page_size": 20
}
` ` `

## 错误码
| Code | 含义 | 示例消息 |
|------|------|----------|
| 400 | 请求参数错误 | "username is required" |
| 401 | 未认证 | "Invalid or expired token" |
| 403 | 无权限 | "Admin role required" |
| 404 | 资源不存在 | "User not found" |
| 409 | 资源冲突 | "Username already exists" |
| 422 | 数据验证失败 | "email must be valid" |
| 500 | 服务器内部错误 | "Internal server error" |

## 通用查询参数
| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| page | int | 1 | 页码 |
| page_size | int | 20 | 每页数量 (max 100) |
| sort_by | string | "created_at" | 排序字段 |
| sort_order | "asc"\|"desc" | "desc" | 排序方向 |
| q | string | - | 全局搜索关键词 |
```
```
