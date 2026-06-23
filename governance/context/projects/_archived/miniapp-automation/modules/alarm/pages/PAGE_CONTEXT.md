# PAGE_CONTEXT — miniapp / alarm

> 从 alarm.page.js 提取 | 2026-06-11

## 页面信息

| 属性 | 值 |
|------|-----|
| 路径 | `pages/alarm/index` (TabBar) |
| Page Object | `alarm.page.js` (AlarmListPage, IS_TAB_PAGE) |
| 测试脚本 | `tests/p0-core/test_alarm.test.js` |

## 核心元素

| 元素 | 类型 | data key | 说明 |
|------|------|----------|------|
| 报警列表 | array | `i` / `filteredList` / `alarmList` | 报警数据 |
| 统计数据 | object | `s` / `statistics` | 报警统计 |
| 筛选Tab | array | `d` / `filterTabs` | 全部/紧急/普通/已处理 |
| 报警项 | cell | 列表项 | 含级别标签+时间+摘要 |
| 级别标签 | tag | — | 红(urgent)/黄(normal)/灰(processed) |

## 关键交互

1. 报警列表加载→按时间倒序
2. 按级别筛选：全部/紧急/普通/已处理（`switchTab` 方法）
3. 点击报警项→跳转详情页
4. 下拉刷新列表

## 获取方法

- `getAlarmList()`: 从 data.i 获取报警数组
- `getStatistics()`: 从 data.s 获取统计
- `filterByLevel(level)`: 按级别筛选
- `getFilterTabs()`: 获取筛选Tab带角标数据
- `tapAlarmItem(index)`: 点击进入详情

<!-- status: draft | phase: Phase 1 | completed_by: ai-assistant | completed_at: 2026-06-11 -->
