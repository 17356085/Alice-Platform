# TEST_CASES.md — 我已审批 (Approval History)

> Generated from: test_approval_history.py
> Module: system-management
> Page: approval-history
> Route: #/system/workflow/history

## Test Case Index

| Case ID | Title | Type | Priority | Automation |
|---------|-------|------|----------|------------|
| SY-HIST-01 | 正常显示我已审批列表及相关字段 | smoke | P0 | ✅ test_sy_hist_01_page_display |
| SY-HIST-02 | 按工厂代码搜索 | functional | P0 | ✅ test_sy_hist_02_search_by_title |
| SY-HIST-03 | 按审批状态筛选 | functional | P0 | ✅ test_sy_hist_03_search_by_status |
| SY-HIST-04 | 按日期范围搜索 | functional | P0 | ✅ test_sy_hist_04_search_by_date |
| SY-HIST-05 | 重置按钮功能正常 | functional | P0 | ✅ test_sy_hist_05_reset_button |
| SY-HIST-06 | 分页跳转 | functional | P1 | ✅ test_sy_hist_06_pagination |
| SY-HIST-07 | 查看审批详情 | functional | P1 | ✅ test_sy_hist_07_detail_view |

## Test Cases

### SY-HIST-01: 正常显示我已审批列表及相关字段
- **Type**: smoke
- **Priority**: P0
- **Preconditions**: 用户已登录，存在已审批记录
- **Steps**:
  1. 导航到 #/system/workflow/history
  2. 获取表头
  3. 校验包含关键列：审批编号、标题、审批状态
- **Expected**: 表头包含审批编号/标题/审批状态至少一项，且行数≥2；若无数据则跳过
- **Automation**: `test_sy_hist_01_page_display`

### SY-HIST-02: 按工厂代码搜索
- **Type**: functional
- **Priority**: P0
- **Preconditions**: 页面已加载
- **Steps**:
  1. 点击重置
  2. 输入工厂代码关键词 "test"
  3. 点击搜索
- **Expected**: 显示搜索结果或"暂无"提示
- **Automation**: `test_sy_hist_02_search_by_title`
- **Note**: 页面搜索字段实际为"工厂代码"非"标题"

### SY-HIST-03: 按审批状态筛选
- **Type**: functional
- **Priority**: P0
- **Preconditions**: 页面已加载
- **Steps**:
  1. 点击重置
  2. 选择状态："已通过"
  3. 点击搜索
- **Expected**: 显示符合条件的列表项，或无数据时显示"暂无"
- **Automation**: `test_sy_hist_03_search_by_status`

### SY-HIST-04: 按日期范围搜索
- **Type**: functional
- **Priority**: P0
- **Preconditions**: 页面已加载
- **Steps**:
  1. 点击重置
  2. 设置日期范围：2026-01-01 ~ 2026-12-31
  3. 点击搜索
- **Expected**: 显示符合日期条件的列表项
- **Automation**: `test_sy_hist_04_search_by_date`

### SY-HIST-05: 重置按钮功能正常
- **Type**: functional
- **Priority**: P0
- **Preconditions**: 页面已加载
- **Steps**:
  1. 输入筛选条件（工厂代码 + 日期范围）
  2. 点击重置
  3. 点击搜索验证列表正常加载
- **Expected**: 所有筛选条件清空，列表正常加载
- **Automation**: `test_sy_hist_05_reset_button`

### SY-HIST-06: 分页跳转
- **Type**: functional
- **Priority**: P1
- **Preconditions**: 页面已加载，数据超过一页
- **Steps**:
  1. 点击重置
  2. 记录第一页页码
  3. 点击下一页
- **Expected**: 页码变化，翻页后列表仍正常加载；仅一页时跳过
- **Automation**: `test_sy_hist_06_pagination`

### SY-HIST-07: 查看审批详情
- **Type**: functional
- **Priority**: P1
- **Preconditions**: 页面已加载，列表有数据
- **Steps**:
  1. 校验列表是否有数据
  2. 点击第一行详情
  3. 校验详情弹窗出现
  4. 关闭详情弹窗
- **Expected**: 弹出审批详情弹窗，可正常关闭
- **Automation**: `test_sy_hist_07_detail_view`
