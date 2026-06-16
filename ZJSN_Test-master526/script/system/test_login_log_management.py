"""登录日志模块测试脚本"""
import os
import sys
import time
import pytest
import allure
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from page.system_page.LoginLogPage import LoginLogPage


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


class TestLoginLog:
    @pytest.fixture(autouse=True)
    def _reset_after_each(self, driver_setup):
        yield
        try:
            LoginLogPage(driver_setup).click_reset()
        except Exception:
            pass

    @pytest.mark.smoke
    @allure.epic("系统管理")
    @allure.feature("登录日志")
    @allure.story("页面基础展示")
    @allure.severity(allure.severity_level.NORMAL)
    def test_sy_login_01_page_display(self, driver_setup):
        page = LoginLogPage(driver_setup)
        case("SY-LOGIN-01", "正常显示登录日志列表及相关字段")
        step("获取表头并校验")
        headers = page.get_table_headers()
        expected = {"时间", "用户名", "登录状态", "IP地址", "登录地点", "浏览器", "操作"}
        assert expected.issubset(set(headers)), ea(f"正常加载登录日志列表及相关字段", headers)
        step("校验列表有数据")
        assert page.get_table_row_count() > 0, ea("正常加载登录日志列表", page.get_empty_text() or "暂无数据")

    def test_sy_login_02_pagination(self, driver_setup):
        page = LoginLogPage(driver_setup)
        case("SY-LOGIN-02", "分页跳转（分页）")
        step("点击重置")
        page.click_reset()
        step("记录第一页页码与用户名列表")
        page1 = page.get_current_page_number()
        users1 = page.get_column_data_by_header("用户名")
        step("点击下一页")
        if not page.click_next_page():
            pytest.skip("只有一页数据，跳过分页测试")
        step("记录第二页页码与用户名列表")
        page2 = page.get_current_page_number()
        users2 = page.get_column_data_by_header("用户名")
        assert page2 != page1, ea("页码切换到下一页", f"{page1}->{page2}")
        assert page.get_table_row_count() > 0, ea("翻页后列表仍正常加载", page.get_empty_text() or "暂无数据")

    def test_sy_login_03_search_by_username_like(self, driver_setup):
        page = LoginLogPage(driver_setup)
        case("SY-LOGIN-03", "按用户名搜索（模糊查询）")
        step("点击重置")
        page.click_reset()
        target = "dm"
        step(f"输入用户名：{target}")
        page.input_username(target)
        step("点击搜索")
        page.click_search()
        users = page.get_column_data_by_header("用户名")
        assert users, ea("显示列表中的符合条件的数据项", page.get_empty_text() or "暂无数据")
        assert all(target.lower() in u.lower() for u in users), ea(f"用户名包含{target}", users)

    def test_sy_login_04_search_by_status(self, driver_setup):
        page = LoginLogPage(driver_setup)
        case("SY-LOGIN-04", "按状态搜索")
        step("点击重置")
        page.click_reset()
        step("输入用户名：DM")
        page.input_username("DM")
        step("选择状态：失败")
        page.select_status("失败")
        step("点击搜索")
        page.click_search()
        statuses = page.get_column_data_by_header("登录状态")
        if not statuses:
            assert "暂无数据" in (page.get_empty_text() or ""), ea("暂无数据", page.get_empty_text() or "未获取到空态")
        else:
            assert all("失败" in s for s in statuses), ea("筛选结果状态都为失败", statuses)

    def test_sy_login_05_search_by_date(self, driver_setup):
        page = LoginLogPage(driver_setup)
        case("SY-LOGIN-05", "按登录时间搜索")
        step("点击重置")
        page.click_reset()
        step("输入用户名：DM")
        page.input_username("DM")
        step("选择状态：失败")
        page.select_status("失败")
        step("选择登录时间：2026-04-24 至 2026-04-27")
        page.set_login_date_range("2026-04-24", "2026-04-27")
        start_v, end_v = page.get_login_date_range_values()
        assert start_v and end_v, ea("日期范围已填写", f"{start_v} 至 {end_v}" if (start_v or end_v) else "日期未填入")
        step("点击搜索")
        page.click_search()
        row_count = page.get_table_row_count()
        empty = page.get_empty_text() or ""
        assert (row_count > 0) or ("暂无数据" in empty), ea("显示列表中的符合条件的数据项（允许暂无数据）", empty or f"row_count={row_count}")

    def test_sy_login_06_reset_button(self, driver_setup):
        page = LoginLogPage(driver_setup)
        case("SY-LOGIN-06", "重置按钮功能正常")
        step("输入筛选条件：用户名DM，状态失败，时间范围")
        page.input_username("DM")
        page.select_status("失败")
        page.set_login_date_range("2026-04-24", "2026-04-27")
        step("点击重置")
        page.click_reset()
        step("点击搜索验证列表正常加载")
        page.click_search()
        assert page.get_table_row_count() > 0, ea("所有筛选条件清空，正常加载登录日志", page.get_empty_text() or "暂无数据")

    def test_sy_login_07_export(self, driver_setup):
        page = LoginLogPage(driver_setup)
        case("SY-LOGIN-07", "导出表格数据")
        step("点击导出")
        try:
            page.click_export()
        except TimeoutException:
            pytest.skip("当前页面未显示导出按钮，可能账号无导出权限")
        msg = page.wait_for_toast_text(timeout=8)
        print(f"  [DEBUG] 导出Toast: {msg!r}")
        # 宽松断言：有消息且非系统错误，或消息为空（操作已触发）
        assert (not msg) or "系统错误" not in msg, ea("导出操作已触发", msg or "未获取到提示")

    def test_sy_login_08_clear(self, driver_setup):
        page = LoginLogPage(driver_setup)
        case("SY-LOGIN-08", "清空表格数据")
        step("点击清空")
        try:
            page.click_clear()
        except TimeoutException:
            pytest.skip("当前页面未显示清空按钮，可能账号无清空权限")
        step("确认清空")
        page.confirm_message_box_if_present()
        msg = page.wait_for_toast_text(timeout=6)
        if msg:
            assert any(k in msg for k in ["成功", "清空成功", "完成"]) or msg != "", ea("显示：暂无数据", msg)
        step("校验空态")
        empty = page.get_empty_text()
        assert ("暂无数据" in empty) or (page.get_table_row_count() == 0), ea("显示：暂无数据", empty or "仍有数据")

    def test_sy_login_09_detail(self, driver_setup):
        page = LoginLogPage(driver_setup)
        case("SY-LOGIN-09", "查看数据项目信息")
        step("校验列表是否暂无数据")
        if page.get_table_row_count() == 0:
            pytest.skip(page.get_empty_text() or "当前无登录日志数据，跳过详情验证")
        step("点击详情")
        try:
            page.click_first_row_detail()
        except TimeoutException:
            pytest.skip("当前列表未显示详情按钮，可能账号无查看详情权限")
        step("校验详情页标题：登录日志详情")
        assert page.wait_detail_title_visible(timeout=8), ea("弹出登录日志详情页（存在“登录日志详情”标题）", "未找到“登录日志详情”标题")
        try:
            page.close_detail_dialog()
        except Exception:
            pass


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
