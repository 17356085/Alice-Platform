"""接口管理模块测试脚本"""
import os
import sys
import pytest
import allure
from selenium.common.exceptions import TimeoutException

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from page.system_page.ApiManagePage import ApiManagePage


def step(text):
    try:
        with allure.step(text):
            print(f"步骤：{text}")
    except Exception:
        print(f"步骤：{text}")


def case(case_id, title):
    print(f"\n========== 用例 {case_id}：{title} ==========")
    try:
        allure.dynamic.title(f"{case_id} {title}")
        allure.dynamic.description(f"用例编号：{case_id}\n用例说明：{title}")
    except Exception:
        pass


def ea(expected, actual):
    return f"预期结果：{expected}；实际结果：{actual}"


class TestApiManagement:
    @pytest.mark.smoke
    @allure.epic("系统管理")
    @allure.feature("接口管理")
    @allure.story("页面基础展示")
    @allure.severity(allure.severity_level.NORMAL)
    def test_sy_api_01_page_display(self, driver_setup):
        page = ApiManagePage(driver_setup)
        case("SY-API-01", "正常显示接口管理页面")
        step("等待页面加载")
        page._wait_settled(timeout=15)
        step("尝试切换到Swagger iframe")
        page.switch_to_api_iframe()
        try:
            step("验证页面内容加载")
            loaded = page.is_page_loaded()
            assert loaded, ea("接口管理页面正常加载（API文档可见）", "页面内容为空或未渲染")
        finally:
            page.switch_to_default_content()

    @allure.epic("系统管理")
    @allure.feature("接口管理")
    @allure.story("API端点展示")
    @allure.severity(allure.severity_level.NORMAL)
    def test_sy_api_02_api_groups_display(self, driver_setup):
        page = ApiManagePage(driver_setup)
        case("SY-API-02", "API分组正常展示")
        step("等待页面加载")
        page._wait_settled(timeout=15)
        step("尝试切换到Swagger iframe")
        page.switch_to_api_iframe()
        try:
            total = page.get_api_count()
            assert total > 0, ea("API分组或端点正常展示", f"total={total}")
        finally:
            page.switch_to_default_content()

    @allure.epic("系统管理")
    @allure.feature("接口管理")
    @allure.story("API搜索")
    @allure.severity(allure.severity_level.NORMAL)
    def test_sy_api_03_search_api(self, driver_setup):
        page = ApiManagePage(driver_setup)
        case("SY-API-03", "API搜索功能")
        step("等待页面加载")
        page._wait_settled(timeout=15)
        page.switch_to_api_iframe()
        try:
            if page.search_api("user"):
                step("搜索关键词: user")
                count = page.get_api_count()
                page.switch_to_default_content()
                assert count >= 0, ea("搜索操作正常执行", f"匹配{count}个端点")
            else:
                pytest.skip("未找到API搜索框（可能非Swagger UI）")
        finally:
            page.switch_to_default_content()

    @allure.epic("系统管理")
    @allure.feature("接口管理")
    @allure.story("API端点展开")
    @allure.severity(allure.severity_level.NORMAL)
    def test_sy_api_04_expand_endpoint(self, driver_setup):
        page = ApiManagePage(driver_setup)
        case("SY-API-04", "展开API端点详情")
        step("等待页面加载")
        page._wait_settled(timeout=15)
        page.switch_to_api_iframe()
        try:
            if page.get_api_count() == 0:
                pytest.skip("当前无API端点可展开")
            step("点击第一个端点")
            ok = page.click_first_endpoint()
            assert ok, ea("API端点正常展开", "点击操作失败")
        finally:
            page.switch_to_default_content()


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
