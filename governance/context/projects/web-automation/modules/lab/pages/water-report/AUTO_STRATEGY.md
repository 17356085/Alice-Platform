# AUTO_STRATEGY — lab / water-report

> Phase 3.5 | 2026-06-12

## 自动化覆盖建议
| 场景 | 自动化 | 理由 |
|------|:--:|------|
| 页面加载+元素完整性 | ✅ | 定位器稳定，A级>70% |
| 切换取样位置 | ✅ | 自定义Tab可定位 |
| 新增报告单(合法) | ✅ | 标准el-dialog |
| 必填校验 | ✅ | el-form-item__error |
| 指标边界值 | ✅ | 参数化测试 |
| 日期搜索 | ✅ | placeholder定位 |
| 导出 | ⚠️ | 涉及文件下载，需特殊处理 |

## 不建议自动化
- 导出文件内容校验(需人工比对)

## 实现方式
- PageObject: 继承BasePage，复用DIALOG/TOAST通用定位器
- 表格: 自定义定位(thead/tbody)，不用BasePage.TABLE_ROWS
- 并发: 只读搜索用例可并行