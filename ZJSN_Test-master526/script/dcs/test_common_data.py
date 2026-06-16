# test_common_data.py
import pytest
import allure
from base.cleanup_tracker import get_cleanup_tracker

@allure.epic("设备管理")
@allure.feature("公共数据管理")
class TestCommonData:

    @allure.story("页面加载")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.smoke
    def test_001_page_load(self, common_data_page):
        """TC-COM-001: 公共数据页正常加载"""
        with allure.step("导航到公共数据页"):
            common_data_page.navigate()
        with allure.step("验证表格可见"):
            assert common_data_page.is_table_visible(), "数据表格未加载"

    @allure.story("字典查询")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_002_search_by_key(self, common_data_page):
        """TC-COM-002: 按字典键名搜索"""
        with allure.step("输入搜索关键词 'TC-ALARM-TYPE'"):
            common_data_page.search("TC-ALARM-TYPE")
        with allure.step("验证搜索结果"):
            rows = common_data_page.get_table_rows()
            assert len(rows) > 0, "未找到匹配的字典项"

    @allure.story("新增字典项")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.destructive
    def test_003_add_dictionary_item(self, common_data_page, cleanup):
        """TC-COM-003: 新增一个字典项并在 teardown 中删除"""
        tracker = get_cleanup_tracker()
        item_key = "TC-TEST-KEY-001"
        item_value = "测试值"

        with allure.step("点击新增按钮"):
            common_data_page.click_add()
        with allure.step("填写键名和值"):
            common_data_page.fill_key(item_key)
            common_data_page.fill_value(item_value)
        with allure.step("保存并确认"):
            common_data_page.save()
            assert common_data_page.is_save_success(), "保存失败"
        with allure.step("注册待清理数据"):
            tracker.register_entity(
                entity_type="common_data",
                entity_id=item_key,
                cleanup_func=lambda: common_data_page.delete_by_key(item_key)
            )
        # teardown 由 cleanup fixture 自动执行