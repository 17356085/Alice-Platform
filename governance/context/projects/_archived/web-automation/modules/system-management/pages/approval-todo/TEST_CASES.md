# TEST_CASES.md — 待我审批 (approval-todo)

> Generated from existing test code
> Module: system-management

## Test Case Index

| Case ID | Title | Type | Priority | Automation |
|---------|-------|------|----------|------------|
| SY-TODO-01 | 正常显示待我审批列表及相关字段 | smoke | P0 | ✅ |
| SY-TODO-02 | 按工厂代码搜索 | functional | P0 | ✅ |
| SY-TODO-03 | 按审批状态筛选 | functional | P1 | ✅ |
| SY-TODO-04 | 按日期范围搜索 | functional | P1 | ✅ |
| SY-TODO-05 | 重置按钮功能正常 | functional | P0 | ✅ |
| SY-TODO-06 | 分页跳转 | functional | P1 | ✅ |
| SY-TODO-07 | 查看审批详情 | functional | P0 | ✅ |
| SY-TODO-08 | 审批通过操作 | functional | P0 | ✅ |

## Test Cases

### SY-TODO-01: 正常显示待我审批列表及相关字段

- **Type**: smoke
- **Priority**: P0
- **Preconditions**: 用户已登录系统，拥有待我审批页面访问权限
- **Steps**:
  1. 导航至待我审批页面（`#/system/workflow/todo`）
  2. 获取表格表头字段
  3. 校验表头是否包含关键列（审批编号/审批状态等）
  4. 获取表格行数，若为0则检查空状态文案
- **Expected**: 页面正常加载，表格表头包含审批编号、标题、审批状态等至少2个关键字段；无数据时显示空状态提示
- **Automation**: `test_sy_todo_01_page_display` in `test_approval_todo.py` (标记 `@pytest.mark.smoke`)

### SY-TODO-02: 按工厂代码搜索

- **Type**: functional
- **Priority**: P0
- **Preconditions**: 用户已登录系统，待我审批列表有数据
- **Steps**:
  1. 点击重置按钮清空筛选条件
  2. 输入工厂代码关键词（如 "test"）
  3. 点击搜索按钮
  4. 检查搜索结果
- **Expected**: 搜索结果正常显示，列表不为空或显示空状态文案（含"暂无"）
- **Automation**: `test_sy_todo_02_search_by_title` in `test_approval_todo.py`
- **Notes**: 搜索字段实际对应"工厂代码"（el-select），非标题输入框

### SY-TODO-03: 按审批状态筛选

- **Type**: functional
- **Priority**: P1
- **Preconditions**: 用户已登录系统，待我审批列表有数据
- **Steps**:
  1. 点击重置按钮清空筛选条件
  2. 选择审批状态为"待审批"
  3. 点击搜索按钮
  4. 检查筛选结果
- **Expected**: 筛选结果正常显示，仅显示符合待审批状态的列表项；无数据时显示空状态文案（含"暂无"）
- **Automation**: `test_sy_todo_03_search_by_status` in `test_approval_todo.py`

### SY-TODO-04: 按日期范围搜索

- **Type**: functional
- **Priority**: P1
- **Preconditions**: 用户已登录系统，待我审批列表有数据
- **Steps**:
  1. 点击重置按钮清空筛选条件
  2. 设置日期范围为 `2026-01-01` 至 `2026-12-31`
  3. 点击搜索按钮
  4. 检查筛选结果
- **Expected**: 筛选结果正常显示，仅显示符合日期范围的列表项；无数据时显示空状态文案（含"暂无"）
- **Automation**: `test_sy_todo_04_search_by_date` in `test_approval_todo.py`

### SY-TODO-05: 重置按钮功能正常

- **Type**: functional
- **Priority**: P0
- **Preconditions**: 用户已登录系统，待我审批列表有数据
- **Steps**:
  1. 输入工厂代码关键词（如 "test"）
  2. 设置日期范围
  3. 点击重置按钮
  4. 点击搜索按钮验证列表正常加载
- **Expected**: 所有筛选条件被清空，列表恢复全量数据正常加载
- **Automation**: `test_sy_todo_05_reset_button` in `test_approval_todo.py`

### SY-TODO-06: 分页跳转

- **Type**: functional
- **Priority**: P1
- **Preconditions**: 用户已登录系统，待我审批列表有多页数据
- **Steps**:
  1. 点击重置按钮清空筛选条件
  2. 记录当前页码
  3. 点击下一页按钮
  4. 验证翻页后页码变化
  5. 检查翻页后表格数据是否正常加载
- **Expected**: 翻页后页码变化（仅一页数据时跳过），翻页后表格行数大于0
- **Automation**: `test_sy_todo_06_pagination` in `test_approval_todo.py`

### SY-TODO-07: 查看审批详情

- **Type**: functional
- **Priority**: P0
- **Preconditions**: 用户已登录系统，待我审批列表至少有一条数据
- **Steps**:
  1. 校验列表是否有数据（无数据则跳过）
  2. 点击第一行的"查看详情"按钮
  3. 等待详情弹窗出现（最长8秒）
  4. 关闭详情弹窗
- **Expected**: 详情弹窗正常弹出，显示申请的完整信息和审批进度；弹窗可正常关闭
- **Automation**: `test_sy_todo_07_detail_view` in `test_approval_todo.py`

### SY-TODO-08: 审批通过操作

- **Type**: functional
- **Priority**: P0
- **Preconditions**: 用户已登录系统并有审批权限，待我审批列表至少有一条可审批的数据
- **Steps**:
  1. 校验列表是否有数据（无数据则跳过）
  2. 点击第一行的"通过"按钮
  3. 填写审批意见 `[AUTO] 自动化测试-审批通过`
  4. 点击确认按钮提交审批
  5. 等待toast提示（最长6秒）
- **Expected**: 审批操作已触发，toast提示包含"成功"、"通过"或"完成"等关键字
- **Automation**: `test_sy_todo_08_approve_action` in `test_approval_todo.py`
