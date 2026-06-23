# RISK_MODEL — DCS 全部点位（All-Data）

## 风险矩阵

| ID | 风险 | 可能性 | 影响 | 等级 | 缓解 |
|----|------|:-----:|:---:|:----:|------|
| R-ALL-01 | 点位数量 >1000，表格分页加载慢 | H | H | **高** | 用分页断言，不依赖全量数据 |
| R-ALL-02 | 上报率实时计算延迟 | M | M | **中** | 避免断言精确上报率值 |
| R-ALL-03 | 批量操作后表格刷新异步 | M | H | **高** | 操作后 `wait_vue_stable` + `_wait_loading_gone` |
| R-ALL-04 | 导入 Excel 格式校验失败 | M | L | **低** | smoke 测试跳过导入验证 |
| R-ALL-05 | 删除确认弹窗为 message-box 非 dialog | M | M | **中** | 用通用确认按钮 XPath `//button[.//span[text()="确定"]]` |

## 测试影响
- **大数据量**: 搜索后用 `get_row_count()` 验证表格响应，不查具体值
- **批量操作**: 先检查行数 >0 再执行 select
- **弹窗类型**: 区分 dialog 和 message-box 确认
