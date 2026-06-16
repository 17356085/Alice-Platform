import pytest
import allure
from base.cleanup_tracker import get_cleanup_tracker

@pytest.mark.usefixtures("driver")  # 假设 conftest 提供了 driver fixture
class TestPointConfig:
    """
    测点配置页面测试
    模块: dcs
    页面: point-config
    """

    @allure.epic("DCS 系统")
    @allure.feature("测点配置")
    @allure.story("页面加载")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.smoke
    def test_001_page_load(self, point_config_page: "PointConfigPage"):
        """TC-POINT-001: 页面正常加载"""
        with allure.step("导航到测点配置页面"):
            point_config_page.navigate()
        with allure.step("验证页面核心元素可见"):
            assert point_config_page.is_table_visible(), "测点配置表格未加载"
        with allure.step("验证搜索框可用"):
            assert point_config_page.is_search_box_enabled(), "搜索框不可用"

    @allure.epic("DCS 系统")
    @allure.feature("测点配置")
    @allure.story("搜索功能")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_002_search_by_name(self, point_config_page: "PointConfigPage"):
        """TC-POINT-002: 按测点名称搜索"""
        keyword = "TC-温度-001"
        with allure.step(f"输入搜索关键词: {keyword}"):
            point_config_page.search(keyword)
        with allure.step("获取搜索结果"):
            data = point_config_page.get_table_data()
        with allure.step("验证搜索过滤"):
            assert len(data) > 0, f"搜索结果为空，关键词: {keyword}"
            for row in data:
                assert keyword in row.get("名称", ""), f"结果包含无关项: {row}"

    @allure.epic("DCS 系统")
    @allure.feature("测点配置")
    @allure.story("新增测点")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.destructive
    def test_003_add_point(self, point_config_page: "PointConfigPage", cleanup_tracker):
        """TC-POINT-003: 添加测点（含数据清理）"""
        point_data = {
            "name": "TC-新增测点-自动",
            "type": "模拟量",
            "unit": "℃",
            "description": "自动化测试创建"
        }
        with allure.step("填写新增表单"):
            point_config_page.click_add_button()
            point_config_page.fill_point_form(point_data)
        with allure.step("保存并验证成功提示"):
            point_config_page.submit()
            assert point_config_page.get_success_message() == "添加成功", "新增测点失败"
        # 注册清理：通过搜索名称删除
        @cleanup_tracker.register
        def cleanup_added_point():
            with allure.step(f"清理测试数据: {point_data['name']}"):
                point_config_page.search(point_data['name'])
                if point_config_page.is_row_exists(point_data['name']):
                    point_config_page.select_row(point_data['name'])
                    point_config_page.click_delete_button()
                    point_config_page.confirm_delete()
        with allure.step("验证数据出现在列表中"):
            point_config_page.search(point_data['name'])
            rows = point_config_page.get_table_data()
            assert any(point_data['name'] in row.get("名称", "") for row in rows), "新增数据未显示"

    @allure.epic("DCS 系统")
    @allure.feature("测点配置")
    @allure.story("编辑测点")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.destructive
    def test_004_edit_point(self, point_config_page: "PointConfigPage", setup_cleanup_test_point):
        """TC-POINT-004: 编辑测点描述"""
        point_name = "TC-编辑测试点"
        # 假设 setup_cleanup_test_point fixture 创建了一个测试点并在 teardown 中删除
        with allure.step("搜索目标测点"):
            point_config_page.search(point_name)
        with allure.step("点击编辑按钮"):
            point_config_page.select_row(point_name)
            point_config_page.click_edit_button()
        new_desc = "编辑后的描述 - 自动化"
        with allure.step("修改描述并保存"):
            point_config_page.set_description(new_desc)
            point_config_page.save_edit()
        with allure.step("验证更新成功"):
            message = point_config_page.get_success_message()
            assert "编辑成功" in message, f"编辑失败: {message}"
        with allure.step("再次搜索并确认"):
            point_config_page.search(point_name)
            row_data = point_config_page.get_row_data(point_name)
            assert row_data.get("描述") == new_desc, f"描述未更新，期望: {new_desc}，实际: {row_data.get('描述')}"

    @allure.epic("DCS 系统")
    @allure.feature("测点配置")
    @allure.story("删除测点")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.destructive
    def test_005_delete_point(self, point_config_page: "PointConfigPage", setup_cleanup_test_point):
        """TC-POINT-005: 删除测点（数据由 fixture 创建且无需清理，因为删除操作本身即清理）"""
        point_name = "TC-删除测试点"
        with allure.step("搜索待删除测点"):
            point_config_page.search(point_name)
        with allure.step("选中并删除"):
            point_config_page.select_row(point_name)
            point_config_page.click_delete_button()
            point_config_page.confirm_delete()
        with allure.step("验证删除成功"):
            message = point_config_page.get_success_message()
            assert "删除成功" in message, f"删除失败: {message}"
        with allure.step("确认记录已不存在"):
            point_config_page.search(point_name)
            rows = point_config_page.get_table_data()
            assert len(rows) == 0, f"删除后仍存在记录: {rows}"

    @allure.epic("DCS 系统")
    @allure.feature("测点配置")
    @allure.story("分页功能")
    @allure.severity(allure.severity_level.NORMAL)
    def test_006_pagination(self, point_config_page: "PointConfigPage"):
        """TC-POINT-006: 分页跳转"""
        with allure.step("获取总页数"):
            total_pages = point_config_page.get_total_pages()
        if total_pages <= 1:
            pytest.skip("数据量不足，无法测试分页")
        with allure.step("跳转到第二页"):
            point_config_page.go_to_page(2)
        with allure.step("验证当前页高亮"):
            assert point_config_page.get_current_page() == 2, "未成功跳转到第二页"
        with allure.step("验证第二页数据非空"):
            row_count = point_config_page.get_row_count()
            assert row_count > 0, "第二页无数据"

    @allure.epic("DCS 系统")
    @allure.feature("测点配置")
    @allure.story("导出功能")
    @allure.severity(allure.severity_level.NORMAL)
    def test_007_export(self, point_config_page: "PointConfigPage", tmp_path):
        """TC-POINT-007: 导出测点列表为 Excel"""
        export_path = tmp_path / "point_export.xlsx"
        with allure.step("点击导出按钮"):
            point_config_page.click_export()
        with allure.step("选择导出路径"):
            point_config_page.handle_file_download(export_path)
        with allure.step("验证文件已下载"):
            assert export_path.exists(), f"导出文件不存在: {export_path}"
        with allure.step("验证文件不为空"):
            file_size = export_path.stat().st_size
            assert file_size > 0, "导出的文件大小为0字节"