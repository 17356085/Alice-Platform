# PAGE_ELEMENT_POSITION — lab / water-compare

> Phase 1 | 2026-06-12 | 定位策略与 gas-compare 完全一致

| 元素 | 策略 | 定位值 | 等级 |
|------|------|--------|:--:|
| 开始日期 | CSS | input[placeholder*="开始日期"] | A |
| 结束日期 | CSS | input[placeholder*="结束日期"] | A |
| 取样位置1 | XPATH | (//div[contains(@class,"el-select__wrapper")])[1] | B |
| 取样位置2 | XPATH | (//div[contains(@class,"el-select__wrapper")])[2] | B |
| 查询/重置 | XPATH | //button[contains(.,"查询")] / //button[contains(.,"重置")] | A |
| 对比表格 | CSS | tbody tr | B |