"""
测试脚本：deviceCentralStation - 全量数据页面
模块：dcs
页面：all-data
"""

import pytest
import allure
from base.cleanup_tracker import get_cleanup_tracker
from page.dcs_page.AllDataPage import AllDataPage


@allure.epic("设备管理中心")
@allure.feature("全量数据管理")
class TestAllData:
    """全量数据页面测试类"""

    @pytest.fixture(autouse=True)
    def cleanup_registry(self, request):
        """
        每个测试用例执行后清理通过 CleanupTracker 注册的测试数据
        清除失败只打 warning，不阻塞其他用例
        """
        tracker = get_cleanup_tracker()
        yield
        tracker.cleanup_all(warn_only=True)

    # --------------------------------------------------------------
    # TC-ALLDATA-001：页面加载
    # --------------------------------------------------------------
    @allure.story("页面加载")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.smoke
    def test_001_page_load(self, all_data_page: AllDataPage):
        """验证全量数据页面正常加载，核心组件可见"""
        with allure.step("导航到全量数据页面"):
            all_data_page.navigate()

        with allure.step("验证表格和搜索框可见"):
            assert all_data_page.is_table_visible(), "全量数据表格未显示"
            assert all_data_page.is_search_input_visible(), "搜索输入框未显示"

    # --------------------------------------------------------------
    # TC-ALLDATA-002：按名称搜索
    # --------------------------------------------------------------
    @allure.story("搜索功能")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_002_search_by_name(self, all_data_page: AllDataPage):
        """根据数据名称搜索，结果应含该名称的记录"""
        search_keyword = "TC-数据名称-002"  # 使用 TC- 前缀标识测试数据
        with allure.step("输入搜索关键词"):
            all_data_page.search(search_keyword)

        with allure.step("获取表格数据并验证"):
            data = all_data_page.get_table_data()
            assert len(data) > 0, f"搜索 '{search_keyword}' 结果为空"
            assert any(
                search_keyword in row.get("名称", "") for row in data
            ), f"搜索结果中未包含 '{search_keyword}'"

    # --------------------------------------------------------------
    # TC-ALLDATA-003：新增数据并验证（破坏性操作，销毁后清理）
    # --------------------------------------------------------------
    @allure.story("新增数据")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.destructive
    def test_003_add_record(self, all_data_page: AllDataPage):
        """
        新增一条数据，验证出现在列表中，并通过 CleanupTracker 注册清理
        """
        record_name = "TC-新增-003-" + str(pytest.current_timestamp)  # 唯一标识
        record_data = {"name": record_name, "type": "温度报警", "value": 100}

        with allure.step("点击新增按钮"):
            all_data_page.click_add_button()

        with allure.step("填写表单并提交"):
            all_data_page.fill_add_form(record_data)
            all_data_page.submit_add_form()

        with allure.step("注册清理实体"):
            tracker = get_cleanup_tracker()
            tracker.register_entity(
                entity_id=record_name,
                delete_func=all_data_page.delete_record,
                delete_args=[record_name],
            )

        with allure.step("搜索新增数据并验证"):
            all_data_page.search(record_name)
            data = all_data_page.get_table_data()
            assert len(data) == 1, f"预期1条记录，实际 {len(data)}"
            assert data[0]["名称"] == record_name, f"记录名称不符: {data[0]['名称']}"

    # --------------------------------------------------------------
    # TC-ALLDATA-004：删除数据（破坏性操作，需先创建再删除）
    # --------------------------------------------------------------
    @allure.story("删除数据")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.destructive
    def test_004_delete_record(self, all_data_page: AllDataPage):
        """
        创建一条数据，删除后验证不再显示
        注意：创建的数据也需注册清理以防删除失败
        """
        record_name = "TC-删除-004"
        record_data = {"name": record_name, "type": "湿度", "value": 80}

        with allure.step("先创建测试数据"):
            all_data_page.click_add_button()
            all_data_page.fill_add_form(record_data)
            all_data_page.submit_add_form()

            # 注册清理（即使删除成功也保证被清理）
            tracker = get_cleanup_tracker()
            tracker.register_entity(
                entity_id=record_name,
                delete_func=all_data_page.delete_record,
                delete_args=[record_name],
            )

        with allure.step("执行删除操作"):
            all_data_page.delete_record(record_name)

        with allure.step("验证数据已从表格中移除"):
            all_data_page.search(record_name)
            data = all_data_page.get_table_data()
            assert len(data) == 0, f"删除后仍存在记录: {data}"