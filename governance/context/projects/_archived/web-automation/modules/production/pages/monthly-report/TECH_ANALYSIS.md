# TECH_ANALYSIS — production / monthly-report

## 1. 技术栈确认
| 维度 | 结论 | 说明 |
|------|------|------|
| UI 框架 | Element Plus + 自定义组件 | el-table/el-button/el-card + 自定义 month-nav |
| 月份选择器 | **自定义** month-nav | 非 el-date-picker，用 el-button.is-circle + span.current-month |
| 表格 | el-table (striped+border) | 4 区独立表格，无分页 |
| 页面容器 | monthly-report-container | 自定义 class |

## 2. 定位器设计

### 月份导航
| 元素 | 定位 | 评级 |
|------|------|:--:|
| 上一月 ← | CSS `.month-nav button.el-button.is-circle:first-child` | A |
| 当前月份 | CSS `.current-month` | A |
| 下一月 → | CSS `.month-nav button.el-button.is-circle:last-child` | A |

### 按钮
| 按钮 | 定位 | 评级 |
|------|------|:--:|
| 生成报表 | XPATH `//button[contains(.,"生成报表")]` | C |
| 趋势 | XPATH `//button[contains(.,"趋势")]` | C |
| 导出 | XPATH `//button[contains(.,"导出")]` | C |
| 打印 | XPATH `//button[contains(.,"打印")]` | C |

### 统计卡片
| 元素 | 定位 | 备注 |
|------|------|------|
| LNG月产量 | XPATH `//*[contains(.,"LNG月产量")]/following-sibling::*` | 数值在label后 |
| 液氮月产量 | 同上 | |
| 脱碳气月产量 | 同上 | |

### 分区表格
- 复用 daily-report 的分区卡片定位方式（`//*[contains(@class,"section-title") and contains(.,"{name}")]/ancestor::div[contains(@class,"el-card")]`）
- 列结构差异：产品表7列（含备注），其余表6列

## 3. Element Plus 坑位影响
- EP-001 (Teleport): 弹窗下拉选项 ✅ 需注意
- EP-010 (动画): 月份切换后表格刷新动画 ✅ 需注意
- 其他坑位影响同 daily-report

## 4. 自动化可行性
| 功能 | 可行性 | 置信度 |
|------|:------:|:------:|
| 页面加载 | ✅ | 高 |
| 月份导航 | ✅ | 高 |
| 生成报表 | ✅ | 高 |
| 趋势弹窗 | ✅ | 高 |
| 导出弹窗 | ⚠️ | 中（同 daily-report） |
| 打印 | ❌ | — |
