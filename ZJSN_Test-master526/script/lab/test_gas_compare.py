"""气体分析对比 — 测试脚本"""
import pytest
import allure


def step(text):
    try:
        with allure.step(text):
            print(f"步骤：{text}")
    except Exception:
        print(f"步骤：{text}")


class TestGasCompare:
    @allure.epic("化验室取样")
    @allure.feature("气体分析对比")
    def test_gc_01_page_display(self, gas_compare_page):
        """GC-01: 正常显示气体分析对比页面（搜索表单）"""
        page = gas_compare_page
        step("验证页面加载")
        assert page.is_page_loaded(), "页面应正常加载（含日期选择器）"

    def test_gc_02_date_search(self, gas_compare_page):
        """GC-02: 日期范围查询"""
        page = gas_compare_page
        step("设置日期范围")
        page.set_start_date("2026-01-01")
        page.set_end_date("2026-06-12")
        step("点击查询")
        page.click_query()
        # 查询后表格应该加载（有数据或空状态提示）
        step("验证响应无异常")
        assert page.is_page_loaded(), "查询后页面应正常"
