# Skill: tech-analysis

## 目标
从页面 HTML 源码和截图中分析前端技术实现，设计元素定位器和异步等待策略。

## 输入
- 页面 HTML 源码（浏览器 F12）
- 页面截图
- PAGE_CONTEXT.md
- 已知技术栈（Vue 3 + Element Plus + Selenium）

## 输出
- TECH_ANALYSIS.md — 组件识别、DOM 结构分析、定位器设计表、等待策略
- PAGE_ELEMENT_POSITION.md（可合并输出）

## 规则
- 先识别 Element Plus 组件类型，再设计定位器
- 定位器分三级：A级（稳定属性）、B级（CSS Selector）、C级（XPath/动态 class）
- 每个定位器标注稳定性评级
- 异步等待策略需覆盖：页面加载、表格刷新、弹窗打开/关闭、loading 消失
- Vue 动态 class 和 v-if 控制元素需特殊说明

## 依赖
- skills/page-analysis.md
- templates/tech-analysis.template.md

## 边界
- 本 Skill 不涉及测试用例设计
- 定位器依赖真实可操作的页面 HTML
- 本 Skill 不产出自动化代码（那是 code-generation 的职责）

---

## Prompt 模板

> 以下 Prompt 可直接复制到 AI 对话中使用。替换 `{{ }}` 占位符即可。

### Element Plus 组件识别与定位器设计

```text
你是Vue3 + Element Plus自动化测试专家。请分析以下页面HTML，输出技术实现分析。

## HTML源码
```html
{{粘贴页面HTML}}
```

## 已知框架
- 前端：Vue 3 + Element Plus
- 测试框架：Selenium 4.15.2 + pytest 7.4.4
- BasePage 已封装：wait_table_loaded / wait_dialog_visible / wait_loading_disappear / click_element / input_text
- ElementPlusHelper 已封装：select_option / get_select_value / get_table_data / get_pagination_info

## 任务
输出 TECH_ANALYSIS.md：

### 1. Element Plus 组件识别
识别并列出所有 Element Plus 组件及其用途：
- el-input、el-select、el-date-picker
- el-table、el-table-column
- el-dialog、el-drawer
- el-tree、el-upload
- el-pagination、el-button
- el-tag、el-switch、el-checkbox、el-radio

### 2. DOM 结构分析
- 关键节点的层级结构
- 稳定属性（id/name/data-*）
- 动态属性（Vue生成的哈希class、v-if控制的元素）

### 3. 定位器设计表（A/B/C 三级）
| 元素 | 推荐定位策略 | 定位值 | 稳定性 | 备注 |
|------|-------------|--------|--------|------|
| 搜索输入框 | CSS | `.search-area input[placeholder*='{{关键词}}']` | A | |
| 搜索按钮 | XPATH | `//button[.//span[text()='搜索']]` | A | |
| 表格容器 | CSS | `.el-table` | A | |
| 表格行 | CSS | `.el-table__body-wrapper .el-table__row` | B | 动态行 |
| 新增按钮 | XPATH | `//button[.//span[text()='新增']]` | A | |
| 弹窗 | CSS | `.el-dialog` | A | |
| 弹窗确认 | XPATH | `//div[contains(@class,'el-dialog')]//button[.//span[text()='确定']]` | A | |
| 分页器 | CSS | `.el-pagination` | A | |

### 4. Vue 异步等待策略
| 场景 | 等待条件 | WebDriverWait 示例 |
|------|---------|-------------------|
| 页面加载 | 表格出现 | `wait.until(EC.presence_of_element_located(TABLE))` |
| 搜索完成 | loading消失 | `wait.until(EC.invisibility_of_element_located(LOADING))` |
| 弹窗打开 | 弹窗可见 | `wait.until(EC.visibility_of_element_located(DIALOG))` |
| 弹窗关闭 | 弹窗不可见 | `wait.until(EC.invisibility_of_element_located(DIALOG))` |
| 表格刷新 | 行数变化 | 自定义等待逻辑 |

### 5. 自动化风险点
- 动态ID/Class
- iframe嵌套
- 虚拟列表/懒加载
- 权限控制导致的元素缺失
- Element Plus 下拉选项渲染在 body 层
```

### 疑难定位器单独分析（按需，可调用 element-plus-locator Skill）

```text
我在定位以下 Element Plus 组件时遇到困难，请帮我设计定位策略。

## 问题组件
```html
{{粘贴具体的HTML片段}}
```

## 已尝试的定位方式
1. {{CSS Selector 尝试}} → 失败原因：{{动态class}}
2. {{XPath 尝试}} → 失败原因：{{元素未找到}}

## 组件特征
- 组件类型：{{el-select 远程搜索下拉框 / el-date-picker 日期范围 / el-cascader 级联选择器}}
- 特殊行为：{{下拉选项动态加载 / 选项在 body 层 / 需要先触发才渲染}}

## 任务
1. 分析为什么现有定位方式失败
2. 给出 2-3 种替代定位策略（从A级到C级）
3. 给出完整的等待+操作代码
4. 建议是否需要扩展 ElementPlusHelper
```

---

## 检查清单

- [ ] 所有 Element Plus 组件已识别（至少覆盖 el-input/select/date-picker/table/dialog/pagination/button）
- [ ] 每个元素有 A/B/C 三级定位策略（A 级优先，C 级保底）
- [ ] 每个定位器标注稳定性评级（A=生产稳定 / B=可能波动 / C=脆弱）
- [ ] 动态 class 和 v-if 控制元素有特殊说明
- [ ] 5 种异步等待场景已覆盖：页面加载/表格刷新/弹窗打开/弹窗关闭/loading 消失
- [ ] 自动化风险点已标注（动态ID、iframe、虚拟列表等）
- [ ] 定位器值来源真实 HTML，不编造
- [ ] 输出同时可作为 PAGE_ELEMENT_POSITION.md 使用

---

## 产出物
→ `TECH_ANALYSIS.md` + `PAGE_ELEMENT_POSITION.md`，存放至对应页面目录。
→ 输出格式参见 `templates/tech-analysis.template.md`。
<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->
<!-- Source: skill-registry -->
> **1.0** | active | automation | synced 2026-06-17 21:52

<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->