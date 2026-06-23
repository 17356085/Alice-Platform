# TEST_CASES — DCS 全部点位（All-Data）

## 测试策略
- **目标**: 验证点位列表加载、搜索、CRUD、分页、批量选择功能
- **类型**: 功能测试 + CRUD 验证
- **Fixture**: `all_data_page` (conftest.py)

## 用例清单

| ID | 标题 | 优先级 | 类型 | 描述 |
|----|------|:-----:|------|------|
| TC-ALL-001 | 页面正常加载 | BLOCKER | smoke | 导航到页面，表格可访问 |
| TC-ALL-002 | 点位搜索 | CRITICAL | functional | 输入关键字后表格筛选更新 |
| TC-ALL-003 | 重置搜索 | NORMAL | functional | 重置按钮恢复默认列表 |
| TC-ALL-004 | 新增点位弹窗 | CRITICAL | functional | 新增按钮打开表单弹窗 |
| TC-ALL-005 | 分页导航 | NORMAL | functional | 翻页后表格正常显示 |
| TC-ALL-006 | 勾选行 | NORMAL | functional | 勾选表格行复选框 |
| TC-ALL-101 | 编辑点位 | CRITICAL | functional | 编辑按钮打开已有数据表单 |

## 覆盖率

| 维度 | 覆盖 |
|------|:----:|
| 页面加载 | ✅ |
| 搜索/筛选 | ✅ |
| 重置 | ✅ |
| 新增 | ✅ |
| 编辑 | ✅ |
| 分页 | ✅ |
| 批量选择 | ✅ |
