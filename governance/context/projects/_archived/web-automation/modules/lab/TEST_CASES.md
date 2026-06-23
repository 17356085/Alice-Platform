# TEST_CASES — lab（化验室取样，6页面，31条用例）

> 2026-06-12 | 32P/0F 全量回归

## gas-analysis-report（气体分析报告单）— 10 cases

| ID | 用例 | 类型 | 结果 |
|:---|------|:---:|:---:|
| GAS-01 | 正常显示气体分析报告单列表及相关字段 | smoke | ✅ |
| GAS-02 | 确认页面默认激活位置 | smoke | ✅ |
| GAS-03 | 表格有数据或显示空状态 | smoke | ✅ |
| GAS-04 | 日期范围查询功能 | functional | ✅ |
| GAS-05 | 重置按钮清空筛选条件 | functional | ✅ |
| GAS-06 | 切换取样位置标签 → 数据正常加载 | functional | ✅ |
| GAS-07 | 切换回默认位置 → 数据恢复 | functional | ✅ |
| GAS-08 | 新增报告单（必填：检验员+复核员） | functional | ✅ |
| GAS-09 | 统计行显示（平均值） | functional | ✅ |
| GAS-10 | 导出报告单 | functional | ✅ |

## gas-compare（气体分析对比）— 4 cases

| ID | 用例 | 类型 | 结果 |
|:---|------|:---:|:---:|
| GC-01 | 页面加载（含日期选择器） | smoke | ✅ |
| GC-02 | 日期范围查询 → 页面正常响应 | functional | ✅ |
| GC-03 | 双位置对比查询 | functional | ✅ |
| GC-04 | 同位置选择守卫 | boundary | ✅ |

## gas-indicator（气体分析设计指标）— 4 cases

| ID | 用例 | 类型 | 结果 |
|:---|------|:---:|:---:|
| GI-01 | 正常显示指标列表（8列） | smoke | ✅ |
| GI-02 | 指标名称列数据可读 | functional | ✅ |
| GI-03 | 页面加载验证 | smoke | ✅ |
| GI-04 | 行数验证（23行） | functional | ✅ |

## water-report（水质分析报告单）— 5 cases

| ID | 用例 | 类型 | 结果 |
|:---|------|:---:|:---:|
| WR-01 | 页面正常加载 | smoke | ✅ |
| WR-02 | 新增按钮可见 | smoke | ✅ |
| WR-03 | 切换取样位置 | functional | ✅ |
| WR-04 | 日期范围搜索 | functional | ✅ |
| WR-05 | 新增弹窗可打开 | functional | ✅ |

## water-compare（水质分析对比）— 4 cases

| ID | 用例 | 类型 | 结果 |
|:---|------|:---:|:---:|
| WC-01 | 页面加载（含日期选择器） | smoke | ✅ |
| WC-02 | 日期范围查询 | functional | ✅ |
| WC-03 | 双位置对比查询 | functional | ✅ |
| WC-04 | 同位置选择守卫 | boundary | ✅ |

## water-indicator（水质分析设计指标）— 4 cases

| ID | 用例 | 类型 | 结果 |
|:---|------|:---:|:---:|
| WI-01 | 正常显示指标列表（8列） | smoke | ✅ |
| WI-02 | 指标名称列数据可读 | functional | ✅ |
| WI-03 | 页面加载验证 | smoke | ✅ |
| WI-04 | 行数验证（22行） | functional | ✅ |

## 汇总

| 页面 | Smoke | Functional | Boundary | 总计 |
|------|:---:|:---:|:---:|:---:|
| gas-analysis-report | 2 | 8 | 0 | 10 |
| gas-compare | 1 | 2 | 1 | 4 |
| gas-indicator | 2 | 2 | 0 | 4 |
| water-report | 2 | 3 | 0 | 5 |
| water-compare | 1 | 2 | 1 | 4 |
| water-indicator | 2 | 2 | 0 | 4 |
| **合计** | **10** | **19** | **2** | **31** |
