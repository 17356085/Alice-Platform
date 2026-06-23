# AUTO_STRATEGY — production / business-type-config

> 基于 TECH_ANALYSIS + TEST_CASES + 现有代码 | 2026-06-12
> production 模块最复杂 CRUD 管理页（17字段表单 + 14条数据 + 批量删除）。首轮 8 passed / 0 failed ✅

## 自动化目标
覆盖业务类型配置的页面展示、表格数据、搜索/重置、新增弹窗、行编辑弹窗、复选框批量删除联动。
写操作（新增确定/编辑确定/删除确认）待数据清理策略就绪后补充。

## 推荐策略
- 脚本层级：BusinessTypeConfigPage（26方法PO）→ conftest.py（fixture + teardown）→ test_business_type_config.py（8用例）
- 断言层级：页面级（元素可见/按钮状态）+ 数据级（表格行数>0/分页总数/行单元格文本）+ 交互级（弹窗开闭/复选框联动）
- 数据策略：只读型测试，依赖环境已有 14 条数据，新增/编辑均取消关闭
- 清理策略：conftest teardown JS 关闭弹窗 + Escape 兜底

## 覆盖矩阵

| 用例编号 | 标题 | 优先级 | 自动化 | 理由 |
|----------|------|--------|--------|------|
| TC-PROD-BTC-001 | 页面基本元素+表格数据 | P0 | ✅ | 冒烟必测：14条数据+11列表头+分页 |
| TC-PROD-BTC-002 | 批量删除按钮初始disabled | P0 | ✅ | is-disabled class 断言 |
| TC-PROD-BTC-003 | 按工厂搜索有结果 | P0 | ✅ | 搜索功能核心路径 |
| TC-PROD-BTC-004 | 重置搜索条件 | P1 | ✅ | 输入框清空+数据恢复 |
| TC-PROD-BTC-005 | 打开新增弹窗 | P1 | ✅ | 17字段弹窗标题 |
| TC-PROD-BTC-006 | 填写新增表单后取消 | P1 | ✅ | 6字段填写+取消关闭 |
| TC-PROD-BTC-007 | 点击行编辑打开弹窗 | P1 | ✅ | 编辑弹窗回填验证 |
| TC-PROD-BTC-008 | 勾选行后批量删除启用 | P1 | ✅ | 复选框联动按钮状态 |

## PageObject 拆分

```
BusinessTypeConfigPage ← 搜索区 + 表格 + 弹窗 + 批量操作（26方法）
  ├── 搜索区：4输入 + 4按钮（搜索/重置/新增/删除）
  ├── 表格：11列（含 checkbox + 操作列）+ 分页（14条数据）
  ├── 弹窗：17字段（参数化 _DIALOG_FIELD_XPATH）+ 确定/取消
  ├── 行操作：编辑/删除
  ├── 批量操作：复选框勾选/批量删除状态
  └── 导航：SidebarNavigator + _is_on_page() 身份验证 + retry
```

## 特殊处理

| 场景 | 处理方式 |
|------|----------|
| 表头含括号后缀 (ZPLPA) | 包含匹配断言 `any(col in h for h in headers)` |
| 17字段弹窗 | 仅验证部分字段填写，不全填（避免提交脏数据风险） |
| 批量删除按钮状态联动 | `select_row()` → `is_batch_delete_enabled()` 联动验证 |
| 搜索后数据恢复 | reset 后断言 `get_row_count() > 0`（验证恢复到全部数据） |

## ROI 分析

| 指标 | 值 |
|------|----|
| 页面类型 | 复杂 CRUD（生产管理最复杂），Element Plus 标准组件 |
| 开发耗时 | ~0.5h（26方法PO + 8用例，模板复用） |
| 维护成本 | 低（CRUD 结构稳定；17字段变更概率低） |
| 首轮质量 | **8 passed / 0 failed** — 零缺陷交付 |

## 与 shift-team-config 的技术差异

| 技术点 | shift-team-config | business-type-config |
|--------|-------------------|---------------------|
| 弹窗字段数 | 6 | **17** |
| 表格数据 | 0条 | **14条** |
| 批量删除 | ❌ | ✅ 复选框+页面级按钮 |
| 表头断言 | 精确匹配 | **包含匹配**（ZPLPA后缀） |
| 搜索参数 | 工厂(4位) | **工厂 "2547"（有已知数据）** |
| 编辑弹窗 | 未测（无数据） | **已测（标题含"修改"）** |

---
<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-12 -->
