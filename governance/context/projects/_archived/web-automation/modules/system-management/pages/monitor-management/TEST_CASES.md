# TEST_CASES.md — 系统监控 (monitor-management)

> Generated from existing test code
> Module: system-management

## Test Case Index

| Case ID | Title | Type | Priority | Automation |
|---------|-------|------|----------|------------|
| SY-MONITOR-01 | 正常显示系统监控页面 | smoke | P0 | ✅ |
| SY-MONITOR-02 | 指标卡片正常展示 | functional | P1 | ✅ |
| SY-MONITOR-03 | 指标数值可读 | functional | P1 | ✅ |
| SY-MONITOR-04 | 刷新监控数据 | functional | P1 | ✅ |

## Test Cases

### SY-MONITOR-01: 正常显示系统监控页面

- **Type**: smoke
- **Priority**: P0
- **Preconditions**: 用户已登录系统，拥有系统监控页面访问权限
- **Steps**:
  1. 导航至系统监控页面（`#/system/monitor`）
  2. 等待页面加载（最长15秒）
  3. 验证页面内容是否渲染
- **Expected**: 系统监控页面正常加载，指标卡片或图表容器可见，页面无异常报错
- **Automation**: `test_sy_monitor_01_page_display` in `test_monitor_management.py`

### SY-MONITOR-02: 指标卡片正常展示

- **Type**: functional
- **Priority**: P1
- **Preconditions**: 用户已登录系统，后端监控数据推送正常
- **Steps**:
  1. 导航至系统监控页面
  2. 等待页面加载（最长15秒）
  3. 获取指标卡片数量
  4. 若卡片数量为0，尝试读取服务器信息文本或指标值
- **Expected**: 至少存在一种监控数据展示形式（指标卡片 > 0，或服务器信息文本可见，或指标值/标签非空）
- **Automation**: `test_sy_monitor_02_metric_cards` in `test_monitor_management.py`

### SY-MONITOR-03: 指标数值可读

- **Type**: functional
- **Priority**: P1
- **Preconditions**: 用户已登录系统，后端监控数据推送正常
- **Steps**:
  1. 导航至系统监控页面
  2. 等待页面加载（最长15秒）
  3. 获取指标数值和标签列表
  4. 若无可读指标数据，尝试读取服务器信息文本
  5. 若仍无数据则跳过用例
- **Expected**: 指标数值/标签列表非空，或服务器信息文本含有效内容；纯图表渲染模式下可跳过
- **Automation**: `test_sy_monitor_03_metric_values` in `test_monitor_management.py`

### SY-MONITOR-04: 刷新监控数据

- **Type**: functional
- **Priority**: P1
- **Preconditions**: 用户已登录系统，页面存在刷新按钮
- **Steps**:
  1. 导航至系统监控页面
  2. 等待页面加载（最长15秒）
  3. 点击刷新按钮
  4. 等待页面重新加载（最长10秒）
  5. 验证刷新后页面仍正常渲染
- **Expected**: 点击刷新后页面重新加载，指标卡片/图表正常显示，刷新功能正常可用；若页面无刷新按钮则跳过
- **Automation**: `test_sy_monitor_04_refresh` in `test_monitor_management.py`
