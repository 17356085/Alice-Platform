# TEST_CASES — DCS 上传日志（Upload-Log）

## 测试策略
- **目标**: 验证日志列表加载、时间/状态筛选、搜索、详情查看、分页功能
- **类型**: 功能测试 + 日志筛选验证
- **Fixture**: `upload_log_page` (conftest.py)

## 用例清单

| ID | 标题 | 优先级 | 类型 | 描述 |
|----|------|:-----:|------|------|
| TC-UL-001 | 页面正常加载 | BLOCKER | smoke | 导航到页面，表格可访问 |
| TC-UL-002 | 统计卡片 | NORMAL | functional | 验证上传统计卡片可读 |
| TC-UL-003 | 日志搜索 | CRITICAL | functional | 搜索关键字后表格更新 |
| TC-UL-004 | 按状态筛选 | CRITICAL | functional | 选择状态后表格筛选 |
| TC-UL-005 | 重置搜索 | NORMAL | functional | 重置恢复默认列表 |
| TC-UL-006 | 查看详情 | NORMAL | functional | 打开日志详情弹窗 |
| TC-UL-007 | 分页导航 | NORMAL | functional | 翻页后表格正常显示 |

## 覆盖率

| 维度 | 覆盖 |
|------|:----:|
| 页面加载 | ✅ |
| 统计卡片 | ✅ |
| 搜索/筛选 | ✅ |
| 状态筛选 | ✅ |
| 重置 | ✅ |
| 详情弹窗 | ✅ |
| 分页 | ✅ |
