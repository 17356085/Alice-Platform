# PAGE_CONTEXT — personnel / employee

## 基本信息
- 页面ID：personnel-employee
- 页面名称：员工管理
- 所属模块：人员管理（personnel）
- 路由：`#/personnel/employee`
- 自动化代码：`page/personnel_page/EmployeeManagePage.py` + `script/personnel/test_employee_management.py`

## 页面职责
员工档案的查询与管理。支持按姓名/工号/部门等条件搜索，查看员工基本信息。

## 核心元素（从代码推断）
- 搜索区：员工姓名/工号输入 + 部门下拉 + 搜索/重置按钮
- 表格区：员工列表（工号/姓名/部门/岗位/联系方式）
- 操作按钮：查看详情、编辑（如有权限）
- 分页区：分页器

## 关键交互
- 搜索→表格异步刷新
- 点击查看→跳转员工详情

## 权限与角色
- 可见角色：admin、部门主管、培训管理员
- 可操作角色：admin（编辑）、部门主管（本部门编辑）

## 特殊行为（待确认）
- 异步加载：表格异步 + loading
- 动态渲染：部门下拉选项根据登录用户权限过滤

## 依赖
- 接口：员工列表查询接口
- 上下游页面：岗位管理（post）
