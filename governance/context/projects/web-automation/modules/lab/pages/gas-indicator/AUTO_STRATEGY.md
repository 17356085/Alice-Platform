# AUTO_STRATEGY — lab / gas-indicator + water-indicator

> Phase 3.5 | 2026-06-12

## 自动化覆盖建议
| 场景 | 自动化 | 理由 |
|------|:--:|------|
| 页面加载 | ✅ | 最简单页面 |
| 行数验证(23/22) | ✅ | JS计数 |
| 只读性验证 | ✅ | 断言无按钮 |

## 实现方式
- gas-indicator和water-indicator共用PageObject(参数化)
- 最低优先级：无交互，仅验证数据完整性