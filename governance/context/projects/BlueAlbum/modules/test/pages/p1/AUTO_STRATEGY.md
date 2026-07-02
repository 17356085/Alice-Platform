---
source: ai
source_agent: auto-strategy-skill
created: 2026-06-18
module: test
page: p1
status: draft
note: 缺少 TEST_CASES.md 及完整 TECH_ANALYSIS.md，策略待补充
---

# AUTO_STRATEGY.md — 自动化覆盖策略

> **模块**: test  
> **页面**: p1  
> **责任人**: 待定  
> **版本**: 0.1

## 1. 自动化覆盖矩阵
> 待输入：请提供 `TEST_CASES.md` 中的用例编号、标题和优先级。  
> 以下为模板示例，实际内容需按用例填充。

| 用例编号 | 标题 | 优先级 | 是否自动化 | 理由 |
|----------|------|--------|------------|------|
| TC-001 | 页面正常加载 | P0 | ✅ | 基础冒烟，推荐使用稳定定位器 |
| TC-002 | 搜索功能正常 | P0 | ✅ | 核心业务，重复执行高频 |
| TC-003 | 空状态展示 | P1 | ✅ | 回归价值高，定位器简单 |
| TC-004 | 错误提示验证 | P2 | ❌ | 需要人工判断文案准确性 |
| TC-xxx | …… | …… | …… | …… |

**风险标注**：若 TECH_ANALYSIS 中定位器稳定性为 C（动态哈希类），则在“理由”中增加 ⚠️ **高风险** 标记。

## 2. PageObject 拆分方案
> 假设该页面基于 Element Plus 标准组件（el-table、el-dialog 等）。

### 建议的 Page 类

| Page 类名 | 职责 | 关键元素 |
|-----------|------|---------|
| **P1Page** | 主页面操作：搜索、表格操作、分页 | 搜索框、el-table、分页器 |
| **P1DetailDialog** | 弹窗/抽屉内的表单 CRUD | el-dialog 内表单、按钮 |

> 若页面存在复杂弹窗（如多步骤向导），建议拆分为独立类，避免 APage 将变得过于庞大。

**继承关系**：
```python
from common.page_objects.base_page import BasePage

class P1Page(BasePage):
    pass
```

## 3. 公共组件复用分析

| 操作类型 | 可复用能力 | 备注 |
|----------|------------|------|
| 表格等待 | `BasePage.wait_for_table()` | 已封装 stale 检测 |
| 分页翻页 | `BasePage.go_to_page(n)` | 需要根据当前页面适配 |
| 选择下拉 | `ElementPlusHelper.select_by_text()` | 支持 el-select 远程搜索 |
| 确认弹窗 | `ElementPlusHelper.confirm_dialog()` | 处理 `el-message-box` |
| 文件上传 | `ElementPlusHelper.upload_file()` | 若涉及 el-upload |
| 树形控件 | 建议新建 `ElementPlusHelper.expand_tree_node()` | 视页面是否包含 el-tree 而定 |

**是否需要扩展 ElementPlusHelper？**  
- [ ] 需要 → 如果页面包含特殊组件（如虚拟滚动、自定义指令），需评估是否加入公共方法。  
- [x] 暂时不需要 → 目前分析尚未发现超出已有能力的组件。

## 4. 等待策略建议
> 待输入：需要从 TECH_ANALYSIS 获取具体的异步行为。以下为通用策略。

| 场景 | 等待条件 | 建议封装 |
|------|---------|---------|
| 页面初始化 | `el-table` 首次渲染 | `wait.until(EC.presence_of_element_located(...))` |
| 搜索后刷新 | 加载遮罩消失（`.el-loading-mask`） | `BasePage.wait_for_loading()` |
| 弹窗打开 | 弹窗容器可见（`.el-dialog` visible） | `ElementPlusHelper.wait_dialog_open()` |
| 弹窗关闭 | 弹窗不可见 | `ElementPlusHelper.wait_dialog_close()` |
| 下拉列表加载 | 选项数量大于0 | 自定义 `lambda d: len(d.find_elements(...)) > 0` |

**页面特有风险**：  
- 若存在 iframe，需要先 `driver.switch_to.frame(...)`，并在操作后返回默认上下文。  
- 动态渲染表格列可能导致定位器不稳定，建议使用文本内容而非下标。

## 5. ROI 分析
> 待输入：请提供手工执行时间和预估开发/维护成本。

| 项目 | 估算值 | 备注 |
|------|--------|------|
| **手工执行时间** | 未提供 (minutes) | 每次回归所需人工操作时间 |
| **预计执行频率** | 未提供 (次/月) | 根据发布节奏估算 |
| **开发成本** | 未提供 (小时) | 依据 Page 类数量与复杂度 |
| **月维护成本** | 未提供 (小时) | 元素变更、用例增加等 |
| **ROI 公式** | (手工时间 × 频率 - 开发成本 - 维护成本 × 月数) | 正值为节省工时 |

**决策建议**：
- 若 P0 用例长期手工执行次数 > 5 次/月，自动化通常可快速回本。  
- 若页面频繁改版，维护成本可能超过手工执行成本，需谨慎评估。

## 6. 下一步行动
1. **补充输入**：提供 `TEST_CASES.md` 和完整 DOM 分析。  
2. **更新覆盖矩阵**：逐一标注所有用例的自动化取舍。  
3. **确认 PageObject 拆分**：与开发 / QA 评审后再进行编码。  
4. **实施**：进入 `code-generation` 技能，产出自动化脚本。

> ⚠️ 本策略为初始版本，所有 `❌ 未提供` 项需在获得完整需求后重新评估。