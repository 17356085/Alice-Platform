# PAGE_ELEMENT_POSITION — sales / customer

> 从 CustomerPage.py + TECH_ANALYSIS 提取 | 2026-06-11

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 客户名称/编码 | XPATH | `//input[@placeholder='客户名称/编码']` | A | |
| 客户等级 | XPATH | `//div[contains(@class,'el-select')][.//input[@placeholder='客户等级']]` | B | |
| 合作状态 | XPATH | `//div[contains(@class,'el-select')][.//input[@placeholder='合作状态']]` | B | |
| 查询 | XPATH | `//button[.//span[text()='查询']]` | A | |
| 重置 | XPATH | `//button[.//span[text()='重置']]` | A | |
| 新增客户 | XPATH | `//button[.//span[text()='新增客户']]` | A | |
| 查看 | XPATH | `.//button[.//span[text()='查看']]` | A | |
| 编辑 | XPATH | `.//button[.//span[text()='编辑']]` | A | |
| 资质维护 | XPATH | `.//button[.//span[text()='资质维护']]` | A | |
| 弹窗确定 | CSS | `.el-dialog__footer .el-button--primary` | A | |

<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-11 -->
