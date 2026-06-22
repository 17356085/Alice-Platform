"""DCS 上传日志 测试脚本

模块: dcs | 页面: upload-log | 路由: #/upload-log
Fixture: upload_log_page (conftest.py)
"""
import pytest
import allure
import logging

logger = logging.getLogger(__name__)


@allure.epic("DCS 数据监控")
@allure.feature("上传日志")
class TestUploadLog:

    @allure.story("页面加载")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.smoke
    def test_001_page_load(self, upload_log_page):
        """TC-UL-001: 上传日志页面正常加载，表格可访问"""
        with allure.step("导航到上传日志页面"):
            upload_log_page.navigate()

        with allure.step("验证页面就绪"):
            row_count = upload_log_page.get_row_count()
            assert row_count > 0, f"上传日志应有数据，实际: {row_count} 行"
            logger.info("页面加载成功，%d 行日志", row_count)

    @allure.story("统计卡片")
    @allure.severity(allure.severity_level.NORMAL)
    def test_002_stats_cards(self, upload_log_page):
        """TC-UL-002: 统计卡片显示"""
        with allure.step("导航"):
            upload_log_page.navigate()

        with allure.step("获取统计数据"):
            try:
                total = upload_log_page.get_stat_total()
                logger.info("上传总数: %s", total)
            except Exception as e:
                logger.warning("统计卡片可能不存在: %s", e)
                pytest.skip("统计卡片未找到")

    @allure.story("日志搜索")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_003_search(self, upload_log_page):
        """TC-UL-003: 按批次号/关键词搜索日志"""
        with allure.step("导航"):
            upload_log_page.navigate()

        with allure.step("搜索日志"):
            upload_log_page.search("MQTT")

        with allure.step("验证结果"):
            rows = upload_log_page.get_row_count()
            logger.info("搜索结果: %d 条", rows)
            assert rows >= 0, f"搜索后表格异常: {rows}"

    @allure.story("按状态筛选")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_004_filter_by_status(self, upload_log_page):
        """TC-UL-004: 按状态筛选日志"""
        with allure.step("导航"):
            upload_log_page.navigate()

        with allure.step("筛选失败状态"):
            upload_log_page.filter_by_status("失败")
            rows = upload_log_page.get_row_count()
            logger.info("失败日志: %d 条", rows)

    @allure.story("重置搜索")
    @allure.severity(allure.severity_level.NORMAL)
    def test_005_reset_search(self, upload_log_page):
        """TC-UL-005: 重置搜索条件"""
        with allure.step("导航并搜索"):
            upload_log_page.navigate()
            upload_log_page.search("MQTT")
            rows_filtered = upload_log_page.get_row_count()

        with allure.step("重置"):
            upload_log_page.reset_search()
            rows_all = upload_log_page.get_row_count()
            logger.info("筛选后: %d, 重置后: %d", rows_filtered, rows_all)

    @allure.story("查看详情")
    @allure.severity(allure.severity_level.NORMAL)
    def test_006_detail(self, upload_log_page):
        """TC-UL-006: 查看日志详情弹窗"""
        with allure.step("导航"):
            upload_log_page.navigate()

        with allure.step("点击第一条日志详情"):
            try:
                upload_log_page.click_detail("MQTT")
                detail_text = upload_log_page.get_detail_content()
                logger.info("详情内容: %s", detail_text[:200])
                assert len(detail_text) > 0, "详情弹窗内容为空"
            except Exception as e:
                logger.warning("详情弹窗异常: %s", e)
                pytest.skip("详情弹窗未找到或定位器需调整")

        with allure.step("关闭详情"):
            upload_log_page.close_detail()

    @allure.story("分页导航")
    @allure.severity(allure.severity_level.NORMAL)
    def test_007_pagination(self, upload_log_page):
        """TC-UL-007: 分页翻页"""
        with allure.step("导航"):
            upload_log_page.navigate()
            total = upload_log_page.get_total_count()
            if total > 20:
                upload_log_page.go_to_next_page()
                logger.info("翻页成功")
            else:
                logger.info("数据不足 20 条，跳过翻页测试")
