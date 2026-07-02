# Skill: component-design/layout-mockup

### 目标
生成 ASCII 布局稿，标注 flex/grid 结构、响应式断点，输出 LAYOUT_MOCKUP.md。

### 输入
- `COMPONENT_SPEC.md`
- 页面列表

### 输出
- `LAYOUT_MOCKUP.md`

### 规则
- 使用 ASCII box-drawing 表示布局结构
- 标注: desktop / tablet / mobile 断点
- 标注 flex 方向 / grid 列数

---

## Prompt 模板

```text
为以下页面生成布局稿。

## 页面: {{PAGE_NAME}}

## 输出
每个页面: ASCII 布局图 + flex/grid 标注 + 响应式断点。
```
<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->
<!-- Source: skill-registry -->
> **1.0** | active | component-design | synced 2026-06-18 10:54

<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->