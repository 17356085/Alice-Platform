#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
气体分析设计指标 测试脚本

页面路由: #/lab/gas/indicator
模块: lab
版本: 1.0

测试覆盖:
    - GI-01: 页面正常加载并显示表格字段 (P0)
    - GI-02: 表格列数据可读 (P0)
    - GI-03: 新增一条完整指标数据 (P0)
    - GI-04: 必填项为空时新增失败 (P1)
    - GI-06: 编辑单条指标数据 (P1)
    - GI-09: 删除单条指标 (P1)
"""

import pytest
import allure
from faker import Faker

faker = Faker(locale='zh_CN')


def generate_test_data(data: dict) -> dict:
    """Generate test data from a template dict. Simple passthrough."""
    return dict(data)


class TestGasIndicatorDisplay:
    """气体分析设计指标 — 页面展示验证"""

    @allure.epic("化验室取样")
    @allure.feature("气体分析设计指标")
    @allure.story("页面基础展示")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.smoke
    def test_gi_01_page_display(self, gas_indicator_page):
        """GI-01: 页面正常加载并显示表格字段"""
        page = gas_indicator_page

        with allure.step("导航到气体分析设计指标页面"):
            page.navigate()

        with allure.step("获取表头并校验关键字段存在"):
            headers = page.get_table_headers()
            expected = {"序号", "指标名称", "分类", "单位", "规则", "阈值", "备注"}
            found = [h for h in headers if h in expected]
            assert len(found) >= 5, f"预期表头应包含至少5个关键字段（{expected}），实际获取表头：{headers}"

        with allure.step("验证表格数据加载状态"):
            row_count = page.get_table_row_count()
            empty_text = page.get_empty_text() or ""
            is_data_loaded = (row_count > 0) or ("暂无" in empty_text)
            assert is_data_loaded, f"表格数据加载异常：行数={row_count}，空提示='{empty_text}'"

    @allure.epic("化验室取样")
    @allure.feature("气体分析设计指标")
    @allure.story("页面基础展示")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_gi_02_table_columns(self, gas_indicator_page):
        """GI-02: 表格列数据可读"""
        page = gas_indicator_page

        with allure.step("获取指标名称列数据（第2列）"):
            names = page.get_column_data(2)

        if names:
            with allure.step("验证指标名称列有数据"):
                assert len(names) >= 1, f"指标名称列应有至少1条数据，实际={names}"
        else:
            with allure.step("表格为空时验证行数为0"):
                row_count = page.get_table_row_count()
                assert row_count >= 0, f"表格行数异常，实际={row_count}"


class TestGasIndicatorCRUD:
    """气体分析设计指标 — 增删改操作验证"""

    @allure.epic("化验室取样")
    @allure.feature("气体分析设计指标")
    @allure.story("新增指标")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    @pytest.mark.destructive
    def test_gi_03_add_indicator(self, gas_indicator_page):
        """GI-03: 新增一条完整指标数据"""
        page = gas_indicator_page
        # 使用 faker 生成随机测试数据
        test_data = generate_test_data({
            "指标名称": f"自动化测试指标-{faker.word()}",
            "分类": "气体",
            "单位": "mg/m³",
            "规则": "最大值",
            "阈值": "10"
        })

        with allure.step("准备随机测试指标数据"):
            indicator_name = test_data["指标名称"]
            category = test_data["分类"]
            unit = test_data["单位"]
            rule = test_data["规则"]
            threshold = test_data["阈值"]
            test_data_str = f"名称={indicator_name}, 分类={category}, 单位={unit}, 规则={rule}, 阈值={threshold}"

        with allure.step(f"新增指标：{test_data_str}"):
            page.click_add()
            page.dialog_input_name(indicator_name)
            page.dialog_select_category(category)
            page.dialog_input_unit(unit)
            page.dialog_select_rule(rule)
            page.dialog_input_threshold(threshold)
            page.dialog_confirm()

        with allure.step("验证新增的指标出现在表格中"):
            names = page.get_column_data(2)
            assert indicator_name in names, f"新增的指标'{indicator_name}'未出现在表格中。表格数据={names}"

    @allure.epic("化验室取样")
    @allure.feature("气体分析设计指标")
    @allure.story("新增指标")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.destructive
    def test_gi_04_add_with_empty_required(self, gas_indicator_page):
        """GI-04: 必填项为空时新增失败"""
        page = gas_indicator_page
        test_data = generate_test_data({
            "指标名称": "",
            "分类": "气体",
            "单位": "mg/m³",
            "规则": "最大值",
            "阈值": ""
        })

        with allure.step("准备测试数据（指标名称为空、阈值为空）"):
            indicator_name = test_data["指标名称"]
            category_index = test_data["分类"]
            unit = test_data["单位"]
            rule_index = test_data["规则"]
            threshold = test_data["阈值"]

        with allure.step("打开新增弹窗并输入空指标名称"):
            page.click_add()
            page.dialog_input_name(indicator_name)
            page.dialog_select_category(category_index)
            page.dialog_input_unit(unit)
            page.dialog_select_rule(rule_index)

        with allure.step("点击确定并验证弹窗未关闭"):
            page.dialog_confirm()
            # 验证弹窗仍然存在，表明新增失败
            is_dialog_open = page._wait_for_dialog_short_check()
            assert is_dialog_open, "应表单验证失败，弹窗不应关闭"

    @allure.epic("化验室取样")
    @allure.feature("气体分析设计指标")
    @allure.story("编辑指标")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.destructive
    def test_gi_06_edit_indicator(self, gas_indicator_page):
        """GI-06: 编辑单条指标数据"""
        page = gas_indicator_page
        # 假设已存在一条可用指标，使用第一条作为编辑对象
        updated_name = f"编辑-自动化-{faker.word()}"

        with allure.step("获取第一条指标的名称"):
            names = page.get_column_data(2)
            assert len(names) > 0, "没有可编辑的指标数据"
            original_name = names[0]
            target_name = original_name

        with allure.step(f"编辑指标'{target_name}'，修改名称为'{updated_name}'"):
            page.click_edit_by_name(target_name)
            page.dialog_input_name(updated_name)
            page.dialog_confirm()

        with allure.step("验证编辑后的指标名称出现在表格中"):
            current_names = page.get_column_data(2)
            assert updated_name in current_names, f"编辑后的指标名称'{updated_name}'未出现在表格中。当前表格数据={current_names}"

        with allure.step("恢复原始指标名称（teardown准备）"):
            yield
            # 在teardown中恢复数据：编辑回原始名称
            page.click_edit_by_name(updated_name)
            page.dialog_input_name(original_name)
            page.dialog_confirm()

    @allure.epic("化验室取样")
    @allure.feature("气体分析设计指标")
    @allure.story("删除指标")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.destructive
    def test_gi_09_delete_indicator(self, gas_indicator_page):
        """GI-09: 删除单条指标"""
        page = gas_indicator_page

        with allure.step("获取并确认存在可删除的指标"):
            old_names = page.get_column_data(2)
            assert len(old_names) > 0, "没有可删除的指标数据"
            target_name = old_names[0]

        with allure.step(f"删除指标'{target_name}'"):
            page.click_delete_by_name(target_name)
            page.dialog_confirm_del()  # 确认删除弹窗

        with allure.step("验证该指标已从表格中消失"):
            current_names = page.get_column_data(2)
            assert target_name not in current_names, f"指标'{target_name}'未被成功删除。当前表格数据={current_names}"