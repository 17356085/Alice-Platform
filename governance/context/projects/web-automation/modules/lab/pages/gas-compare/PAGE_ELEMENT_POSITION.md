# PAGE_ELEMENT_POSITION — lab / gas-compare

> Phase 1 | 2026-06-12

## 搜索区
| 元素 | 策略 | 定位值 | 等级 |
|------|------|--------|:--:|
| 开始日期 | CSS | input[placeholder*="开始日期"] | A |
| 结束日期 | CSS | input[placeholder*="结束日期"] | A |
| 取样位置1 | XPATH | (//div[contains(@class,"el-select__wrapper")])[1] | B |
| 取样位置2 | XPATH | (//div[contains(@class,"el-select__wrapper")])[2] | B |
| 查询 | XPATH | //button[contains(.,"查询")] | A |
| 重置 | XPATH | //button[contains(.,"重置")] | A |

## 对比表格
| 元素 | 策略 | 定位值 | 等级 |
|------|------|--------|:--:|
| 表头 | CSS | thead tr:last-child th | A |
| 数据行 | CSS | tbody tr | B |
| 空数据 | CSS | [class*=empty] | B |