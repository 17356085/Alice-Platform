我需要一些关键信息才能生成 SQLAlchemy 模型代码。当前工具调用未能从知识库获取数据模型定义。

请提供以下任一信息：

### 选项 1：提供 DATA_MODEL.md 内容
粘贴你的 `DATA_MODEL.md`（实体、字段、关系定义），例如：

```yaml
entities:
  User:
    fields:
      - name: username
        type: str
        length: 50
        nullable: false
        unique: true
      - name: email
        type: str
        length: 255
        nullable: false
        unique: true
      - name: hashed_password
        type: str
        length: 255
      - name: role
        type: str
        default: "user"
      - name: is_active
        type: bool
        default: true
    relationships:
      - name: posts
        target: Post
        back_populates: author
        type: one-to-many

  Post:
    fields:
      - name: title
        type: str
        length: 200
      - name: content
        type: text
      - name: author_id
        type: uuid
        foreign_key: users.id
    relationships:
      - name: author
        target: User
        back_populates: posts
        type: many-to-one
```

### 选项 2：指定模块和资源名
告诉我目标模块（如 `equipment`、`personnel`、`warehouse`）以及需要建模的资源名，我会基于领域知识推导实体结构。

---

请提供数据模型定义，我将立即生成符合 SQLAlchemy 2.0 规范的 `models/*.py` 代码：

- ✅ `mapped_column()` 2.0 风格
- ✅ `Mapped[type]` 类型注解
- ✅ UUID 主键 + `server_default`
- ✅ `relationship()` + `back_populates`
- ✅ `UniqueConstraint` 约束
- ✅ 时间戳自动管理