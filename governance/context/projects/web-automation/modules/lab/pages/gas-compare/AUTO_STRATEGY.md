# AUTO_STRATEGY — lab / gas-compare + water-compare

> Phase 3.5 | 2026-06-12

## 自动化覆盖建议
| 场景 | 自动化 | 理由 |
|------|:--:|------|
| 页面加载(空状态) | ✅ | 简单 |
| 双位置对比查询 | ✅ | 2个el-select+日期+按钮 |
| 相同位置校验 | ✅ | 验证无意义对比 |

## 实现方式
- gas-compare 和 water-compare 共用一个 PageObject 类(参数化路由/指标)
- 对比表格定位器需兼容空数据状态