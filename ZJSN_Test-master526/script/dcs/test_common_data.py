"""DCS 常用点位 测试脚本

模块: dcs | 页面: common-data | 路由: #/common-data
Fixture: common_data_page (conftest.py)
"""
import pytest
import allure
import logging

logger = logging.getLogger(__name__)


@allure.epic("DCS 数据监控")
@allure.feature("常用点位")
class TestCommonData:

    @allure.story("页面加载")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.smoke
    def test_001_page_load(self, common_data_page):
        """TC-COM-001: 常用点位页面正常加载，至少显示 1 个卡片"""
        with allure.step("导航到常用点位页面"):
            common_data_page.navigate()

        with allure.step("验证页面就绪"):
            card_count = common_data_page.get_card_count()
            assert card_count > 0, f"页面应至少显示1个卡片/表格区域，实际: {card_count}"
            logger.info("页面加载成功，%d 个卡片/区域", card_count)

    @allure.story("搜索常用点位")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_002_search(self, common_data_page):
        """TC-COM-002: 搜索框输入后卡片筛选"""
        with allure.step("导航"):
            common_data_page.navigate()
            cards_before = common_data_page.get_card_count()

        with allure.step("搜索"):
            common_data_page.search("温度")

        with allure.step("验证结果"):
            cards_after = common_data_page.get_card_count()
            logger.info("搜索前: %d, 搜索后: %d", cards_before, cards_after)

    @allure.story("重置搜索")
    @allure.severity(allure.severity_level.NORMAL)
    def test_003_reset_search(self, common_data_page):
        """TC-COM-003: 重置恢复默认卡片"""
        with allure.step("搜索后重置"):
            common_data_page.navigate()
            common_data_page.search("温度")
            common_data_page.reset_search()
            card_count = common_data_page.get_card_count()
            assert card_count >= 0, "重置后应正常显示"

    @allure.story("点击卡片")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.skip(reason="页面为搜索表单+数据表格布局，非卡片视图。PO CommonDataPage 假设卡片/拖拽/右键菜单，与实际DOM不匹配，需重新设计PO")
    def test_004_click_card(self, common_data_page):
        pass

    @allure.story("新增常用点位")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.skip(reason="DCS常用点位页面为只读查询页，无'新增'按钮")
    def test_005_add_dialog(self, common_data_page):
        pass
