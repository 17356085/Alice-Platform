# Phase C 实战验证报告

> 验证日期：2026-06-11 | 验证模块：储罐管理（tank）| 使用 Skill：module-modeling → page-analysis

---

## 验证目标

用刚填充的 10 个核心 Skill，对一个零上下文模块执行完整的 `module-onboarding` Workflow 前半段（Phase 0 → Phase 0.5 → Phase 1），验证：

1. Skill 中的 Prompt 是否可直接使用
2. 产出质量是否符合预期
3. 流程中是否存在断点

---

## 验证过程

### Step 1：模块侦察（5 分钟）

从代码工程中提取 tank 模块信息：
- `sidebar_navigator.py` → 2 个路由：`#/tank/monitor`、`#/tank/report`
- `script/tank/conftest.py` → 路由配置已就绪，Page Object 和测试脚本均为空
- `page/tank_page/__init__.py` → 仅注释，无实现
- `PROJECT_KNOWLEDGE.md` → 储罐监控 15 条用例已完成（小程序端），Web 端未覆盖
- 旧 `contexts/储罐管理/` → 目录存在但为空

### Step 2：module-modeling（10 分钟）

使用 `skills/module-modeling.md` 的 Prompt 模板，填入：
- 模块名称：储罐管理
- 入口路由：从 sidebar_navigator 提取
- 参考：PROJECT_KNOWLEDGE.md 中的模块树

**产出**：`modules/tank/MODULE_CONTEXT.md`
- ✅ 模块定位清晰
- ✅ 页面清单完整（2 个页面，均已标注 ⏳）
- ✅ 风险点标注了 P0/P1/P2
- ✅ 与 equipment 模块的边界区分明确
- ⚠️ 数据对象部分依赖推理（实际页面未访问）

### Step 3：page-analysis × 2（15 分钟）

使用 `skills/page-analysis.md` 的 Prompt 模板，分别为两个页面产出 PAGE_CONTEXT。

**产出 1**：`modules/tank/pages/monitor/PAGE_CONTEXT.md`
- ✅ 推断结构合理（指标卡区 + 储罐列表区 + 详情弹窗）
- ⚠️ 所有元素标注"待实际页面确认"——无法从代码推理具体 DOM 结构

**产出 2**：`modules/tank/pages/report/PAGE_CONTEXT.md`
- ✅ 推断结构合理（日期选择区 + 汇总指标 + 表格区）
- ⚠️ 同上，缺少截图/HTML 导致元素清单无法精确

### Step 4：索引更新（2 分钟）

- ✅ `MODULE_INDEX.md` 新增 tank 行
- ✅ `project-index.yaml` 新增 tank 到 current_modules

### Step 5：风险建模（跳过）

`risk-modeling` Skill 的 Prompt 需要 PAGE_CONTEXT 中有精确的元素清单。当前两个 PAGE_CONTEXT 均为推理骨架，强行做风险建模会产生大量虚假风险。

**结论**：Phase 1.5（risk-modeling）依赖 Phase 1（page-analysis）产出完整度 ≥ 80%。骨架级 PAGE_CONTEXT 不能直接进入 risk-modeling。

---

## 发现的问题（断点与改进项）

### 🔴 断点 1：page-analysis 依赖浏览器访问

**问题**：模块建模可以从代码推断，但 page-analysis 的 Prompt 模板假设有截图或 HTML。当 AI 无法访问浏览器时（无截图、无 HTML），产出只能是推理骨架，无法进行后续 Phase。

**建议**：
- 在 `page-analysis` Skill 中增加 **"无截图模式"** — 基于项目已有文档和代码推断页面结构
- 或者在 Workflow 中增加前置检查：是否有截图？无 → 提示用户提供或跳过

### 🔴 断点 2：risk-modeling 依赖 PAGE_CONTEXT 完整度

**问题**：骨架级 PAGE_CONTEXT（元素全部标注"待确认"）无法支持 6 维度风险建模。强行执行会产生大量低质量风险。

**建议**：
- 在 `risk-modeling` Skill 的 Prompt 中增加前置校验：PAGE_CONTEXT 中元素清单完整度 < 60%？→ 提示先完成页面分析
- 在 `module-onboarding` Workflow 中，Phase 1 和 Phase 1.5 之间增加完整度检查门禁

### 🟡 断点 3：Skill Prompt 中占位符的默认值

**问题**：Skill Prompt 模板使用 `{{设备报警配置}}` 等示例值作为占位符，新 AI 可能直接使用示例值而不替换。

**建议**：在 Prompt 模板前增加明确的"使用前替换所有 `{{ }}`"的提示（已有，但可加粗强调）。

### 🟡 断点 4：MODULE_CONTEXT 缺少"数据来源标注"

**问题**：当前 PAGE_CONTEXT 模板的"元素清单"都来自推理，但没有标注每个元素的推理来源（来自代码/来自截图/来自推理）。

**建议**：在模板中增加"数据来源"列（代码分析/截图分析/逻辑推理/待确认）。

---

## 本次产出

| 文件 | 路径 | 状态 |
|------|------|------|
| MODULE_CONTEXT.md | `governance/context/projects/web-automation/modules/tank/` | ✅ 已产出 |
| PAGE_CONTEXT.md (monitor) | `.../tank/pages/monitor/` | ⚠️ 推理骨架 |
| PAGE_CONTEXT.md (report) | `.../tank/pages/report/` | ⚠️ 推理骨架 |
| MODULE_INDEX.md | 更新 | ✅ 已注册 tank |
| project-index.yaml | 更新 | ✅ 已注册 tank |

---

## 结论

**Workflow 前半段（Phase 0.5 → Phase 1）可在无浏览器访问的条件下产出骨架级文档**。但 Phase 1.5 以后的所有阶段（风险建模 → 测试设计 → 技术分析 → 代码生成）依赖实际的页面访问。

**最大收益的下一步**：用一次浏览器访问获取 tank 两个页面的截图和 HTML，即可将骨架升级为完整文档，然后一次性走通 Phase 1.5 → Phase 4。

**Skill 改进项**：4 个断点中，断点1和断点2需要在对应 Skill 中增加"降级模式"或"前置校验"。
