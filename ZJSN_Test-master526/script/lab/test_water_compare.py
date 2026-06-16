"""水质分析对比 — 测试脚本"""
import pytest
import allure


def step(text):
    try:
        with allure.step(text):
            print(f"步骤：{text}")
    except Exception:
        print(f"步骤：{text}")


class TestWaterCompare:
    @allure.epic("化验室取样")
    @allure.feature("水质分析对比")
    def test_wc_01_page_display(self, water_compare_page):
        """WC-01: 正常显示水质分析对比页面"""
        page = water_compare_page
        step("验证页面加载")
        assert page.is_page_loaded(), "页面应正常加载"

    def test_wc_02_date_search(self, water_compare_page):
        """WC-02: 日期范围查询"""
        page = water_compare_page
        step("设置日期范围并查询")
        page.set_start_date("2026-01-01")
        page.set_end_date("2026-06-12")
        page.click_query()
        assert page.is_page_loaded(), "查询后页面应正常"
