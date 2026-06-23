# TEST_CASES — DCS 点位配置（Point-Config）

## 测试策略
- **目标**: 验证点位配置 CRUD、搜索、表单验证、分页功能
- **类型**: 功能测试 + CRUD + 条件表单验证
- **Fixture**: `point_config_page` (conftest.py)

## 用例清单

| ID | 标题 | 优先级 | 类型 | 描述 |
|----|------|:-----:|------|------|
| TC-POINT-001 | 页面正常加载 | BLOCKER | smoke | 导航到页面，表格可访问 |
| TC-POINT-002 | 点位搜索 | CRITICAL | functional | 输入关键字后表格更新 |
| TC-POINT-003 | 重置搜索 | NORMAL | functional | 重置恢复默认列表 |
| TC-POINT-004 | 新增弹窗 | CRITICAL | functional | 新增按钮打开表单，填写名称 |
| TC-POINT-005 | 新增并清理 | CRITICAL | destructive | 完整新增流程 + cleanup |
| TC-POINT-006 | 编辑点位 | CRITICAL | functional | 编辑按钮打开已有数据表单 |
| TC-POINT-007 | 分页导航 | NORMAL | functional | 翻页后表格正常显示 |

## 覆盖率

| 维度 | 覆盖 |
|------|:----:|
| 页面加载 | ✅ |
| 搜索/筛选 | ✅ |
| 重置 | ✅ |
| 新增 (含清理) | ✅ |
| 编辑 | ✅ |
| 分页 | ✅ |
| 告警规则表单 | manual |
