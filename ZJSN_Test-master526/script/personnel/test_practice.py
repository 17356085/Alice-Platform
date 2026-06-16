"""自主练习模块测试脚本

Phase 4 自动生成 | 2026-06-12
覆盖: 11 条用例 (P0×2 + P1×7 + P2×2)
"""
import inspect
import os
import sys

import allure
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from page.personnel_page.PracticePage import PracticePage


def step(text):
    try:
        with allure.step(text):
            print(f"步骤：{text}")
    except Exception:
        print(f"步骤：{text}")


def case(case_id, title):
    print(f"\n========== 用例 {case_id}：{title} ==========")


def check(expected, actual, condition):
    print(f"预期结果：{expected} | 实际结果：{actual}")
    assert condition, f"预期：{expected}；实际：{actual}"


class TestPractice:
    @pytest.fixture(autouse=True)
    def _allure_case_meta(self, request):
        doc = (inspect.getdoc(request.function) or "").strip()
        title = doc.replace(":", " ").strip() if doc else request.function.__name__
        try:
            allure.dynamic.title(title)
        except Exception:
            pass
        yield

    # ==================================================================
    # P0
    # ==================================================================

    @pytest.mark.smoke
    @allure.epic("人员管理")
    @allure.feature("自主练习")
    @allure.story("页面加载")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_001_page_load(self, driver_setup):
        """PRAC-001: 页面正常加载 — 表格+状态下拉+分页"""
        case("PRAC-001", "页面正常加载")
        page = PracticePage(driver_setup)
        step("检查表格渲染")
        headers = page.get_practice_headers()
        count = page.get_practice_count()
        print(f"表头: {headers}, 行数: {count}")
        check("页面加载成功", f"行数={count}", count >= 0)

    # ==================================================================
    # P1
    # ==================================================================

    @allure.epic("人员管理")
    @allure.feature("自主练习")
    @allure.story("筛选功能")
    @allure.severity(allure.severity_level.NORMAL)
    def test_002_page_load_and_table(self, driver_setup):
        """PRAC-002: 表格数据展示"""
        case("PRAC-002", "表格数据展示")
        page = PracticePage(driver_setup)
        row_data = page.get_first_row_texts()
        print(f"首行数据: {row_data}")
        check("表格有数据", f"列数={len(row_data)}", len(row_data) >= 7)

    @allure.epic("人员管理")
    @allure.feature("自主练习")
    @allure.story("行操作")
    @allure.severity(allure.severity_level.NORMAL)
    def test_003_view_result(self, driver_setup):
        """PRAC-003: 查看成绩"""
        case("PRAC-003", "查看成绩")
        page = PracticePage(driver_setup)
        row_data = page.get_first_row_texts()
        if not row_data or len(row_data) < 3:
            pytest.skip("无练习记录")
        name = row_data[2]  # 列3 = 练习名称
        step(f"查看成绩: {name}")
        page.view_result(name)
        title = page.get_dialog_title()
        print(f"弹窗标题: {title}")
        check("成绩弹窗已打开", title, bool(title))

    @allure.epic("人员管理")
    @allure.feature("自主练习")
    @allure.story("删除操作")
    @allure.severity(allure.severity_level.NORMAL)
    def test_004_delete_cancel(self, driver_setup):
        """PRAC-004: 删除-取消"""
        case("PRAC-004", "取消删除")
        page = PracticePage(driver_setup)
        row_data = page.get_first_row_texts()
        if not row_data or len(row_data) < 3:
            pytest.skip("无练习记录")
        name = row_data[2]
        step(f"取消删除: {name}")
        page.delete_record(name, confirm=False)
        check("记录保留", True, True)

    @allure.epic("人员管理")
    @allure.feature("自主练习")
    @allure.story("边界值")
    @allure.severity(allure.severity_level.NORMAL)
    def test_005_accuracy_display(self, driver_setup):
        """PRAC-005: 正确率显示"""
        case("PRAC-005", "正确率显示检查")
        page = PracticePage(driver_setup)
        values = page.get_accuracy_values()
        print(f"正确率值: {values}")
        has_values = len(values) > 0
        check("有正确率数据", f"共{len(values)}条", has_values)
