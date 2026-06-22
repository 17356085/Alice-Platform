# Skill: component-design/data-flow

### 目标
设计组件间的数据流向：API → Store → Page → Component → Event → Store，生成 DATA_FLOW.md。

### 输入
- `COMPONENT_TREE.md`
- `PROPS_INTERFACE.yaml`
- `API_CONTRACTS.md`

### 输出
- `DATA_FLOW.md`：每个页面的数据获取→传递→事件回传链路

### 规则
- 单向数据流：Store → Page → Component(props)，Component → Page(emit) → Store(action)
- 标注异步边界

---

## Prompt 模板

```text
设计组件数据流向。

## 组件树 + Props
{{COMPONENT_TREE}}
{{PROPS_INTERFACE}}

## 输出
每个页面: API 调用 → Store 更新 → Props 传递 → Events 回传 的完整链路。
```
<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->
<!-- Source: skill-registry -->
> **1.0** | active | component-design | synced 2026-06-18 10:54

<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->