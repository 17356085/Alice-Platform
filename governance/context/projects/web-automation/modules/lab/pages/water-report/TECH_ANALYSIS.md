# TECH_ANALYSIS — lab / water-report

> Phase 3 | 2026-06-12 | 参考 gas-analysis-report/TECH_ANALYSIS.md

## 技术栈
- UI: Element Plus (搜索/弹窗) + 自定义 report-table (表格)
- 表格: 非el-table，class=report-table，多行表头，含统计行(tfoot)
- 弹窗: 标准 el-dialog

## 定位策略
- 搜索区: placeholder属性(A级) + 文本匹配XPath(A级)
- 表格: CSS thead/tbody + 多行表头取最后一行
- 弹窗: BasePage DIALOG/DIALOG_SAVE 通用定位器

## 异步等待
- 切换取样位置 → 等待表格行数变化
- 新增保存 → 等待弹窗关闭 + toast出现 + 表格刷新
- 日期搜索 → 等待loading遮罩消失

## 与 gas-analysis-report 共用模式
- 定位器命名前缀统一
- 表格等待策略复用
- 新增弹窗流程一致(仅指标字段不同)