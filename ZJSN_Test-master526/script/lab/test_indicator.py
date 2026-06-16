"""气体/水质分析设计指标 — 测试脚本

覆盖 gas-indicator + water-indicator
只读展示页面，验证行数
"""
import pytest
import logging

logger = logging.getLogger(__name__)


class TestGasIndicator:
    """气体分析设计指标"""

    def test_page_loads(self, gas_indicator_page):
        """TD-LI-001: 页面加载"""
        page = gas_indicator_page
        page._wait_page_ready()
        rows = page.get_row_count()
        assert rows > 0, "设计指标表格应有数据"

    def test_row_count(self, gas_indicator_page):
        """TD-LI-002: 行数验证 — gas=23"""
        page = gas_indicator_page
        assert page.verify_row_count(), \
            f"预期23行，实际{page.get_row_count()}行"


class TestWaterIndicator:
    """水质分析设计指标"""

    def test_page_loads(self, water_indicator_page):
        """页面加载"""
        page = water_indicator_page
        page._wait_page_ready()
        rows = page.get_row_count()
        assert rows > 0

    def test_row_count(self, water_indicator_page):
        """行数验证 — water=22"""
        page = water_indicator_page
        assert page.verify_row_count(), \
            f"预期22行，实际{page.get_row_count()}行"
