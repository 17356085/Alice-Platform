好的，收到你的指令。现在开始对"tank"模块的"monitor"页面进行页面分析。

由于你未提供具体的页面截图或HTML源码，我将基于“tank/monitor”这个典型的模块-页面命名，结合标准的自动化测试实践，为你生成一份**结构化的、可直接填充的页面上下文模板和定位器设计模板**。当你补充实际页面内容后，即可快速完成分析。

---

## PAGE_CONTEXT.md — 坦克模块·监控页面元素清单

```markdown
# 页面上下文：tank / monitor

## 1. 页面基本信息
| 属性 | 值 |
|------|-----|
| 页面名称 | 监控页面 |
| 所属模块 | tank |
| 页面URL | {{待补充: 如 /tank/monitor}} |
| 测试环境URL | {{待补充}} |

## 2. 页面整体结构
- **顶部区域**: 面包屑导航 / 标题（如“Tank Monitor”）
- **主内容区**: 以仪表盘/监控面板形式展示坦克状态信息
- **无左侧导航影响**: 此页面通常为全宽布局

## 3. 搜索/筛选区（如有）
| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
|--------|----------|----------|----------|------|
| {{待补充}} | 坦克ID输入框 | el-input | 顶部筛选栏 | 支持模糊搜索 |
| {{待补充}} | 状态筛选下拉框 | el-select | 顶部筛选栏 | 选项：在线/离线/告警 |
| {{待补充}} | 搜索按钮 | el-button (primary) | 顶部筛选栏 | 触发筛选 |
| {{待补充}} | 重置按钮 | el-button (default) | 顶部筛选栏 | 重置筛选条件 |

## 4. 监控面板/表格区
| 元素ID | 元素描述 | 数据类型 | 所在区域 | 备注 |
|--------|----------|----------|----------|------|
| {{待补充}} | 坦克ID | 文本 | 卡片/表格列 | 唯一标识 |
| {{待补充}} | 当前状态 | 标签/状态点 | 卡片/表格列 | 在线/离线/告警 |
| {{待补充}} | 油位(%) | 数字+进度条 | 卡片/表格列 | 0-100% |
| {{待补充}} | 发动机温度(°C) | 数字 | 卡片/表格列 | 数值范围 |
| {{待补充}} | 速度(km/h) | 数字 | 卡片/表格列 | 数值范围 |
| {{待补充}} | 操作按钮 | 按钮组 | 卡片/表格列 | {详情, 编辑, 告警确认} |

## 5. 分页区（如有）
| 元素ID | 元素描述 | 控件类型 | 备注 |
|--------|----------|----------|------|
| {{待补充}} | 分页组件 | el-pagination | 位于表格底部 |
| {{待补充}} | 每页条数 | el-select | 默认20条 |
| {{待补充}} | 页码切换 | el-button | 导航按钮 |

## 6. 弹窗/对话框
| 弹窗名称 | 弹窗标题 | 内表字段 | 按钮 | 备注 |
|----------|----------|----------|------|------|
| {{详情弹窗}} | “坦克详情” | 全部字段只读 | 关闭 | 只读 |
| {{告警确认弹窗}} | “确认告警” | 告警描述/时间 | 确认/取消 | 影响状态变更 |

## 7. 页面状态
- **加载中**: 显示 `el-loading` (骨架屏或spinner)
- **空数据**: 显示“暂无监控数据”占位图
- **错误状态**: 网络错误时显示“加载失败，请重试” + 重试按钮

## 8. 权限点
| 元素ID | 元素描述 | 权限说明 |
|--------|----------|----------|
| {{待补充}} | 确认告警按钮 | 需“告警处理”权限 |
| {{待补充}} | 编辑按钮 | 需“设备编辑”权限 |
```

---

## PAGE_ELEMENT_POSITION.md — 元素定位器设计

```markdown
# 元素定位器设计：tank / monitor

## 设计原则
- **A级优先**: 优先使用 `data-testid` / `id` / `name` / `placeholder`
- **B级保底**: 稳定的 CSS Selector
- **C级兜底**: 相对 XPath（避免绝对路径）

## 定位器表格

| 元素ID | 元素描述 | 定位策略 | 定位值 (示例) | 稳定性评级 | 备用方案 |
|--------|----------|----------|---------------|------------|----------|
| search-input | 坦克ID输入框 | A级 | `input[data-testid="tankIdInput"]` | 高 | `input[placeholder*="坦克ID"]` |
| status-select | 状态筛选下拉 | A级 | `select[data-testid="statusSelect"]` | 高 | `.el-select__wrapper` 结合标签文本 |
| search-btn | 搜索按钮 | A级 | `button[data-testid="searchBtn"]` | 高 | `button:has-text("搜索")` |
| reset-btn | 重置按钮 | A级 | `button[data-testid="resetBtn"]` | 高 | `button:has-text("重置")` |
| tank-id-cell | 坦克ID列 | B级 | `.el-table__row td:nth-child(1)` | 中 | XPath: `//*[@class="el-table__row"]/td[1]` |
| status-badge | 状态标签 | B级 | `.status-badge` | 中 | XPath: `//span[contains(@class, "status-badge")]` |
| action-edit | 编辑按钮 | A级 | `button[data-testid="editBtn"]` | 高 | `button:has-text("编辑")` |
| pagination | 分页组件 | B级 | `.el-pagination` | 高 | 无 |
| dialog-save | 弹窗保存按钮 | A级 | `button[data-testid="dialogSave"]` | 高 | `//div[contains(@class, "el-dialog")]//button[contains(text(), "确认")]` |
| toast-message | 操作反馈 | B级 | `.el-message__content` | 高 | 无 |

## 等待策略说明
| 场景 | 等待策略 | 预期条件 |
|------|----------|----------|
| 页面加载 | WebDriverWait(visibility_of_element_located) | 页面主容器可见（如表格首行或分页组件） |
| 筛选后刷新 | WebDriverWait( staleness_of / text_to_be_present_in_element ) | 表格数据刷新完成 |
| 弹窗打开 | WebDriverWait(visibility_of_element_located) | 弹窗 `el-dialog` 可见 |
| Toast 消息 | WebDriverWait(visibility_of_element_located) | `.el-message` 可见 |
```

---

## 下一步行动清单

| # | 行动项 | 说明 |
|---|--------|------|
| 1 | **提供页面截图** | 提供“tank/monitor”页面的1-3张截图（含搜索区、表格、弹窗） |
| 2 | **提供HTML源码** | 提供页面关键区域的HTML源码（尤其是搜索区、表格行、弹窗结构） |
| 3 | **启动自动生成** | 在页面源码就绪后，执行 `python tools/generate_page_interface.py --module tank --page monitor` 生成 `PAGE_INTERFACE.yaml` |

请补充具体的页面素材，我可以立即帮你完成最终版的分析。