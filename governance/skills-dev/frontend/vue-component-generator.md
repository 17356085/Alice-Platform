# Skill: frontend/vue-component-generator

### 目标
从 PROPS_INTERFACE.yaml + COMPONENT_SPEC.md 生成 Vue 3 SFC 组件代码（`<script setup lang="ts">` + `<template>` + `<style scoped>`）。

### 输入
- `PROPS_INTERFACE.yaml` — 组件的 Props/Events 接口定义
- `COMPONENT_SPEC.md` — 组件的状态和行为规范
- `COMPONENT_TREE.md` — 父组件的上下文
- Element Plus 组件库文档参考（如适用）

### 输出
- `*.vue` 文件（Vue 3 SFC），包含三部分：
  - `<script setup lang="ts">` — Props、Emits、逻辑
  - `<template>` — 模板（使用 Element Plus 组件）
  - `<style scoped>` — 局部样式

### 规则
- 必须使用 `<script setup lang="ts">`（Composition API），禁用 Options API
- `defineProps<T>()` 带 TypeScript 类型，禁止 `any`
- `defineEmits<T>()` 带类型
- 模板中必须处理 4 种状态：loading、empty、error、正常数据
- 样式使用 `<style scoped>`，不污染全局
- Element Plus 组件优先（el-table、el-form、el-dialog、el-button 等）
- 禁止 `console.log` 在生产代码中
- 生成后必须执行 ESLint + tsc --noEmit 自检

### 依赖
- architecture/component-tree-designer（COMPONENT_SPEC.md、PROPS_INTERFACE.yaml）

### 边界
- 不调用后端 API（那是 page-implementer 的职责）
- 不设置路由
- 不管理全局状态（store 是独立 skill）
- Props down, Events up — 不直接修改父组件状态

### 检查清单
- [ ] `<script setup lang="ts">` 而非 Options API
- [ ] Props 类型完整，无 `any`
- [ ] 模板处理 loading / empty / error / 正常 四种状态
- [ ] `<style scoped>` 存在
- [ ] 无 console.log
- [ ] Element Plus 组件正确导入和使用
- [ ] ESLint 通过
- [ ] TypeScript 编译通过

### 产出物
- 文件路径: `src/components/{{ComponentName}}.vue`
- 格式: Vue 3 SFC

---

## Prompt 模板

```text
你是一个资深 Vue 3 + TypeScript 前端开发专家。请从组件接口定义生成完整的 Vue 3 SFC。

## 组件接口
```yaml
{{PROPS_INTERFACE_YAML}}
```

## 组件规格
{{COMPONENT_SPEC_CONTENT}}

## 规则（严格执行）
1. 使用 `<script setup lang="ts">`
2. `defineProps<T>()` — Props 类型完整，禁止 any
3. `defineEmits<T>()` — Events 类型完整
4. 模板必须处理 4 种状态：
   - `v-if="loading"` → `<el-skeleton />`
   - `v-else-if="error"` → `<el-result icon="error" />`
   - `v-else-if="!data.length"` → `<el-empty />`
   - `v-else` → 正常渲染
5. 样式 `<style scoped>`，使用 Element Plus CSS 变量
6. 禁止 console.log
7. 通过 ESLint + TypeScript 编译

## 生成后自检
```bash
# 在你的代码生成完成后，运行以下命令验证：
npx eslint {{ComponentName}}.vue --fix
npx vue-tsc --noEmit
```

## 输出
只输出完整的 .vue 文件内容，包裹在 ```vue 代码块中。
```
<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->
<!-- Source: skill-registry -->
> **1.0** | active | frontend | synced 2026-06-17 21:52

<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->