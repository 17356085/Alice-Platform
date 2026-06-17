# Skill: page-analysis

## 目标
通过页面截图或 HTML 源码分析页面结构、元素清单和元素定位器。

## 输入
- 页面截图（1-3 张）或 HTML 源码
- 页面名称、URL、所属模块
- MODULE_CONTEXT.md

## 输出
- PAGE_CONTEXT.md — 页面元素清单（搜索区/表格/弹窗/权限点）
- PAGE_ELEMENT_POSITION.md — 元素定位器设计（A/B/C 三级）

## 规则
- 使用表格呈现元素清单
- 定位器优先级：A级（data-testid/id/name/placeholder）> B级（CSS Selector）> C级（XPath）
- Element Plus 组件需识别具体类型（el-input/el-select/el-table 等）
- 所有等待场景标注 WebDriverWait 策略

## 依赖
- templates/page-context.template.md
- templates/tech-analysis.template.md
- skills/module-modeling.md

## 边界
- 本 Skill 不产出风险模型（那是 risk-modeling 的职责）
- 本 Skill 不产出测试设计（那是 testcase-design 的职责）
- 定位器依赖实际 HTML 源码或可操作的页面

---

## Prompt 模板

> 以下 Prompt 可直接复制到 AI 对话中使用。替换 `{{ }}` 占位符即可。

### 基于截图分析页面

```text
你是一个Web端测试工程师，擅长通过截图分析页面结构。请分析以下页面截图。

## 页面信息
- 页面名称：{{设备报警配置}}
- 所属模块：{{设备管理}}
- 页面URL：{{http://8.136.215.171:8081/equipment/alarm-config}}

## 截图
{{上传截图}}

## 任务
请逐区域分析页面，输出 PAGE_CONTEXT.md：

1. **页面整体结构**：顶部/左侧/主内容区的布局描述
2. **搜索/筛选区**：
   - 每个输入控件的类型（input/select/date-picker）
   - 每个控件的标签文字
   - 按钮（搜索/重置/新增等）
3. **表格/列表区**：
   - 所有列标题
   - 每列的数据类型（文本/数字/日期/标签/操作按钮）
   - 操作列中的按钮（编辑/删除/详情等）
4. **分页区**：分页组件位置、每页条数选项
5. **弹窗/对话框**：
   - 弹窗标题
   - 弹窗内表单字段（标签+控件类型）
   - 弹窗按钮（确认/取消）
6. **页面状态**：加载中、空数据、错误状态的表现
7. **权限点**：哪些元素可能受权限控制

## 输出格式
使用表格呈现元素清单：
| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
```

### 基于 HTML 源码分析元素定位器（初版）

```text
你是一个Selenium自动化测试专家，擅长从HTML源码中提取稳定的元素定位器。
被测系统是 Vue 3 + Element Plus。

## HTML源码
```html
{{粘贴页面关键区域的HTML源码}}
```

## 已识别的页面元素（来自 PAGE_CONTEXT.md）
{{粘贴 PAGE_CONTEXT.md 中的元素清单}}

## 任务
为每个元素设计定位器，按优先级输出：

1. **A级定位器**（优先使用）：
   - `data-testid` 属性
   - 稳定的 `id` 属性
   - 唯一的 `name` 属性
   - 唯一的 `placeholder` 文本

2. **B级定位器**（A级不可用时使用）：
   - 稳定的 CSS Selector（基于类名组合）
   - 注意：Element Plus 的 class 名称可能随版本变化

3. **C级定位器**（保底方案）：
   - XPath（相对路径，避免绝对路径）
   - 使用 `contains()` 处理动态 class
   - 使用 `text()` 匹配按钮文字

## 特别注意
- Element Plus 组件的动态 class（如 el-xxx--active）
- Vue 的 v-if 导致元素可能不在 DOM 中
- 表格行的动态索引问题
- 下拉框选项的动态渲染

## 输出格式
| 元素ID | 定位策略 | 定位值 | 稳定性评级 | 备用方案 |
```

> **注意**：完整的技术实现分析（含定位器设计表 + Vue 异步等待策略）建议使用 `skills/tech-analysis.md`。

---

## 检查清单

- [ ] 页面整体结构描述清晰（顶部/左侧/主内容区）
- [ ] 搜索区每个控件有：标签名 + 控件类型 + 定位思路
- [ ] 表格所有列标题已列出，操作列按钮已识别
- [ ] 所有弹窗/对话框已列出（标题 + 字段 + 按钮）
- [ ] 页面特殊状态已标注（加载中/空数据/错误）
- [ ] 权限敏感元素已标注
- [ ] 元素定位器至少覆盖 A/B 两级
- [ ] 输出使用表格格式（元素ID/描述/类型/区域/备注）

---

## 产出物
→ `PAGE_CONTEXT.md` + `PAGE_ELEMENT_POSITION.md`，存放至对应页面目录。
→ 输出格式参见 `templates/page-context.template.md`。

---

## 附: PAGE_INTERFACE.yaml 自动生成 (P1-2 合并自 page-interface-generator)

> P1-2 (2026-06-13): `page-interface-generator` Skill 已合并为本 Skill 的自动后处理步骤。
> 不再作为独立 Skill 暴露——page-analysis 完成后自动执行。

### 目的
automation-agent 优先消费 PAGE_INTERFACE.yaml（~200 tokens）而非通读 PAGE_CONTEXT.md（~2000+ tokens）。
每个页面节省 ~1800 tokens。

### 执行方式
page-analysis 完成后自动调用:
```bash
python tools/generate_page_interface.py --module {{module}} --page {{page}}
```
此工具读取 PAGE_CONTEXT.md + TEST_CASES.md，通过 LLM 提取结构化元素信息，生成 PAGE_INTERFACE.yaml。

### 产出物
→ `PAGE_INTERFACE.yaml`，存放至对应页面目录。
<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->
<!-- Source: skill-registry -->
> **1.1** | active | test-design | synced 2026-06-17 16:53

<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->