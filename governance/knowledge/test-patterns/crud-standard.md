# 测试模式: CRUD 标准流程

> 适用: 任何含表格+弹窗CRUD的页面 | 来源: equipment/maintenance, personnel/post, sales/*

## 必测场景 (P0)

| # | 场景 | 验证点 | 示例代码 |
|---|------|--------|----------|
| 1 | 页面加载 | 表格+搜索区+分页可见 | `navigate_to() + wait_table_loaded()` |
| 2 | 表头完整性 | 所有列标题匹配 | `get_table_headers()` vs 预期集合 |

## 新增操作 (P1)

| # | 场景 | 验证点 |
|---|------|--------|
| 3 | 弹窗打开 | 标题正确/表单字段完整 |
| 4 | 必填项校验 | 留空提交→红色错误提示+弹窗不关 |
| 5 | 格式校验 | 非法输入→对应字段错误提示 |
| 6 | 提交成功 | Toast "新增成功" + 表格刷新含新数据 |
| 7 | 取消操作 | 弹窗关闭+数据未变 |
| 8 | 唯一性校验 | 重复名称→"数据已存在" |

## 编辑操作 (P1)

| # | 场景 | 验证点 |
|---|------|--------|
| 9 | 数据回显 | 弹窗字段=表格行数据 |
| 10 | 修改保存 | Toast "修改成功" + 表格更新 |
| 11 | 取消修改 | 数据未变化 |

## 删除操作 (P0/P1)

| # | 场景 | 验证点 |
|---|------|--------|
| 12 | 确认弹窗 | "确定删除？" + 确定/取消按钮 |
| 13 | 确认删除 | Toast "删除成功" + 表格刷新 |
| 14 | 取消删除 | 数据未变化 |
| 15 | 关联数据保护 | 被引用记录→后端拒绝+Toast提示 |

## 分页 (P1)

| # | 场景 | 验证点 |
|---|------|--------|
| 16 | 翻页 | 数据变化 |
| 17 | 改变每页条数 | 行数匹配 |

## 自动化实现模板

```python
class TestCrudStandard:
    @pytest.mark.smoke
    def test_page_load(self, page): ...
    
    def test_add_required_validation(self, page): ...
    
    def test_add_submit_success(self, page): ...
    
    def test_edit_data_echo(self, page): ...
    
    def test_delete_confirm(self, page): ...
    
    def test_pagination(self, page): ...
```

## Element Plus 陷阱速查

| 陷阱 | 应对 |
|------|------|
| el-select teleport | 选项在body层，使用BasePage.select_option() |
| el-dialog多实例 | 定位器加 `not(contains(@style,'display:none'))` |
| v-if移除DOM | 操作前 `is_present()` 检查 |
| loading不消失(空数据) | 同时监听loading消失OR空数据提示 |
