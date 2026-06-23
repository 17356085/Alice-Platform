# AUTO_STRATEGY — production / monthly-report

## 1. 自动化范围
- ✅ 页面加载验证（月份导航+按钮+统计卡片+分区表格）
- ✅ 月份导航（← → 按钮 + current-month 文字变化验证）
- ✅ 生成报表按钮 disabled→enabled 切换
- ✅ 表格表头验证（最小列集）
- ✅ 趋势/导出弹窗打开+关闭
- ❌ 打印（浏览器原生对话框）
- ❌ 统计数据准确性（后端验证）

## 2. 架构设计

### Page Object 结构
```
MonthlyReportPage(BasePage)
├── 导航
│   └── navigate_to_monthly_report()
├── 月份导航
│   ├── get_current_month() → str
│   ├── click_prev_month()
│   ├── click_next_month()
│   └── navigate_to_month(year, month)
├── 操作按钮
│   ├── click_generate_report()
│   ├── click_trend()
│   ├── click_export()
│   ├── is_generate_disabled() → bool
│   └── is_print_visible() → bool
├── 统计卡片
│   ├── get_lng_monthly_output() → str
│   ├── get_lin_monthly_output() → str
│   └── get_gas_monthly_output() → str
├── 分区表格 (复用 daily-report 模式)
│   ├── get_section_table_headers(name)
│   ├── get_section_row_count(name)
│   └── is_section_visible(name)
└── 弹窗 (复用 daily-report 模式)
    ├── is_dialog_open(title)
    └── click_dialog_cancel(title)
```

### Fixture
```python
@pytest.fixture(scope="function")
def monthly_report_page(driver_setup):
    page = MonthlyReportPage(driver_setup)
    page.navigate_to_monthly_report()
    yield page
    # teardown: 关闭残留弹窗
```

### 关键策略
- **JS Click 优先**：趋势/导出按钮使用 `_js_click_by_text()`（避免叠加层拦截）
- **月份验证**：只验证月份文字是否变化，不验证格式
- **统计卡片**：只验证元素存在和内容非空，不做数值校验
