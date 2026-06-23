# TECH_ANALYSIS — lab（化验室取样，6页面）

> 定位策略 + 组件类型 + 已解决问题 | 2026-06-12 | 32P/0F

## 一、页面技术特征矩阵

| 页面 | UI框架 | 表格类型 | 搜索表单 | 弹窗 | 特殊组件 |
| --- | :---: | :---: | :---: | :---: | --- |
| gas-analysis-report | Element Plus | el-table | ✅ 日期 | ✅ dialog | 自定义Tab标签栏 |
| gas-compare | Element Plus | 自定义table | ✅ 日期+select | ❌ | — |
| gas-indicator | Element Plus | el-table | ❌ | ❌ | — |
| water-report | Element Plus | 自定义report-table | ✅ 日期+select | ✅ dialog | 自定义Tab标签栏 |
| water-compare | Element Plus | 自定义table | ✅ 日期+select | ❌ | — |
| water-indicator | Element Plus | el-table | ❌ | ❌ | — |

## 二、定位策略矩阵

| 场景 | 策略 | 示例 |
| --- | :---: | --- |
| **按钮点击** | JS `arguments[0]` 传参 | `execute_script('...indexOf(arguments[0])...', '查询')` |
| **弹窗检测** | CSS Selector | `.el-dialog:not([style*="display: none"])` |
| **表格行数** | 多选择器降级 | `table tbody tr, .report-table tbody tr` |
| **日期输入** | CSS placeholder | `input[placeholder*="开始日期"]` |
| **标签切换** | JS 遍历+textContent | `querySelectorAll('[class*="tab"]')` |

## 三、已解决的技术问题

| # | 问题 | 根因 | 解决方案 |
|:---:|------|------|------|
| 1 | `_js()` JS语法错误 | 字符串拼接中文字符 → `missing )` | `arguments[0]` 传参 |
| 2 | `switch_location()` JS语法错误 | CSS选择器双引号冲突 `[class*="tab"]` | 单引号+`arguments[0]` |
| 3 | `_wait_page_ready` 缺失 | PO未实现测试调用的方法 | 别名方法到所有PO |
| 4 | `search_compare` 签名不匹配 | 参数(start,end) vs 测试(pos1,pos2) | 重写为双位置选择 |
| 5 | session fixture 竞态 | session级driver跨文件状态不一致 | function级fixture |

## 四、安全代码模式

```python
# ✅ JS 点击 — arguments[0] 传参
def _js_click(self, text):
    self.driver.execute_script("""
        var btns = document.querySelectorAll('button');
        for (var i = 0; i < btns.length; i++) {
            if ((btns[i].textContent || '').trim().indexOf(arguments[0]) !== -1) {
                btns[i].click(); return;
            }
        }
    """, text)

# ✅ 多容器表格行数
def get_row_count(self):
    rows = self.driver.find_elements(By.CSS_SELECTOR,
        'table tbody tr, .report-table tbody tr')
    return sum(1 for r in rows if r.is_displayed())

# ✅ gas/water 共用PO
ROUTES = {'gas': '#/lab/gas/indicator', 'water': '#/lab/water/indicator'}
```
