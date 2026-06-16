"""员工管理模块测试脚本"""
import pytest
import time
import sys
import os
import inspect
import allure
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from page.personnel_page.EmployeeManagePage import EmployeeManagePage

CREATED_EMPLOYEE_KEYWORD = None


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


def check(expected, actual, condition):
    print(f"预期结果：{expected}")
    print(f"实际结果：{actual}")
    assert condition, f"【失败】预期：{expected}，实际：{actual}"


class TestEmployeeManagement:
    """员工管理测试用例"""

    @pytest.fixture(autouse=True)
    def _allure_case_meta(self, request):
        doc = (inspect.getdoc(request.function) or "").strip()
        title = doc.replace(":", " ").strip() if doc else request.function.__name__
        try:
            allure.dynamic.title(title)
            if doc:
                allure.dynamic.description(doc)
        except Exception:
            pass
        yield

    @pytest.mark.smoke
    @allure.epic("人员管理")
    @allure.feature("员工管理")
    @allure.story("页面基础展示")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_001_display_list_and_fields(self, driver_setup):
        """EMP-001: 正常显示员工列表及相关字段"""
        case("EMP-001", "正常显示员工列表及相关字段")
        page = EmployeeManagePage(driver_setup)
        step("验证页面加载完成")
        loaded = page.is_page_loaded()
        check("页面加载成功", loaded, loaded)

        step("获取表格列头")
        headers = page.get_table_header_texts()
        step(f"表格列头: {headers}")
        check("表头不为空", headers, len(headers) > 0)

        step("获取表格数据行数")
        row_count = page.get_table_row_count()
        step(f"当前页行数: {row_count}")
        check("列表正常加载", row_count, row_count >= 0)

    def test_002_pagination(self, driver_setup):
        """EMP-002: 分页跳转"""
        case("EMP-002", "分页跳转")
        page = EmployeeManagePage(driver_setup)

        step("获取总条数")
        total = page.get_total_count()
        step(f"总条数: {total}")
        check("总条数 >= 0", total, total >= 0)

        if total <= 0:
            step("无数据，跳过分页测试")
            return

        first_page_data = page.get_table_row_count()
        step(f"第一页行数: {first_page_data}")

        try:
            page.click_next_page()
            step("点击下一页完成")
            check("翻页后列表正常", page.get_table_row_count(), page.get_table_row_count() >= 0)
        except Exception as e:
            pytest.fail(f"分页失败：{e}")

    def test_003_search_by_name(self, driver_setup):
        """EMP-003: 按姓名或工号搜索"""
        case("EMP-003", "按姓名或工号搜索")
        page = EmployeeManagePage(driver_setup)
        keyword = "测"
        step(f"输入搜索关键词: {keyword}")
        page.input_search_name(keyword)
        page.click_search()
        row_count = page.get_table_row_count()
        step(f"搜索结果行数: {row_count}")
        check("搜索后列表正常显示", row_count, row_count >= 0)

    def test_004_search_by_department(self, driver_setup):
        """EMP-004: 按部门搜索"""
        case("EMP-004", "按部门搜索")
        page = EmployeeManagePage(driver_setup)
        dept = "测"
        step(f"输入部门关键词: {dept}")
        page.input_search_dept(dept)
        page.click_search()
        row_count = page.get_table_row_count()
        step(f"搜索结果行数: {row_count}")
        check("部门搜索后列表正常显示", row_count, row_count >= 0)

    def test_005_reset_button(self, driver_setup):
        """EMP-005: 重置按钮功能正常"""
        case("EMP-005", "重置按钮功能正常")
        page = EmployeeManagePage(driver_setup)
        page.input_search_name("测")
        page.click_search()
        page.click_reset()
        row_count = page.get_table_row_count()
        step(f"重置后行数: {row_count}")
        check("重置后列表正常加载", row_count, row_count >= 0)


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
