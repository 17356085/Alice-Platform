# test_upload_log.py
import pytest
import allure
from page.dcs_page.UploadLogPage import UploadLogPage
from base.cleanup_tracker import get_cleanup_tracker

@allure.epic("设备管理")
@allure.feature("上传日志")
class TestUploadLog:

    @allure.story("页面加载")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.smoke
    def test_001_page_load(self, upload_log_page: UploadLogPage):
        """TC-UPLOAD-001: 页面正常加载"""
        with allure.step("导航到上传日志页"):
            upload_log_page.navigate()
        with allure.step("验证页面核心元素"):
            assert upload_log_page.is_table_visible(), "日志表格未加载"

    @allure.story("搜索日志")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_002_search_by_filename(self, upload_log_page: UploadLogPage):
        """TC-UPLOAD-002: 按文件名搜索日志"""
        with allure.step("输入搜索关键词"):
            upload_log_page.search("test_log_2023")
        with allure.step("验证搜索结果"):
            data = upload_log_page.get_table_data()
            assert len(data) > 0, "搜索结果为0，预期至少一条日志"
        with allure.step("清空搜索条件"):
            upload_log_page.clear_search()

    @allure.story("上传日志")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.destructive
    def test_003_upload_log_file(self, upload_log_page: UploadLogPage):
        """TC-UPLOAD-003: 上传日志文件"""
        cleanup = get_cleanup_tracker()
        filename = "TC-test_upload_file.txt"
        with allure.step("点击上传按钮"):
            upload_log_page.click_upload()
        with allure.step("选择文件并上传"):
            upload_log_page.upload_file(filename, content="test content")
        with allure.step("验证上传成功"):
            assert upload_log_page.is_toast_success(), "上传操作未返回成功提示"
        # 注册待清理实体（假设系统支持按名称删除）
        cleanup.register_entity("upload_log", filename)

    @allure.story("删除日志")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.destructive
    def test_004_delete_log(self, upload_log_page: UploadLogPage):
        """TC-UPLOAD-004: 删除日志"""
        cleanup = get_cleanup_tracker()
        # 先创建一条测试数据
        with allure.step("创建一条测试日志"):
            upload_log_page.create_test_log("TC-delete_test")
            cleanup.register_entity("upload_log", "TC-delete_test")
        with allure.step("选中该日志"):
            upload_log_page.select_log("TC-delete_test")
        with allure.step("点击删除按钮"):
            upload_log_page.click_delete()
        with allure.step("确认删除弹窗"):
            upload_log_page.confirm_delete()
        with allure.step("验证日志已删除"):
            assert not upload_log_page.is_log_exists("TC-delete_test"), "日志未被成功删除"