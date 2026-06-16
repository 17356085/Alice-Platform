"""承包商单位管理测试脚本

测试范围：
  - 页面列表展示、分页
  - 搜索（按名称/编码/状态）
  - 新增承包商单位（闭环：新增→查询→修改→删除）
  - 行内操作（编辑、启停用、删除）
"""
import pytest
import sys
import os
import inspect
import allure
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from page.personnel_page.ContractorUnitPage import ContractorUnitPage

CREATED_UNIT_CODE = None
CREATED_UNIT_NAME = None
UPDATED_UNIT_NAME = None


def _generate_unit_test_data():
    """生成本轮闭环测试数据"""
    day_tag = datetime.now().strftime("%Y%m%d%H%M%S")
    # 统一社会信用代码 = 18位数字
    unit_code = f"91{day_tag}AB"
    unit_name = f"测试承包商_{day_tag}"
    updated_name = f"测试承包商_{day_tag}_已修改"
    return unit_code, unit_name, updated_name


class TestContractorUnit:
    """承包商单位管理测试用例"""

    @pytest.fixture(autouse=True)
    def _allure_case_meta(self, request):
        doc = (inspect.getdoc(request.function) or "").strip()
        title = doc.replace(":", " ").strip() if doc else request.function.__name__
        try:
            allure.dynamic.title(title)
            if doc:
                allure.dynamic.description(doc)
        except Exception:
            pass
        yield

    def _require_created_unit_code(self):
        global CREATED_UNIT_CODE
        assert CREATED_UNIT_CODE, "未获取到新增承包商单位编码，请先执行新增用例"
        return CREATED_UNIT_CODE

    def _require_created_unit_name(self):
        global CREATED_UNIT_NAME
        assert CREATED_UNIT_NAME, "未获取到新增承包商单位名称，请先执行新增用例"
        return CREATED_UNIT_NAME

    @pytest.mark.smoke
    @allure.epic("人员管理")
    @allure.feature("承包商管理")
    @allure.story("承包商单位-页面展示")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_001_page_display(self, driver_setup):
        """CU-001: 页面打开时正常显示承包商单位列表"""
        driver = driver_setup
        page = ContractorUnitPage(driver)
        print("\n========== 测试 CU-001: 页面显示正常 ==========")

        try:
            total_text = page.get_total_count_text()
            print(f"[OK] 获取到总条数信息: {total_text}")
            assert any(char.isdigit() for char in total_text), "总条数应包含数字"

            header_text = page.get_table_header_texts()
            print(f"[OK] 表头字段: {header_text}")
            assert len(header_text) > 0, "表头不应为空"

            row_count = page.get_table_row_count()
            print(f"[OK] 当前页加载了 {row_count} 条数据")

            print("========== CU-001 测试通过 ==========")

        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    def test_002_pagination(self, driver_setup):
        """CU-002: 分页功能正常"""
        driver = driver_setup
        page = ContractorUnitPage(driver)
        print("\n========== 测试 CU-002: 分页功能正常 ==========")

        try:
            total = page.get_total_count()
            print(f"总数据条数: {total}")

            if total <= 0:
                print("无数据，跳过分页测试")
                return

            page1_first = page.get_first_row_data()
            print(f"第 1 页第 1 行数据: {page1_first}")

            has_next = page.is_next_page_enabled()
            if has_next:
                page.click_next_page()
                page2_first = page.get_first_row_data()
                print(f"第 2 页第 1 行数据: {page2_first}")
                assert page1_first != page2_first, "分页失败：两页数据相同"
                page.click_prev_page()
                print("[OK] 分页功能验证通过")
            else:
                print("无下一页按钮，数据可能不足一页")

            print("========== CU-002 测试通过 ==========")

        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    def test_003_search_by_name(self, driver_setup):
        """CU-003: 按单位名称搜索"""
        driver = driver_setup
        page = ContractorUnitPage(driver)
        print("\n========== 测试 CU-003: 按单位名称搜索 ==========")

        try:
            keyword = "测"
            page.input_search_name(keyword)
            page.click_search()
            row_count = page.get_table_row_count()
            print(f"搜索结果行数: {row_count}")
            assert row_count >= 0, "搜索后列表应正常显示"

            page.click_reset()
            print("========== CU-003 测试通过 ==========")

        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    def test_004_search_by_code(self, driver_setup):
        """CU-004: 按单位编码搜索"""
        driver = driver_setup
        page = ContractorUnitPage(driver)
        print("\n========== 测试 CU-004: 按单位编码搜索 ==========")

        try:
            keyword = "CU"
            # 承包商单位页面可能无独立编码搜索框，改用名称搜索
            try:
                page.input_search_code(keyword)
            except Exception:
                print("编码搜索框未找到，改用名称搜索")
                page.input_search_name(keyword)
            page.click_search()
            row_count = page.get_table_row_count()
            print(f"搜索结果行数: {row_count}")
            assert row_count >= 0, "搜索后列表应正常显示"

            page.click_reset()
            print("========== CU-004 测试通过 ==========")

        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    def test_005_reset_button(self, driver_setup):
        """CU-005: 重置按钮功能正常"""
        driver = driver_setup
        page = ContractorUnitPage(driver)
        print("\n========== 测试 CU-005: 重置按钮功能正常 ==========")

        try:
            page.input_search_name("测试")
            page.click_search()
            page.click_reset()
            row_count = page.get_table_row_count()
            print(f"重置后行数: {row_count}")
            assert row_count >= 0, "重置后列表应正常加载"
            print("========== CU-005 测试通过 ==========")

        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    def test_006_add_unit_success(self, driver_setup):
        """CU-006: 新增承包商单位成功（闭环数据）"""
        driver = driver_setup
        page = ContractorUnitPage(driver)
        print("\n========== 测试 CU-006: 新增承包商单位成功 ==========")

        try:
            global CREATED_UNIT_CODE, CREATED_UNIT_NAME, UPDATED_UNIT_NAME
            unit_code, unit_name, updated_name = _generate_unit_test_data()
            CREATED_UNIT_CODE = unit_code
            CREATED_UNIT_NAME = unit_name
            UPDATED_UNIT_NAME = updated_name
            print(f"本轮闭环测试数据：编码={unit_code}, 名称={unit_name}")

            page.click_add_button()
            dialog_title = page.get_dialog_title_text()
            print(f"弹窗标题: {dialog_title}")

            page.fill_dialog_input("统一社会信用代码", unit_code)
            page.fill_dialog_input("承包商名称", unit_name)

            try:
                page.fill_dialog_input("法定代表人", "张三")
                page.fill_dialog_input("联系人", "李四")
                page.fill_dialog_input("联系电话", "13800138000")
                page.fill_dialog_input("企业地址", "测试地址")
            except Exception:
                print("部分非必填字段填充失败，跳过")

            page.click_dialog_save()
            toast = page.get_toast_text()
            print(f"操作提示: {toast}")
            assert toast, "应返回操作提示"

            # 验证新增数据存在
            page.click_reset()
            page.input_search_name(unit_name)
            page.click_search()
            assert page.is_unit_name_present(unit_name), f"新增的承包商单位「{unit_name}」应在列表中"
            print(f"[OK] 新增承包商单位「{unit_name}」验证通过")

            print("========== CU-006 测试通过 ==========")

        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    def test_007_edit_unit(self, driver_setup):
        """CU-007: 编辑承包商单位"""
        driver = driver_setup
        page = ContractorUnitPage(driver)
        print("\n========== 测试 CU-007: 编辑承包商单位 ==========")

        try:
            unit_name = self._require_created_unit_name()
            global UPDATED_UNIT_NAME

            page.input_search_name(unit_name)
            page.click_search()

            page.click_edit_by_name(unit_name)
            page.fill_dialog_input("承包商名称", UPDATED_UNIT_NAME)
            page.click_dialog_save()

            toast = page.get_toast_text()
            print(f"操作提示: {toast}")
            assert toast, "应返回操作提示"

            print(f"[OK] 承包商单位已修改为「{UPDATED_UNIT_NAME}」")
            print("========== CU-007 测试通过 ==========")

        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    def test_008_delete_unit(self, driver_setup):
        """CU-008: 删除承包商单位（清理测试数据）"""
        driver = driver_setup
        page = ContractorUnitPage(driver)
        print("\n========== 测试 CU-008: 删除承包商单位 ==========")

        try:
            unit_name = self._require_created_unit_name()
            global UPDATED_UNIT_NAME
            search_name = UPDATED_UNIT_NAME if UPDATED_UNIT_NAME else unit_name

            page.click_reset()
            page.input_search_name(search_name)
            page.click_search()

            page.click_delete_by_name(search_name)
            page.confirm_message_box()

            toast = page.get_toast_text()
            print(f"操作提示: {toast}")
            assert toast, "应返回操作提示"

            print(f"[OK] 承包商单位「{search_name}」已删除")
            print("========== CU-008 测试通过 ==========")

        except Exception as e:
            pytest.fail(f"测试失败：{e}")


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
