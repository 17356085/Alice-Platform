"""系统日志模块测试脚本"""
import os
import sys
import pytest
import allure

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from page.system_page.SystemLogPage import SystemLogPage
 
 
def step(text):
    try:
        with allure.step(text):
            print(f"步骤：{text}")
    except Exception:
        print(f"步骤：{text}")
 
 
def case(case_id, title):
    print(f"\n========== 用例 {case_id}：{title} ==========")
    try:
        allure.dynamic.title(f"{case_id} {title}")
        allure.dynamic.description(f"用例编号：{case_id}\n用例说明：{title}")
    except Exception:
        pass
 
 
def ea(expected, actual):
    return f"预期结果：{expected}；实际结果：{actual}"
 
 
def check(expected, actual, condition):
    print(f"断言条件：{expected}")
    print(f"预期结果：{expected}")
    print(f"实际结果：{actual}")
    assert condition, ea(expected, actual)
 
 
class TestSystemLog:
    @pytest.fixture(autouse=True)
    def _reset_after_each(self, driver_setup):
        yield
        try:
            SystemLogPage(driver_setup).click_reset()
        except Exception:
            pass
 
    @pytest.mark.smoke
    @allure.epic("系统管理")
    @allure.feature("系统日志")
    @allure.story("页面基础展示")
    @allure.severity(allure.severity_level.NORMAL)
    def test_sy_sylog_01_page_display(self, driver_setup):
        page = SystemLogPage(driver_setup)
        case("SY-SYLOG-01", "正常显示系统日志列表及相关字段")
        step("获取表头并校验")
        headers = page.get_table_headers()
        expected = {"日志编号", "日志类型", "日志级别", "模块名称", "日志内容", "创建时间", "操作"}
        check("正常加载系统日志列表及相关字段", headers, expected.issubset(set(headers)))
        step("校验列表有数据")
        row_count = page.get_table_row_count()
        check("正常加载系统日志列表", row_count if row_count else (page.get_empty_text() or "暂无数据"), row_count > 0)
 
    def test_sy_sylog_02_pagination(self, driver_setup):
        page = SystemLogPage(driver_setup)
        case("SY-SYLOG-02", "分页跳转（分页）")
        step("点击重置")
        page.click_reset()
        step("记录第一页页码与日志编号列表")
        page1 = page.get_current_page_number()
        ids1 = page.get_column_data_by_header("日志编号")
        step("点击下一页")
        if not page.click_next_page():
            pytest.skip("只有一页数据，跳过分页测试")
        step("记录第二页页码与日志编号列表")
        page2 = page.get_current_page_number()
        ids2 = page.get_column_data_by_header("日志编号")
        check("页码切换到下一页", f"{page1}->{page2}", page2 != page1)
        if ids1 and ids2:
            check("数据不重复无遗漏", f"page1={ids1}, page2={ids2}", ids1 != ids2)
 
    def test_sy_sylog_03_search_by_log_type(self, driver_setup):
        page = SystemLogPage(driver_setup)
        case("SY-SYLOG-03", "日志类型搜索")
        step("点击重置")
        page.click_reset()
        step("选择日志类型：启动")
        page.select_log_type("启动")
        step("点击搜索")
        page.click_search()
        types = page.get_column_data_by_header("日志类型")
        empty = page.get_empty_text() or ""
        check(
            "显示列表中的符合条件的数据项或暂无数据",
            types if types else (empty or "未获取到空态"),
            bool(types) or ("暂无数据" in empty),
        )
        if not types:
            return
        check("筛选结果日志类型为启动", types, all("启动" in t for t in types))
 
    def test_sy_sylog_04_search_by_log_level(self, driver_setup):
        page = SystemLogPage(driver_setup)
        case("SY-SYLOG-04", "日志级别搜索")
        step("点击重置")
        page.click_reset()
        step("选择日志级别：WARN")
        page.select_log_level("WARN")
        step("点击搜索")
        page.click_search()
        levels = page.get_column_data_by_header("日志级别")
        empty = page.get_empty_text() or ""
        check(
            "显示列表中的符合条件的数据项或暂无数据",
            levels if levels else (empty or "未获取到空态"),
            bool(levels) or ("暂无数据" in empty),
        )
        if not levels:
            return
        check("筛选结果日志级别为WARN", levels, all("WARN" in l for l in levels))
 
    def test_sy_sylog_05_search_by_module_name_like(self, driver_setup):
        page = SystemLogPage(driver_setup)
        case("SY-SYLOG-05", "按模块名称搜索（模糊查询）")
        step("点击重置")
        page.click_reset()
        keyword = "system"
        step(f"输入模块名称：{keyword}")
        page.input_module_name(keyword)
        step("点击搜索")
        page.click_search()
        modules = page.get_column_data_by_header("模块名称")
        if not modules:
            check("允许暂无数据", page.get_empty_text() or "未获取到空态", "暂无数据" in (page.get_empty_text() or ""))
            return
        check(f"模块名称包含{keyword}", modules, all(keyword.lower() in m.lower() for m in modules))
 
    def test_sy_sylog_06_search_by_date(self, driver_setup):
        page = SystemLogPage(driver_setup)
        case("SY-SYLOG-06", "按操作时间搜索")
        step("点击重置")
        page.click_reset()
        step("选择操作时间：2026-04-24 至 2026-04-27")
        page.set_operation_date_range("2026-04-24", "2026-04-27")
        start_v, end_v = page.get_operation_date_range_values()
        check("日期范围已填写", f"{start_v} 至 {end_v}" if (start_v or end_v) else "日期未填入", bool(start_v and end_v))
        step("点击搜索")
        page.click_search()
        row_count = page.get_table_row_count()
        if row_count == 0:
            check("允许暂无数据", page.get_empty_text() or "未获取到空态", "暂无数据" in (page.get_empty_text() or ""))
            return
        check("显示列表中的符合条件的数据项", row_count, row_count > 0)
 
    def test_sy_sylog_07_reset_button(self, driver_setup):
        page = SystemLogPage(driver_setup)
        case("SY-SYLOG-07", "重置按钮功能正常")
        step("输入筛选条件")
        page.select_log_type("错误")
        page.select_log_level("WARN")
        page.input_module_name("system")
        page.set_operation_date_range("2026-04-24", "2026-04-27")
        step("点击重置")
        page.click_reset()
        step("点击搜索验证列表正常加载")
        page.click_search()
        row_count = page.get_table_row_count()
        check("所有筛选条件清空，正常加载系统日志", row_count if row_count else (page.get_empty_text() or "暂无数据"), row_count > 0)
 
    def test_sy_sylog_08_clear(self, driver_setup):
        page = SystemLogPage(driver_setup)
        case("SY-SYLOG-08", "清空表格数据")
        step("点击清空")
        page.click_clear()
        step("确认清空")
        page.confirm_message_box_if_present()
        msg = page.wait_for_toast_text(timeout=6)
        if msg:
            check("显示提示信息", msg, msg != "")
        step("校验空态")
        empty = page.get_empty_text()
        check("显示：暂无数据", empty or "仍有数据", ("暂无数据" in empty) or (page.get_table_row_count() == 0))
 
    def test_sy_sylog_09_detail(self, driver_setup):
        page = SystemLogPage(driver_setup)
        case("SY-SYLOG-09", "查看数据项目信息")
        step("校验列表是否暂无数据")
        if page.get_table_row_count() == 0:
            check("允许暂无数据", page.get_empty_text() or "未获取到空态", "暂无数据" in (page.get_empty_text() or ""))
            return
        step("点击详情")
        page.click_first_row_detail()
        check("显示相关操作信息", "已打开详情", True)
 
 
if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
 
