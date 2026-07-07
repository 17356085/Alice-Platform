# 页面上下文: 仓库管理

## 页面名称
仓库列表 / 仓库管理模块

## 目标用户
仓库管理员、运营人员

## 核心功能
1.  **仓库列表展示**: 分页展示所有仓库信息（仓库编码、名称、类型、状态、负责人、联系电话、创建时间）。
2.  **搜索与筛选**: 支持按仓库名称、仓库编码、仓库类型、状态进行模糊搜索和精确筛选。
3.  **新建仓库**: 点击“新建仓库”按钮，打开新增仓库表单弹窗或跳转至新建页面。
4.  **编辑仓库**: 点击列表中的“编辑”按钮，打开编辑仓库表单弹窗，预填充已有数据。
5.  **查看仓库详情**: 点击列表中的“仓库编码”或“查看详情”按钮，跳转至仓库详情页。
6.  **启用/禁用仓库**: 在列表中对仓库状态进行切换操作（可能是一个开关按钮或操作栏按钮）。
7.  **删除仓库**: 删除指定仓库，需要二次确认。

## 页面结构（DOM 层级）
- `div.main-container`
  - `div.page-header` (标题 + 面包屑)
  - `div.search-area` (搜索/筛选条件区域)
    - `input#searchName` (按名称搜索)
    - `input#searchCode` (按编码搜索)
    - `select#searchType` (按类型筛选)
    - `select#searchStatus` (按状态筛选)
    - `button#searchBtn` (搜索)
    - `button#resetBtn` (重置)
  - `div.action-bar` (操作按钮区域)
    - `button#addWarehouseBtn` (新建仓库)
  - `div.table-container`
    - `table#warehouseTable`
      - `thead`
      - `tbody`
        - `tr` (每一行包含: 复选框, 仓库编码, 名称, 类型, 状态标签, 负责人, 电话, 创建时间, 操作按钮组)
          - `td` > `a.warehouse-code` (点击跳转详情)
          - `td` > `span.warehouse-status` (状态: 启用/禁用)
          - `td` 操作按钮组:
            - `button.edit-btn` (编辑)
            - `button.toggle-status-btn` (启用/禁用)
            - `button.delete-btn` (删除)
  - `div.pagination` (分页组件)
    - `span.total-count`
    - `ul.pagination-list` > `li`
    - ...

## 路由
- 列表页: `/warehouse/list`
- 新建页: `/warehouse/create` (或 `/warehouse/create?type=modal`)
- 编辑页: `/warehouse/:id/edit` (或 `/warehouse/edit/:id`)
- 详情页: `/warehouse/:id`

## 接口
- `GET /api/warehouses` (分页列表)
- `POST /api/warehouses` (新增)
- `PUT /api/warehouses/:id` (编辑)
- `GET /api/warehouses/:id` (详情)
- `PATCH /api/warehouses/:id/status` (启用/禁用)
- `DELETE /api/warehouses/:id` (删除)