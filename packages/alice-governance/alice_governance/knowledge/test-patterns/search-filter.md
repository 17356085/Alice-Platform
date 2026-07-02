# 测试模式: 搜索与筛选

> 适用: 含 el-input + el-select 搜索区的页面 | 来源: 全模块

## 搜索场景矩阵

| 场景 | 输入 | 验证点 | 优先级 |
|------|------|--------|:--:|
| 关键词精确搜索 | 完整名称 | 返回唯一匹配 | P1 |
| 关键词模糊搜索 | 部分关键词 | 返回所有包含该词记录 | P1 |
| 无结果搜索 | 不存在名称 | 表格"暂无数据"，不报错 | P1 |
| 特殊字符搜索 | `<script>alert(1)</script>` | 无XSS弹窗，正常显示空结果 | P2 |
| 超长文本搜索 | 500字符 | 不崩溃，正常处理 | P2 |

## 下拉筛选场景

| 场景 | 操作 | 验证点 |
|------|------|--------|
| 单选筛选 | 选择下拉选项→查询 | 结果均匹配该选项 |
| 组合筛选 | 多条件同时生效 | 结果满足所有条件 |
| 重置 | 点击重置→查询 | 恢复全量数据 |
| 下拉选项动态加载 | 远程搜索→等待选项 | 选项正确渲染 |

## 自动化实现模板

```python
class TestSearchFilter:
    def test_search_by_keyword(self, page):
        page.search("关键词")
        data = page.get_table_data()
        assert len(data) > 0, "搜索结果为空"
        assert "关键词" in str(data), "结果不包含关键词"
    
    def test_filter_by_select(self, page):
        page.select_filter("类型", "选项值")
        page.click_search()
        data = page.get_column_data(col_index)
        assert all(v == "选项值" for v in data)
    
    def test_combined_filter(self, page):
        page.select_filter("类型", "值1")
        page.select_filter("状态", "值2")
        page.search("关键词")
        # 验证三条件交集
    
    def test_reset(self, page):
        page.search("xxx")
        before_reset = page.get_total_count()
        page.reset_search()
        after_reset = page.get_total_count()
        assert after_reset >= before_reset
    
    def test_search_no_result(self, page):
        page.search("ZZZZ_NOT_EXIST")
        assert page.is_table_empty() or page.get_table_row_count() == 0
```

## Element Plus 搜索区陷阱

| 陷阱 | 应对 |
|------|------|
| el-select filterable teleport | JS click降级 |
| el-date-picker 弹出层在body | 使用body级 `.el-picker-panel` |
| 远程搜索延迟渲染 | 先触发下拉→输入→等待选项出现→选择 |
| 搜索后loading遮罩未消(空数据) | 等待 `loading消失 OR 空数据提示` |
