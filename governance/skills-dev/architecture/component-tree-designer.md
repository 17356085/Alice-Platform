# Skill: architecture/component-tree-designer

### 目标
基于需求和技术栈，设计页面-组件层级树，定义每个组件的职责、Props 接口方向、路由映射，生成 COMPONENT_TREE.md。

### 输入
- `TECH_STACK.md` — 技术栈决策
- 功能需求描述或 FEATURE_SPEC.md
- UI 布局描述或线框图（可选）

### 输出
- `COMPONENT_TREE.md`：含组件层级图（mermaid）、组件职责表、路由映射表

### 规则
- 每个组件必须有：名称、职责一句话、Props（输入）、Events（输出）、父组件
- 页面级组件 vs 可复用组件的区分
- 使用 mermaid 流程图展示组件嵌套关系
- 路由页面必须映射到 URL path

### 依赖
- architecture/tech-stack-decider（需 TECH_STACK.md）

### 边界
- 不设计具体 UI 样式
- 不生成代码
- 不设计数据库
- 组件总数建议控制在 10-30 个（MVP 范围）

### 检查清单
- [ ] mermaid 图正确渲染组件嵌套
- [ ] 每个组件有 Props（in）和 Events（out）
- [ ] 路由表完整（path → page component）
- [ ] 可复用组件已标注
- [ ] 布局组件（Layout/Header/Sidebar）已包含
- [ ] 输出格式符合 COMPONENT_TREE.md 模板

### 产出物
- 文件路径: `{{module_dir}}/COMPONENT_TREE.md`
- 格式: Markdown，含 `## 组件层级图` `## 组件职责表` `## 路由映射` `## 数据流向`

---

## Prompt 模板

```text
你是一个资深前端架构师。请设计页面-组件层级树。

## 项目技术栈
{{TECH_STACK_CONTENT}}

## 功能需求
{{FEATURE_DESCRIPTION}}

## 任务
1. 列出所有页面（路由页面）
2. 为每个页面设计子组件层级
3. 抽取可复用组件
4. 定义每个组件的 Props（输入）和 Events（输出）
5. 设计路由映射

## 输出格式
```markdown
# 组件树 — {{PROJECT_NAME}}

## 组件层级图
` ` `mermaid
graph TD
  App --> Layout
  Layout --> Header
  Layout --> Sidebar
  Layout --> RouterView
  RouterView --> HomePage
  RouterView --> UserListPage
  UserListPage --> UserTable
  UserListPage --> SearchBar
  UserTable --> UserRow
  RouterView --> UserDetailPage
  UserDetailPage --> UserForm
` ` `

## 组件职责表
| 组件名 | 类型 | 职责 | Props (in) | Events (out) | 父组件 |
|--------|------|------|------------|--------------|--------|
| App | root | 应用根组件 | - | - | - |
| Layout | layout | 页面布局框架 | - | - | App |
| Header | shared | 顶部导航栏 | title:string | logout | Layout |
| Sidebar | shared | 侧边导航 | menuItems:MenuItem[] | navigate:path | Layout |
| HomePage | page | 首页仪表盘 | - | - | RouterView |
| UserListPage | page | 用户列表页 | - | - | RouterView |
| UserTable | component | 用户数据表格 | users:User[], loading:boolean | select:userId, sort:field | UserListPage |
| SearchBar | shared | 搜索输入框 | placeholder:string | search:query | UserListPage |
| UserDetailPage | page | 用户详情/编辑页 | - | - | RouterView |
| UserForm | component | 用户表单 | user?:User, loading:boolean | submit:UserData, cancel | UserDetailPage |

## 路由映射
| Path | Page Component | Auth Required | Lazy Load |
|------|---------------|---------------|-----------|
| / | HomePage | No | Yes |
| /users | UserListPage | Yes | Yes |
| /users/:id | UserDetailPage | Yes | Yes |

## 数据流向
- **用户列表**: UserListPage → API(/api/users) → Pinia store → UserTable(:users)
- **用户搜索**: SearchBar → emit(search) → UserListPage → API(/api/users?q=...) → store
- **用户详情**: UserDetailPage → API(/api/users/:id) → UserForm(:user)
```
```
<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->
<!-- Source: skill-registry -->
> **1.0** | active | architecture | synced 2026-06-18 10:54

<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->