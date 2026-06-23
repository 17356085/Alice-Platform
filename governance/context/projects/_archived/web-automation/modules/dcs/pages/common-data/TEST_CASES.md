# TEST_CASES — DCS 常用点位（Common-Data）

## 测试策略
- **目标**: 验证常用点位卡片加载、搜索、新增、删除功能
- **类型**: 功能测试 + 卡片交互验证
- **Fixture**: `common_data_page` (conftest.py)

## 用例清单

| ID | 标题 | 优先级 | 类型 | 描述 |
|----|------|:-----:|------|------|
| TC-COM-001 | 页面正常加载 | BLOCKER | smoke | 导航到页面，卡片区域可访问 |
| TC-COM-002 | 搜索常用点位 | CRITICAL | functional | 输入关键字后卡片筛选 |
| TC-COM-003 | 重置搜索 | NORMAL | functional | 重置恢复默认卡片 |
| TC-COM-004 | 点击卡片 | NORMAL | functional | 点击卡片查看详情 |
| TC-COM-005 | 新增弹窗 | CRITICAL | functional | 新增按钮打开选择弹窗 |

## 覆盖率

| 维度 | 覆盖 |
|------|:----:|
| 页面加载 | ✅ |
| 搜索/筛选 | ✅ |
| 重置 | ✅ |
| 卡片交互 | ✅ |
| 新增 | ✅ |
