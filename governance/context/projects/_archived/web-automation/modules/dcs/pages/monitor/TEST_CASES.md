# TEST_CASES — DCS 关键参数监控（Monitor）

## 测试策略
- **目标**: 验证参数卡片加载、搜索、刷新、新增/编辑/删除功能
- **类型**: 功能测试 + UI 验证
- **Fixture**: `monitor_page` (conftest.py)

## 用例清单

| ID | 标题 | 优先级 | 类型 | 描述 |
|----|------|:-----:|------|------|
| TC-MON-001 | 页面正常加载 | BLOCKER | smoke | 导航到页面，验证至少 1 个参数卡片可见 |
| TC-MON-002 | 参数搜索 | CRITICAL | functional | 输入关键字后卡片筛选更新 |
| TC-MON-003 | 重置搜索 | NORMAL | functional | 重置按钮恢复默认卡片展示 |
| TC-MON-004 | 数据刷新 | CRITICAL | functional | 刷新按钮重新加载实时数据 |
| TC-MON-005 | 新增参数弹窗 | CRITICAL | functional | 新增按钮打开表单弹窗 |
| TC-MON-006 | 参数卡片详情 | NORMAL | functional | 点击卡片查看详情 |
| TC-MON-101 | 编辑参数 | CRITICAL | functional | 编辑按钮打开已有数据表单 |

## 覆盖率

| 维度 | 覆盖 |
|------|:----:|
| 页面加载 | ✅ |
| 搜索/筛选 | ✅ |
| 重置 | ✅ |
| 新增 | ✅ |
| 编辑 | ✅ |
| 刷新 | ✅ |
| 分页 | N/A (卡片视图) |
