# Skill: component-design/props-interface

### 目标
从 COMPONENT_SPEC.md 提取 Props/Events 的 TypeScript 类型定义，输出 PROPS_INTERFACE.yaml。

### 输入
- `COMPONENT_SPEC.md`

### 输出
- `PROPS_INTERFACE.yaml`：每个组件的 Props/Events 类型

### 规则
- 每个 Prop: name, type, required?, default, description
- YAML 格式便于下游 Skill 消费（~200 tokens vs ~2000 tokens Markdown）

---

## Prompt 模板

```text
从组件规格提取 Props/Events 接口定义。

## 组件规格
{{COMPONENT_SPEC}}

## 输出
```yaml
components:
  UserTable:
    props:
      - name: users
        type: User[]
        required: true
        description: 用户数据列表
    events:
      - name: select
        payload: userId: string
```
```
<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->
<!-- Source: skill-registry -->
> **1.0** | active | component-design | synced 2026-06-18 10:54

<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->