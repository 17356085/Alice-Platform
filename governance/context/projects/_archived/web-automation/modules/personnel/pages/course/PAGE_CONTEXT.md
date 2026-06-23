# PAGE_CONTEXT — personnel / course

## 基本信息
- 页面ID：personnel-course
- 页面名称：课程管理
- 所属模块：人员管理（personnel）→ 培训管理
- 路由：`#/personnel/training/course`
- 自动化代码：`page/personnel_page/CourseManagePage.py` + `script/personnel/test_course_management.py`

## 页面职责
培训课程的 CRUD 管理。支持课程基本信息维护、课程分类、课程封面上传。

## 核心元素（从代码推断）
- 搜索区：课程名称输入 + 课程分类下拉 + 搜索/重置按钮
- 表格区：课程列表（名称/分类/讲师/时长/状态）
- 操作按钮：新增 / 行内编辑 / 删除
- 弹窗：新增/编辑表单（课程名称/分类/讲师/时长/封面图上传/描述）
- 分页区：分页器

## 关键交互
- 新增课程→弹窗→填写→上传封面→提交→表格刷新
- 编辑→弹窗→修改→保存→表格刷新
- 搜索→异步刷新

## 权限与角色
- 可见角色：admin、培训管理员
- 可操作角色：admin、培训管理员

## 特殊行为（待确认）
- 异步加载：表格 + 分类下拉异步
- 文件上传：封面图上传（el-upload）
- 前端校验：名称必填、分类必选

## 依赖
- 接口：课程 CRUD + 文件上传接口
- 上下游页面：培训计划（plan，关联课程）
