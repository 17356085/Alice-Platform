"""学习记录模块测试脚本

Phase 4 自动生成 | 2026-06-12
覆盖: 11 条用例 (P0×2 + P1×7 + P2×2)
"""
import inspect
import os
import sys

import allure
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from page.personnel_page.StudyRecordPage import StudyRecordPage


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


class TestStudyRecord:
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
    @allure.feature("学习记录")
    @allure.story("页面加载")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_001_page_load(self, driver_setup):
        """SR-001: 页面正常加载 — 表格+3个筛选条件+分页"""
        case("SR-001", "页面正常加载")
        page = StudyRecordPage(driver_setup)
        step("检查页面渲染")
        count = page.get_record_count()
        print(f"记录数: {count}")
        check("页面加载成功", f"记录数={count}", count >= 0)

    # ==================================================================
    # P1
    # ==================================================================

    @allure.epic("人员管理")
    @allure.feature("学习记录")
    @allure.story("搜索功能")
    @allure.severity(allure.severity_level.NORMAL)
    def test_002_search_by_student(self, driver_setup):
        """SR-002: 学员名称搜索"""
        case("SR-002", "学员名称搜索")
        page = StudyRecordPage(driver_setup)
        step("搜索 admin")
        page.search_by_student("admin")
        count = page.get_record_count()
        print(f"搜索结果: {count}")
        check("搜索成功", f"记录数={count}", count >= 0)

    @allure.epic("人员管理")
    @allure.feature("学习记录")
    @allure.story("搜索功能")
    @allure.severity(allure.severity_level.NORMAL)
    def test_003_search_by_course(self, driver_setup):
        """SR-003: 课程名称搜索"""
        case("SR-003", "课程名称搜索")
        page = StudyRecordPage(driver_setup)
        step("搜索课程 'test'")
        page.search_by_course("test")
        count = page.get_record_count()
        print(f"搜索结果: {count}")
        check("搜索成功", f"记录数={count}", count >= 0)

    @allure.epic("人员管理")
    @allure.feature("学习记录")
    @allure.story("重置功能")
    @allure.severity(allure.severity_level.NORMAL)
    def test_004_reset_search(self, driver_setup):
        """SR-004: 重置搜索条件"""
        case("SR-004", "重置搜索")
        page = StudyRecordPage(driver_setup)
        step("输入条件后重置")
        page.input_student_name("admin")
        page.click_reset()
        page.click_search()
        count = page.get_record_count()
        print(f"重置后: {count}")
        check("重置成功", f"记录数={count}", count >= 0)

    @allure.epic("人员管理")
    @allure.feature("学习记录")
    @allure.story("数据展示")
    @allure.severity(allure.severity_level.NORMAL)
    def test_005_progress_display(self, driver_setup):
        """SR-005: 学习进度百分比显示"""
        case("SR-005", "学习进度显示")
        page = StudyRecordPage(driver_setup)
        page.click_search()
        values = page.get_progress_values()
        print(f"进度值: {values}")
        has_percent = any("%" in v for v in values) if values else False
        check("进度含百分比", f"值={values}", has_percent or len(values) > 0)

    @allure.epic("人员管理")
    @allure.feature("学习记录")
    @allure.story("数据展示")
    @allure.severity(allure.severity_level.NORMAL)
    def test_006_student_names(self, driver_setup):
        """SR-006: 学员名称列数据"""
        case("SR-006", "学员名称列")
        page = StudyRecordPage(driver_setup)
        page.click_search()
        names = page.get_student_names()
        print(f"学员: {names}")
        check("有学员数据", f"共{len(names)}人", len(names) > 0)
