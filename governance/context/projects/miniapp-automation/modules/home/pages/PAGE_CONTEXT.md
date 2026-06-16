# PAGE_CONTEXT — miniapp / home

> 从 home.page.js 提取 | 2026-06-11

## 页面信息

| 属性 | 值 |
|------|-----|
| 路径 | `/pages/index/index` (TabBar) |
| Page Object | `home.page.js` (extends MiniPage, IS_TAB_PAGE) |
| 测试脚本 | `tests/smoke/test_home.test.js` |

## 核心元素

| 元素 | 类型 | data key | 说明 |
|------|------|----------|------|
| 菜单分类列表 | view[] | `g` / `menuCategories` | 首页grid布局 |
| 菜单项名称 | text | `item.f` / `item.name` | 每个菜单卡片的标题 |
| 菜单图标 | image | — | 快捷入口图标 |
| 统计卡片 | view | — | 产量/库存/报警数 |
| 底部TabBar | tabBar | — | 首页/报警/审批/我的 |

## 关键交互

- 首页加载→统计卡片渲染→快捷入口grid出现
- 点击菜单项→跳转对应功能页
- 不同角色首页卡片内容差异

## 获取方法

- `getMenuCategories()`: 从 data.g 获取菜单分类
- `getAllMenuNames()`: 展开所有菜单名称列表
- `getPageText()`: 前20个 view/text 文本拼接

<!-- status: draft | phase: Phase 1 | completed_by: ai-assistant | completed_at: 2026-06-11 -->
