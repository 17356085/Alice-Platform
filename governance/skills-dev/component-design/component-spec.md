# Skill: component-design/component-spec

### 目标
为每个组件生成 COMPONENT_SPEC.md：职责、状态（loading/empty/error/disabled）、插槽、视觉变体。

### 输入
- `COMPONENT_TREE.md`
- UI 组件库参考

### 输出
- `COMPONENT_SPEC.md`

### 规则
- 必须列: loading, empty, error, disabled, hover, focus 6 种状态
- 插槽标注: 名称、位置、默认内容

---

## Prompt 模板

```text
你是资深 UI 架构师。为以下组件生成规格文档。

## 组件树
{{COMPONENT_TREE}}

## 输出
每个组件: 名称 / 职责 / Props / Events / 状态(6种) / 插槽
```
<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->
<!-- Source: skill-registry -->
> **1.0** | active | component-design | synced 2026-06-18 10:54

<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->