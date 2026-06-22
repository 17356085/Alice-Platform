# RISK_MODEL — DCS 关键参数监控（Monitor）

## 风险矩阵

| ID | 风险 | 可能性 | 影响 | 等级 | 缓解 |
|----|------|:-----:|:---:|:----:|------|
| R-MON-01 | WebSocket 实时推送导致元素状态不一致 | M | H | **高** | 刷新后断言，`wait_vue_stable` 前置 |
| R-MON-02 | 参数卡片由 CSS Grid 动态渲染，个数不固定 | H | M | **高** | 用 `find_all` 计数，避免硬编码卡片数 |
| R-MON-03 | ECharts 图表渲染延迟导致白屏 | M | M | **中** | `wait_element_visible` 检查 canvas |
| R-MON-04 | 状态颜色编码（绿/红/黄）因 CSS 变量变化 | L | L | **低** | 用 el-tag class 断言，不依赖具体颜色 |
| R-MON-05 | 卡片拖拽排序不支持 | — | — | — | N/A（monitor 页无拖拽） |

## 测试影响
- **实时数据**: 避免精确值断言，用 `>=` 或 `in` 检查
- **图表**: smoke 测试只验证 canvas 存在，不验证数据点
- **并发**: 避免多线程同时操作卡片
