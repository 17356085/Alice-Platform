# TEST_CASES.md — SAP推送日志 (sap-push-log)

> Generated from existing test code
> Module: system-management

## Test Case Index

| Case ID | Title | Type | Priority | Automation |
|---------|-------|------|----------|------------|
| SY-SAPLOG-01 | 正常显示SAP推送日志列表及相关字段 | smoke | P0 | ✅ |
| SY-SAPLOG-02 | 按推送状态筛选 | functional | P1 | ✅ |
| SY-SAPLOG-03 | 按日期范围搜索 | functional | P1 | ✅ |
| SY-SAPLOG-04 | 重置按钮功能正常 | functional | P0 | ✅ |
| SY-SAPLOG-05 | 分页跳转 | functional | P1 | ✅ |
| SY-SAPLOG-06 | 查看推送详情 | functional | P1 | ✅ |

## Test Cases

### SY-SAPLOG-01: 正常显示SAP推送日志列表及相关字段

- **Type**: smoke
- **Priority**: P0
- **Preconditions**: 用户已登录系统，拥有SAP推送日志页面访问权限
- **Steps**:
  1. 导航至SAP推送日志页面（`#/system/workflow/sap-push-log`）
  2. 获取表格表头字段
  3. 校验表头是否包含关键列（请求、状态、时间、推送等）
  4. 获取表格行数，若为0则检查空状态文案
- **Expected**: 页面正常加载，表格表头包含请求、状态、时间、推送等至少2个关键字段；无数据时显示空状态提示
- **Automation**: `test_sy_saplog_01_page_display` in `test_sap_push_log.py` (标记 `@pytest.mark.smoke`)

### SY-SAPLOG-02: 按推送状态筛选

- **Type**: functional
- **Priority**: P1
- **Preconditions**: 用户已登录系统，SAP推送日志列表有数据
- **Steps**:
  1. 点击重置按钮清空筛选条件
  2. 选择推送状态为"成功"
  3. 点击搜索按钮
  4. 检查筛选结果
- **Expected**: 筛选结果正常显示，仅显示符合成功状态的列表项；无数据时显示空状态文案（含"暂无数据"）
- **Automation**: `test_sy_saplog_02_search_by_status` in `test_sap_push_log.py`

### SY-SAPLOG-03: 按日期范围搜索

- **Type**: functional
- **Priority**: P1
- **Preconditions**: 用户已登录系统，SAP推送日志列表有数据
- **Steps**:
  1. 点击重置按钮清空筛选条件
  2. 设置日期范围为 `2026-01-01` 至 `2026-12-31`
  3. 点击搜索按钮
  4. 检查筛选结果
- **Expected**: 筛选结果正常显示，仅显示符合日期范围的列表项；无数据时显示空状态文案（含"暂无数据"）
- **Automation**: `test_sy_saplog_03_search_by_date` in `test_sap_push_log.py`

### SY-SAPLOG-04: 重置按钮功能正常

- **Type**: functional
- **Priority**: P0
- **Preconditions**: 用户已登录系统，SAP推送日志列表有数据
- **Steps**:
  1. 设置日期范围
  2. 点击重置按钮
  3. 点击搜索按钮验证列表正常加载
- **Expected**: 所有筛选条件被清空，列表恢复全量数据正常加载
- **Automation**: `test_sy_saplog_04_reset_button` in `test_sap_push_log.py`

### SY-SAPLOG-05: 分页跳转

- **Type**: functional
- **Priority**: P1
- **Preconditions**: 用户已登录系统，SAP推送日志列表有多页数据
- **Steps**:
  1. 点击重置按钮清空筛选条件
  2. 记录当前页码
  3. 点击下一页按钮
  4. 验证翻页后页码变化
  5. 检查翻页后表格数据是否正常加载
- **Expected**: 翻页后页码变化（仅一页数据时跳过），翻页后表格行数大于0
- **Automation**: `test_sy_saplog_05_pagination` in `test_sap_push_log.py`

### SY-SAPLOG-06: 查看推送详情

- **Type**: functional
- **Priority**: P1
- **Preconditions**: 用户已登录系统，SAP推送日志列表至少有一条数据
- **Steps**:
  1. 校验列表是否有数据（无数据则跳过）
  2. 点击第一行的"查看详情"按钮
  3. 等待详情弹窗出现（最长8秒）
  4. 关闭详情弹窗
- **Expected**: 详情弹窗正常弹出，显示SAP推送的完整信息；弹窗可正常关闭
- **Automation**: `test_sy_saplog_06_detail_view` in `test_sap_push_log.py`
