# PAGE_CONTEXT — system / dict-management

## 基本信息
- 页面ID：dict-management
- 页面名称：字典管理
- 所属模块：系统管理（system）
- 页面入口：左侧菜单 → 系统管理 → 字典管理
- 路由：#/system/dict

## 页面职责
- 左侧字典分类面板（树形/列表）+ 右侧字典明细表格
- 支持字典分类的新增/编辑/删除（左侧面板）
- 支持字典明细的搜索、新增、编辑、删除（右侧表格）
- 按分类筛选（全部/系统/自定义）和分类搜索

## 核心元素
| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
|--------|----------|----------|----------|------|
| tab-dict | 字典标签页 | el-tabs__item | 顶部 | 默认激活 |
| tab-dict-category | 字典分类标签页 | el-tabs__item | 顶部 | |
| category-filter-all | 全部分类筛选 | el-radio-button | 左侧面板 | |
| category-filter-system | 系统分类筛选 | el-radio-button | 左侧面板 | |
| category-filter-custom | 自定义分类筛选 | el-radio-button | 左侧面板 | |
| category-search | 字典分类搜索 | el-input | 左侧面板 | placeholder="搜索字典分类" |
| category-add-btn | 新增分类按钮 | el-button | 左侧面板 | |
| category-list | 字典分类列表 | div列表 | 左侧面板 | 点击切换右侧明细 |
| search-input | 字典标签搜索框 | el-input | 右侧搜索区 | placeholder含"字典标签" |
| search-status | 状态下拉 | el-select | 右侧搜索区 | |
| search-btn | 搜索按钮 | el-button | 右侧搜索区 | |
| reset-btn | 重置按钮 | el-button | 右侧搜索区 | |
| add-btn | 新增按钮 | el-button | 右侧工具栏 | |
| export-btn | 导出按钮 | el-button | 右侧工具栏 | |
| table | 字典明细表格 | el-table | 右侧表格区 | 标签/键值/状态/备注/操作 |
| dialog | 新增/编辑弹窗 | el-dialog | 弹窗 | 含标签/键值/状态/备注/排序 |
| pagination | 分页器 | el-pagination | 底部 | |

## 关键交互
- 左侧点击分类 → 右侧表格异步加载该分类下的字典明细
- 分类筛选(全部/系统/自定义) → 左侧列表过滤
- 新增分类 → 弹窗 → 填写 → 确认 → 左侧列表刷新
- 新增字典 → 弹窗 → 填写 → 确认 → 表格刷新 + toast
- 删除字典 → 确认弹窗 → 确认 → 记录消失 + toast
- 搜索 → 当前分类下表格刷新

## 权限与角色
- 可见角色：admin、系统管理员
- 可操作角色：admin(全部)、系统管理员(新增/编辑字典明细)
- 特殊限制：系统分类不可删除；系统字典不可删除

## 特殊行为
- 异步加载：切换分类时右侧表格异步刷新
- 动态渲染：状态列 el-tag 颜色
- 前端校验：标签必填≤50字符；键值必填
- 后端校验：标签唯一性(同类下)；系统字典受保护不可删除

## 依赖
- 接口：GET/POST/PUT/DELETE /api/system/dict/*
- 上下游页面：下游-参数设置(参数引用字典值)
