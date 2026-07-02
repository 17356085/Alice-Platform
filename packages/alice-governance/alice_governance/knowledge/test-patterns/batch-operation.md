# 测试模式: 批量操作

> 适用: 含批量删除/导入/导出/状态切换的页面 | 来源: personnel/question, equipment/*

## 批量删除

| # | 场景 | 操作 | 验证点 |
|---|------|------|--------|
| 1 | 未勾选-按钮disabled | 查看删除按钮 | `is-disabled` class存在 |
| 2 | 全选-批量删除 | 勾选全部→删除→确认 | Toast "删除成功"+表格刷新+选中数据消失 |
| 3 | 部分勾选-删除 | 勾选3条→删除 | 仅删除选中3条 |
| 4 | 取消批量删除 | 勾选→删除→取消 | 数据未变化 |
| 5 | 跨页勾选 | 翻页勾选→删除 | 所有选中页的数据被删除 |

## 批量导入

| # | 场景 | 操作 | 验证点 |
|---|------|------|--------|
| 6 | 正常导入 | 上传合法文件 | Toast "导入成功"+N条 |
| 7 | 空文件导入 | 上传空文件 | 错误提示 |
| 8 | 格式错误 | 上传错误格式 | 行级错误报告 |
| 9 | 部分错误 | 含错误行的文件 | 正确行导入+错误行报告 |
| 10 | 重复数据 | 导入已存在数据 | 跳过/覆盖提示 |

## 批量导出

| # | 场景 | 操作 | 验证点 |
|---|------|------|--------|
| 11 | 导出全部 | 点击导出 | 文件下载+N条 |
| 12 | 筛选后导出 | 搜索后导出 | 仅导出筛选结果 |

## 自动化实现

```python
class TestBatchOperation:
    def test_delete_disabled_no_select(self, page):
        assert "is-disabled" in page.get_attribute(page.DELETE_BTN, "class")
    
    def test_delete_selected(self, page, cleanup_tracker):
        page.select_rows([0, 1, 2])
        page.click_batch_delete()
        page.confirm_message_box()
        assert "删除成功" in page.get_toast()
    
    def test_import_valid_file(self, page, cleanup_tracker):
        page.click_import()
        page.upload_file("/data/import_valid.xlsx")
        page.click_confirm()
        assert "导入成功" in page.get_toast()
```

## 注意事项

- 批量删除后必须清理测试数据（CleanupTracker注册）
- 导入文件放在 `data/` 目录，路径使用绝对路径
- 批量操作可能较慢，WebDriverWait 设 30s+
- 并行测试时批量操作必须串行（`-m destructive`）
