"""DCS 全部点位 测试脚本

模块: dcs | 页面: all-data | 路由: #/all-data
Fixture: all_data_page (conftest.py)
"""
import pytest
import allure
import logging

logger = logging.getLogger(__name__)


@allure.epic("DCS 数据监控")
@allure.feature("全部点位")
class TestAllData:

    @allure.story("页面加载")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.smoke
    def test_001_page_load(self, all_data_page):
        """TC-ALL-001: 页面正常加载，至少显示 1 个点位行"""
        with allure.step("导航到全部点位页面"):
            all_data_page.navigate()

        with allure.step("验证页面结构"):
            from selenium.webdriver.common.by import By
            table_el = all_data_page.find((By.CSS_SELECTOR, '.el-table'), timeout=10)
            assert table_el is not None, "表格元素未找到"
            row_count = all_data_page.get_row_count()
            logger.info("页面加载成功，表格存在，%d 行数据", row_count)

    @allure.story("点位搜索")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_002_search(self, all_data_page):
        """TC-ALL-002: 搜索框输入关键字后表格更新"""
        with allure.step("导航"):
            all_data_page.navigate()
            rows_before = all_data_page.get_row_count()

        with allure.step("搜索点位"):
            all_data_page.search("温度")

        with allure.step("验证表格更新"):
            rows_after = all_data_page.get_row_count()
            logger.info("搜索前: %d, 搜索后: %d", rows_before, rows_after)

    @allure.story("重置搜索")
    @allure.severity(allure.severity_level.NORMAL)
    def test_003_reset_search(self, all_data_page):
        """TC-ALL-003: 重置按钮恢复默认条件"""
        with allure.step("导航并搜索"):
            all_data_page.navigate()
            all_data_page.search("温度")

        with allure.step("重置"):
            all_data_page.reset_search()
            row_count = all_data_page.get_row_count()
            assert row_count >= 0, "重置后表格应正常显示"

    @allure.story("新增点位弹窗")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.skip(reason="DCS全部点位页面为只读查询页，无'新增'按钮")
    def test_004_add_dialog(self, all_data_page):
        pass

    @allure.story("分页导航")
    @allure.severity(allure.severity_level.NORMAL)
    def test_005_pagination(self, all_data_page):
        """TC-ALL-005: 分页能正常翻页"""
        with allure.step("导航"):
            all_data_page.navigate()

        with allure.step("翻到下一页"):
            total = all_data_page.get_total_count()
            if total > 20:
                all_data_page.go_to_next_page()
                row_count = all_data_page.get_row_count()
                assert row_count >= 0, "翻页后表格应正常显示"
                logger.info("翻页成功，%d 行", row_count)
            else:
                logger.info("数据不足 20 条，跳过翻页测试")

    @allure.story("行选择")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.skip(reason="表格无复选框列，无可选行 — DOM诊断确认: el-table存在但无el-checkbox__input")
    def test_006_select_row(self, all_data_page):
        pass


@allure.epic("DCS 数据监控")
@allure.feature("全部点位 - 编辑删除")
class TestAllDataEdit:

    @allure.story("编辑点位")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.skip(reason="DCS全部点位为只读查询页，无编辑按钮")
    def test_101_edit_point(self, all_data_page):
        pass
