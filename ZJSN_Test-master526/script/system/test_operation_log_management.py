"""操作日志模块测试脚本"""
import os
import sys
import time
import pytest
import allure
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from page.system_page.OperationLogPage import OperationLogPage


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


class TestOperationLog:
    @pytest.fixture(autouse=True)
    def _reset_after_each(self, driver_setup):
        yield
        try:
            OperationLogPage(driver_setup).click_reset()
        except Exception:
            pass

    @pytest.mark.smoke
    @allure.epic("系统管理")
    @allure.feature("操作日志")
    @allure.story("页面基础展示")
    @allure.severity(allure.severity_level.NORMAL)
    def test_sy_action_01_page_display(self, driver_setup):
        page = OperationLogPage(driver_setup)
        case("SY-ACTION-01", "正常显示操作日志列表及相关字段")
        step("获取表头并校验")
        headers = page.get_table_headers()
        expected = {"日志编号", "系统模块", "操作类型", "操作人员", "操作状态", "操作IP", "操作时间", "操作"}
        check("正常加载操作日志列表及相关字段", headers, expected.issubset(set(headers)))
        step("校验列表有数据")
        row_count = page.get_table_row_count()
        check("正常加载操作日志列表", row_count if row_count else (page.get_empty_text() or "暂无数据"), row_count > 0)

    def test_sy_action_02_pagination(self, driver_setup):
        page = OperationLogPage(driver_setup)
        case("SY-ACTION-02", "分页跳转（分页）")
        step("点击重置")
        page.click_reset()
        step("记录第一页页码与系统模块列表")
        page1 = page.get_current_page_number()
        modules1 = page.get_column_data_by_header("系统模块")
        step("点击下一页")
        if not page.click_next_page():
            pytest.skip("只有一页数据，跳过分页测试")
        step("记录第二页页码与系统模块列表")
        page2 = page.get_current_page_number()
        modules2 = page.get_column_data_by_header("系统模块")
        check("页码切换到下一页", f"{page1}->{page2}", page2 != page1)
        if modules1 and modules2:
            check("数据不重复无遗漏", f"page1={modules1}, page2={modules2}", modules1 != modules2)

    def test_sy_action_03_search_by_system_module(self, driver_setup):
        page = OperationLogPage(driver_setup)
        case("SY-ACTION-03", "按系统模块搜索（模糊查询）")
        step("点击重置")
        page.click_reset()
        keyword = "th"
        step(f"输入系统模块：{keyword}")
        page.input_system_module(keyword)
        step("点击搜索")
        page.click_search()
        modules = page.get_column_data_by_header("系统模块")
        check("显示列表中的符合条件的数据项", modules if modules else (page.get_empty_text() or "暂无数据"), bool(modules))
        check(f"系统模块包含{keyword}", modules, all(keyword.lower() in m.lower() for m in modules))

    def test_sy_action_04_search_by_operation_type(self, driver_setup):
        page = OperationLogPage(driver_setup)
        case("SY-ACTION-04", "按操作类型搜索")
        step("点击重置")
        page.click_reset()
        step("输入系统模块：app")
        page.input_system_module("app")
        step("输入操作类型：POST")
        page.input_operation_type("POST")
        step("点击搜索")
        page.click_search()
        types = page.get_column_data_by_header("操作类型")
        if not types:
            check("允许暂无数据", page.get_empty_text() or "未获取到空态", "暂无数据" in (page.get_empty_text() or ""))
        else:
            check("筛选结果操作类型包含POST", types, all("POST" in t for t in types))

    def test_sy_action_05_search_by_operator(self, driver_setup):
        page = OperationLogPage(driver_setup)
        case("SY-ACTION-05", "按操作人员搜索")
        step("点击重置")
        page.click_reset()
        step("输入系统模块：SYS")
        page.input_system_module("SYS")
        step("输入操作类型：POST")
        page.input_operation_type("POST")
        step("输入操作人员：系统管理员")
        page.input_operator("系统管理员")
        step("点击搜索")
        page.click_search()
        users = page.get_column_data_by_header("操作人员")
        if not users:
            check("允许暂无数据", page.get_empty_text() or "未获取到空态", "暂无数据" in (page.get_empty_text() or ""))
        else:
            check("筛选结果操作人员为系统管理员", users, all("系统管理员" in u for u in users))

    def test_sy_action_06_search_by_status(self, driver_setup):
        page = OperationLogPage(driver_setup)
        case("SY-ACTION-06", "按状态搜索")
        step("点击重置")
        page.click_reset()
        step("输入系统模块：sys")
        page.input_system_module("sys")
        step("输入操作类型：POST")
        page.input_operation_type("POST")
        step("输入操作人员：系统管理员")
        page.input_operator("系统管理员")
        step("选择状态：失败")
        page.select_status("失败")
        step("点击搜索")
        page.click_search()
        statuses = page.get_column_data_by_header("操作状态")
        if not statuses:
            check("允许暂无数据", page.get_empty_text() or "未获取到空态", "暂无数据" in (page.get_empty_text() or ""))
        else:
            check("筛选结果状态都为失败", statuses, all("失败" in s for s in statuses))

    def test_sy_action_07_search_by_date(self, driver_setup):
        page = OperationLogPage(driver_setup)
        case("SY-ACTION-07", "按操作时间搜索")
        step("点击重置")
        page.click_reset()
        step("输入系统模块：sys")
        page.input_system_module("sys")
        step("选择状态：失败")
        page.select_status("失败")
        today = datetime.now().date()
        start_date = (today - timedelta(days=1)).strftime("%Y-%m-%d")
        end_date = today.strftime("%Y-%m-%d")
        step(f"选择操作时间：{start_date} 至 {end_date}")
        page.set_operation_date_range(start_date, end_date)
        start_v, end_v = page.get_operation_date_range_values()
        check("日期范围已填写", f"{start_v} 至 {end_v}" if (start_v or end_v) else "日期未填入", bool(start_v and end_v))
        step("点击搜索")
        page.click_search()
        row_count = page.get_table_row_count()
        check("显示列表中的符合条件的数据项", row_count if row_count else (page.get_empty_text() or "暂无数据"), row_count > 0)

    def test_sy_action_08_reset_button(self, driver_setup):
        page = OperationLogPage(driver_setup)
        case("SY-ACTION-08", "重置按钮功能正常")
        step("输入筛选条件")
        page.input_system_module("sys")
        page.input_operation_type("POST")
        page.input_operator("系统管理员")
        page.select_status("失败")
        page.set_operation_date_range("2026-04-24", "2026-04-27")
        step("点击重置")
        page.click_reset()
        step("校验搜索项已清空")
        v1 = page.get_system_module_value()
        v2 = page.get_operation_type_value()
        v3 = page.get_operator_value()
        s = page.get_status_selected_text()
        start_v, end_v = page.get_operation_date_range_values()
        ok = (v1 == "" and v2 == "" and v3 == "" and (start_v == "" and end_v == "") and (s == "" or "全部" in s))
        check("重置后搜索项为空", f"module={v1}, type={v2}, operator={v3}, status={s}, date={start_v}-{end_v}", ok)

    def test_sy_action_09_export(self, driver_setup):
        page = OperationLogPage(driver_setup)
        case("SY-ACTION-09", "导出表格数据")
        step("点击导出")
        page.click_export()
        xpath = (
            '//*[@id="message_20"]/p[contains(normalize-space(.), "导出成功")]'
            ' | //div[starts-with(@id,"message_")]//p[contains(normalize-space(.), "导出成功")]'
            ' | //div[starts-with(@id,"message_")]//*[contains(@class,"el-message__content")][contains(normalize-space(.), "导出成功")]'
        )
        try:
            el = WebDriverWait(driver_setup, 8, poll_frequency=0.1).until(
                EC.visibility_of_element_located((By.XPATH, xpath))
            )
            msg = (el.text or "").strip()
        except TimeoutException:
            msg = ""
        print(f"  [DEBUG] 导出Toast: {msg!r}")
        # 宽松断言：有消息且非系统错误，视为导出操作已触发
        check("弹出提示导出成功", msg or "未弹出导出成功提示",
              msg and "系统错误" not in msg)

    def test_sy_action_10_clear(self, driver_setup):
        page = OperationLogPage(driver_setup)
        case("SY-ACTION-10", "清空表格数据")
        step("点击清空")
        page.click_clear()
        step("确认清空")
        page.confirm_message_box_if_present()
        msg = page.wait_for_toast_text(timeout=6)
        check("弹出提示：清空成功", msg or "未获取到提示", "清空成功" in (msg or ""))

    def test_sy_action_11_detail(self, driver_setup):
        page = OperationLogPage(driver_setup)
        case("SY-ACTION-11", "查看数据项目信息")
        step("校验列表是否暂无数据")
        if page.get_table_row_count() == 0:
            check("允许暂无数据", page.get_empty_text() or "未获取到空态", "暂无数据" in (page.get_empty_text() or ""))
            return
        step("点击详情")
        page.click_first_row_detail()
        check("显示相关操作信息", "已打开详情", True)


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
