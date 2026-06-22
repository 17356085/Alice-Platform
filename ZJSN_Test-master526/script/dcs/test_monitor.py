"""DCS 关键参数监控 测试脚本

模块: dcs | 页面: monitor | 路由: #/monitor
Fixture: monitor_page (conftest.py)
"""
import pytest
import allure
import logging
from base.cleanup_tracker import get_cleanup_tracker

logger = logging.getLogger(__name__)


@allure.epic("DCS 数据监控")
@allure.feature("关键参数监控")
class TestMonitor:

    @allure.story("页面加载")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.smoke
    def test_001_page_load(self, monitor_page):
        """TC-MON-001: 页面正常加载，至少显示 1 个参数卡片"""
        with allure.step("导航到关键参数监控页面"):
            monitor_page.navigate()

        with allure.step("验证页面核心元素"):
            card_count = monitor_page.get_card_count()
            assert card_count >= 1, f"期望 >=1 个参数卡片，实际 {card_count}"
            logger.info("页面加载成功，%d 个参数卡片", card_count)

    @allure.story("参数搜索")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.skip(reason="关键参数监控为卡片仪表盘，无传统搜索栏")
    def test_002_search(self, monitor_page):
        pass

    @allure.story("重置搜索")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.skip(reason="关键参数监控为卡片仪表盘，无重置按钮")
    def test_003_reset_search(self, monitor_page):
        pass

    @allure.story("数据刷新")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.skip(reason="监控仪表盘无'刷新'按钮，数据自动推送")
    def test_004_refresh(self, monitor_page):
        pass

    @allure.story("新增参数")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.skip(reason="DCS监控页面为只读仪表盘，无'新增'按钮")
    def test_005_add_param(self, monitor_page):
        pass

    @allure.story("参数详情")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.skip(reason="监控卡片选择器需根据实际DOM调整")
    def test_006_card_detail(self, monitor_page):
        pass


@allure.epic("DCS 数据监控")
@allure.feature("关键参数监控 - 编辑删除")
class TestMonitorEdit:

    @allure.story("编辑参数")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.skip(reason="DCS监控为只读仪表盘，无编辑功能")
    def test_101_edit_param(self, monitor_page):
        pass
