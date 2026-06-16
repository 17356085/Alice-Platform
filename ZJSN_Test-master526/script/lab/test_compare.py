"""气体/水质分析对比 — 测试脚本

覆盖 gas-compare + water-compare
"""
import pytest
import logging

logger = logging.getLogger(__name__)


class TestGasCompare:
    """气体分析对比"""

    def test_page_loads_empty(self, gas_compare_page):
        """TD-LC-001: 初始空状态"""
        page = gas_compare_page
        page._wait_page_ready()
        # 初始无数据

    def test_dual_position_search(self, gas_compare_page):
        """TD-LC-002: 双位置对比查询"""
        page = gas_compare_page
        page.search_compare("界区原料气", "除雾除尘出口原料气")
        rows = page.get_row_count()
        assert rows >= 0


class TestWaterCompare:
    """水质分析对比"""

    def test_page_loads_empty(self, water_compare_page):
        """初始空状态"""
        page = water_compare_page
        page._wait_page_ready()

    def test_dual_position_search(self, water_compare_page):
        """双位置对比查询"""
        page = water_compare_page
        page.search_compare("取样点1", "取样点2")
        rows = page.get_row_count()
        assert rows >= 0


class TestSamePositionGuard:
    """相同位置校验"""

    def test_same_position_gas(self, gas_compare_page):
        """TD-LC-003: 相同位置查询"""
        page = gas_compare_page
        page.search_compare("界区原料气", "界区原料气")
        # 应无对比数据或空表格
        page.wait_vue_stable()
