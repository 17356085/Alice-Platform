# AUTO_STRATEGY — tank / monitor

## 自动化覆盖矩阵

| 用例编号 | 标题 | 优先级 | 自动化 | 理由 |
|----------|------|--------|:------:|------|
| TC-TANK-MON-001 | 页面正常加载 | P0 | ✅ | 冒烟必测，定位器A级 |
| TC-TANK-MON-002 | 统计卡片数值显示 | P1 | ✅ | 核心数据，定位器B级 |
| TC-TANK-MON-003 | 按储罐编号精确搜索 | P0 | ✅ | 核心功能 |
| TC-TANK-MON-004 | 按名称模糊搜索 | P1 | ✅ | 同 TC-003，搜索方法复用 |
| TC-TANK-MON-005 | 按储罐类型筛选 | P1 | ✅ | 需要打开下拉框 |
| TC-TANK-MON-006 | 按运行状态筛选 | P1 | ✅ | 需要打开下拉框 |
| TC-TANK-MON-007 | 组合条件搜索 | P1 | ✅ | 搜索方法组合复用 |
| TC-TANK-MON-008 | 无匹配结果 | P1 | ✅ | 边界条件 |
| TC-TANK-MON-009 | 重置搜索 | P1 | ✅ | 核心操作 |
| TC-TANK-MON-010 | 特殊字符搜索 | P1 | ✅ | 安全测试 |
| TC-TANK-MON-011 | 表头列验证 | P0 | ✅ | 页面完整性 |
| TC-TANK-MON-012 | 运行状态标签颜色 | P1 | ❌ | 需视觉判断，非自动化适宜 |
| TC-TANK-MON-013 | 查看储罐详情 | P0 | ✅ | 核心功能 |
| TC-TANK-MON-014 | 查看历史数据 | P1 | ✅ | 核心功能 |
| TC-TANK-MON-015 | 操作工权限 | P0 | 🔄 | 需要多账号 |
| TC-TANK-MON-016 | 分页控件 | P2 | ✅ | 基本验证 |
| TC-TANK-MON-017 | 表单纯空校验 | P2 | 🔄 | 需弹窗字段确认 |
| TC-TANK-MON-018 | 接口超时 | P1 | ⚠️ | 需 CDP 工具 |

## PageObject 拆分方案

建议拆分：
- `TankMonitorPage` — 主页面（搜索区 + 统计卡片 + 表格 + 分页）
- `TankMonitorDialog` — 详情弹窗/历史数据弹窗（如弹窗字段复杂）

## 公共组件复用分析
- 页面使用自定义 UI 框架（非 Element Plus）
- BasePage 中的通用定位器（DIALOG/TOAST/TABLE_ROWS 等）不可直接在 tank 页面复用
- 但 BasePage 的核心方法（click/input_text/find 等）可以复用

## 等待策略
- 表格刷新：等待 `table.data-table tbody tr` 出现或变化
- 暂无统一的 loading 遮罩，需使用自定义等待

## ROI 分析
- 预估开发时间：4h（含 PageObject + 测试脚本）
- 预估维护成本：0.5h/月（定位器稳定，A级占比高）
- 手工执行时间：20min/次 × 每周3次 = 1h/周
- ROI：约 1 个月回本

## 待确认
- 新增储罐弹窗的具体表单字段 → 获取弹窗 HTML 后补充覆盖
- 下拉框的 DOM 结构（el-select 还是自定义）→ 触发下拉后补充
