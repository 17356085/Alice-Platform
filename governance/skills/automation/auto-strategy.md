# Skill: auto-strategy

## 目标
从测试用例和技术分析出发，制定自动化覆盖策略、PageObject 拆分方案和 ROI 分析。

## 输入
- TEST_CASES.md
- TECH_ANALYSIS.md
- 已有 BasePage 能力清单
- 自动化架构文档

## 输出
- AUTO_STRATEGY.md

## 规则
- P0 用例必须自动化
- 定位器不稳定的用例标注风险
- 一次性操作（仅上线前执行）不建议自动化
- PageObject 拆分遵循：一个页面一个 Page 类，复杂弹窗独立
- 必须给出 ROI 计算（开发成本 vs 执行频率 vs 维护成本）

## 依赖
- templates/auto-strategy.template.md
- skills/tech-analysis.md
- skills/testcase-design.md

## 边界
- 本 Skill 不产出自动化代码（那是 code-generation 的职责）
- 不评估已有自动化用例的稳定性（那是 bug-analysis 的职责）

---

## Prompt 模板

> 以下 Prompt 可直接复制到 AI 对话中使用。替换 `{{ }}` 占位符即可。

### 自动化覆盖策略设计

```text
基于以下测试用例和技术分析，制定自动化测试策略。

## 输入
- TEST_CASES：{{粘贴 TEST_CASES 用例编号和标题}}
- TECH_ANALYSIS：{{粘贴 TECH_ANALYSIS 定位器设计表}}
- 已有 BasePage 能力：{{粘贴 AUTOMATION_ARCHITECTURE.md 中 BasePage 能力描述}}

## 任务
输出 AUTO_STRATEGY.md：

### 1. 自动化覆盖矩阵
| 用例编号 | 标题 | 优先级 | 是否自动化 | 理由 |
|---------|------|--------|----------|------|
| TC-001 | 页面正常加载 | P0 | ✅ | 基础冒烟，定位器稳定 |
| TC-xxx | ... | P2 | ❌ | 需要人工判断UI美观度 |

### 2. PageObject 拆分方案
```
建议的 Page 类及职责：
- {{AlarmConfigPage}}：报警配置页的搜索/表格/分页操作
- {{AlarmConfigDialog}}：报警配置弹窗的CRUD操作
```

### 3. 公共组件复用分析
- 哪些操作可以复用 BasePage 已有方法
- 是否需要扩展 ElementPlusHelper

### 4. 等待策略建议
- 该页面特有的异步行为
- 建议的等待封装

### 5. ROI 分析
- 预估开发时间：{{X}} 小时
- 预估维护成本：{{Y}} 小时/月
- 手工执行时间：{{Z}} 分钟/次
- ROI = {{Z × 执行频率 - X - Y × 月数}}

## 注意
- P0 用例必须自动化
- 定位器不稳定的用例标注风险
- 一次性操作（如仅上线前执行）不自动化
- PageObject 拆分遵循：一个页面一个 Page 类，复杂弹窗独立
```

---

## 检查清单

- [ ] 覆盖矩阵：每个 P0 用例标注 ✅ 自动化
- [ ] 覆盖矩阵：每个非自动化用例有明确的"不建议自动化理由"
- [ ] PageObject 拆分方案：一个页面一个 Page 类，复杂弹窗独立类
- [ ] 公共组件复用分析：标注哪些可复用 BasePage/ElementPlusHelper
- [ ] 等待策略：标注页面特有的异步行为
- [ ] ROI 计算完整：开发时间 + 维护成本 + 手工执行时间
- [ ] 定位器不稳定的用例标注了风险

---

## 产出物
→ `AUTO_STRATEGY.md`，存放至对应页面目录。
→ 输出格式参见 `templates/auto-strategy.template.md`。
<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->
<!-- Source: skill-registry -->
> **1.0** | active | automation | synced 2026-06-17 16:53

<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->