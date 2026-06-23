# PAGE_ELEMENT_POSITION — lab / water-report

> Phase 1 | 2026-06-12 | A级=稳定属性 B级=CSS C级=XPath保底

## 搜索/筛选区
| 元素 | 策略 | 定位值 | 等级 |
|------|------|--------|:--:|
| 开始日期 | CSS | input[placeholder*="开始日期"] | A |
| 结束日期 | CSS | input[placeholder*="结束日期"] | A |
| 查询按钮 | XPATH | //button[contains(.,"查询")] | A |
| 重置按钮 | XPATH | //button[contains(.,"重置")] | A |

## 工具栏
| 元素 | 策略 | 定位值 | 等级 |
|------|------|--------|:--:|
| 新增按钮 | XPATH | //button[contains(.,"新增")] | A |
| 导出按钮 | XPATH | //button[contains(.,"导出")] | A |

## 取样位置标签栏
| 元素 | 策略 | 定位值 | 等级 |
|------|------|--------|:--:|
| 取样位置Tab | XPATH | //*[contains(normalize-space(.),"{text}") and not(ancestor::table)] | B |
| 当前选中 | CSS | [class*="tab"][class*="active"] | B |

## 数据表格（自定义 report-table）
| 元素 | 策略 | 定位值 | 等级 |
|------|------|--------|:--:|
| 表头 | CSS | thead tr:last-child th | A |
| 数据行 | CSS | tbody tr:not([class*=average]):not([class*=summary]) | B |
| 空数据 | CSS | [class*=empty] | B |

## 新增报告单弹窗（标准 el-dialog）
| 元素 | 策略 | 定位值 | 等级 |
|------|------|--------|:--:|
| 弹窗 | CSS | .el-dialog:not([style*="display:none"]) | A |
| 检验员 | XPATH | //input[@placeholder="请输入检验员"] | A |
| 复核员 | XPATH | //input[@placeholder="请输入复核员"] | A |
| 保存 | CSS | .el-dialog .el-button--primary | A |
| 取消 | XPATH | //button[contains(.,"取消")] | A |