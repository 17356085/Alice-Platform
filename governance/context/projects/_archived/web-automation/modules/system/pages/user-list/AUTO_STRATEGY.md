# AUTO_STRATEGY — 用户列表页 自动化策略

> 最后更新: 2026-06-14 | 执行状态: ✅ 11/11 passed (无失败)

## 当前自动化状态

| 维度 | 状态 |
|------|------|
| Page Object | ✅ UserListPage.py (专用 PO) |
| 测试脚本 | ✅ test_user_list.py (12条) |
| 测试执行 | ✅ 11 passed, 1 skipped (2026-06-14) |
| CI集成 | 待配置 |
| 执行环境 | Selenium + Chrome headless |

## 自动化覆盖情况

| 优先级 | 覆盖 | 详情 |
|:---:|:---:|------|
| P0 | 2/2 (100%) | TC-001 页面加载, TC-012 新增按钮 |
| P1 | 6/6 (100%) | TC-002~005 表格/分页/搜索, TC-006 状态筛选, TC-008 翻页 |
| P2 | 3/4 (75%) | TC-009 查看, TC-010~011 批量选择; TC-007 角色筛选(P2, skip) |

## 已知限制

1. **分页组件**: 需用 JS `execute_script` 提取 `.el-pagination__total` 文本（Selenium visibility 检查失败）
2. **Button 文本**: Element Plus 渲染 button 文本含前后空白，必须用 `normalize-space()` 匹配
3. **Row action 按钮**: "查看"/"编辑" 无 span 子节点，需用 button 级别 `normalize-space()` 匹配
4. **Checkbox 响应**: 必须点击 label 元素 + dispatch change 事件才能触发 Vue v-model 更新
5. **角色筛选 (TC-007)**: 角色下拉选项动态变化，特定角色不可用时预期 skip

## 维护建议

- 页面变更时同步更新 Page Object
- 新增 button 定位器使用 `normalize-space()` 而非 `text()`
- 分页相关数据建议使用 JS 提取
- CI失败时优先检查元素定位和 Element Plus 版本变化
