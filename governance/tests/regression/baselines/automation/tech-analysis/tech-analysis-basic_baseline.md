请提供 `equipment/alarm-config` 页面的 HTML 源码（可通过浏览器 F12 复制），以及页面截图（可选），以便我进行 Element Plus 组件识别和定位器设计。同时请确认该页面是否支持以下行为（用于等待策略设计）：

1. 页面是否包含表格（el-table）？
2. 是否有搜索/筛选区域？
3. 是否有新增/编辑/删除弹窗（el-dialog）？
4. 是否有分页器（el-pagination）？
5. 是否依赖异步加载（loading 状态）？

收到 HTML 后，我将输出：
- `TECH_ANALYSIS.md` — 组件识别、DOM 结构分析、A/B/C 三级定位器表、异步等待策略、风险点
- `PAGE_ELEMENT_POSITION.md` — 可直接用于 Page Object 的元素定位字典

示例输出格式（基于 element-plus 常见结构）：

| 元素 | 推荐定位策略 | 定位值 | 稳定性 | 备注 |
|------|-------------|--------|--------|------|
| 表格容器 | CSS | `.el-table` | A | 表格顶层容器 |
| 表格行 | CSS | `.el-table__body-wrapper .el-table__row` | B | 动态行，v-for |
| 新增按钮 | XPATH | `//button[.//span[text()='新增']]` | A | 文字稳定 |
| 弹窗确定 | XPATH | `//div[contains(@class,'el-dialog')]//button[.//span[text()='确定']]` | A | |
| 分页器 | CSS | `.el-pagination` | A | |

请提供 HTML 源码。