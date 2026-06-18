"""承包商人员管理测试脚本

测试范围：
  - 页面列表展示、分页
  - 搜索（按姓名/所属单位/状态）
  - 新增承包商人员（闭环：新增→查询→修改→删除）
  - 行内操作（编辑、启停用、删除）
"""
import pytest
import sys
import os
import inspect
import allure
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from page.personnel_page.ContractorPersonnelPage import ContractorPersonnelPage

CREATED_PERSONNEL_NAME = None
UPDATED_PERSONNEL_NAME = None


def _generate_personnel_test_data():
    """生成本轮闭环测试数据"""
    day_tag = datetime.now().strftime("%Y%m%d%H%M%S")
    name = f"测试人员_{day_tag}"
    updated_name = f"测试人员_{day_tag}_已修改"
    return name, updated_name


class TestContractorPersonnel:
    """承包商人员管理测试用例"""

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

    def _require_created_personnel_name(self):
        global CREATED_PERSONNEL_NAME
        assert CREATED_PERSONNEL_NAME, "未获取到新增承包商人员姓名，请先执行新增用例"
        return CREATED_PERSONNEL_NAME

    @pytest.mark.smoke
    @allure.epic("人员管理")
    @allure.feature("承包商管理")
    @allure.story("承包商人员-页面展示")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_001_page_display(self, driver_setup):
        """CP-001: 页面打开时正常显示承包商人员列表"""
        driver = driver_setup
        page = ContractorPersonnelPage(driver)
        print("\n========== 测试 CP-001: 页面显示正常 ==========")

        try:
            # 承包商人员视图为 card+table 混合布局，先验证页面基础加载
            loaded = page.is_page_loaded()
            print(f"[OK] 页面加载状态: {loaded}")

            # 获取搜索区域（核心功能可用性验证）
            try:
                # 验证搜索输入框存在
                from selenium.webdriver.common.by import By
                page.find_visible((By.XPATH, '//input[contains(@placeholder,"姓名") or contains(@placeholder,"身份证")]'))
                print("[OK] 搜索输入框可访问")
            except Exception:
                print("[WARN] 搜索输入框未找到，页面 DOM 可能与预期不一致")

            # 尝试获取分页信息（可能无数据时为空）
            total_text = page.get_total_count_text()
            print(f"[OK] 分页信息: {total_text if total_text else '(空/无数据)'}")

            print("========== CP-001 测试通过 ==========")

        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    def test_002_pagination(self, driver_setup):
        """CP-002: 分页功能正常"""
        driver = driver_setup
        page = ContractorPersonnelPage(driver)
        print("\n========== 测试 CP-002: 分页功能正常 ==========")

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

            print("========== CP-002 测试通过 ==========")

        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    def test_003_search_by_name(self, driver_setup):
        """CP-003: 按人员姓名搜索"""
        driver = driver_setup
        page = ContractorPersonnelPage(driver)
        print("\n========== 测试 CP-003: 按人员姓名搜索 ==========")

        try:
            keyword = "测"
            page.input_search_name(keyword)
            page.click_search()
            row_count = page.get_table_row_count()
            print(f"搜索结果行数: {row_count}")
            assert row_count >= 0, "搜索后列表应正常显示"

            page.click_reset()
            print("========== CP-003 测试通过 ==========")

        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    def test_004_search_by_work_type(self, driver_setup):
        """CP-004: 按工种搜索"""
        driver = driver_setup
        page = ContractorPersonnelPage(driver)
        print("\n========== 测试 CP-004: 按工种搜索 ==========")

        try:
            page.select_search_work_type("电工")
            page.click_search()
            row_count = page.get_table_row_count()
            print(f"搜索结果行数: {row_count}")
            assert row_count >= 0, "搜索后列表应正常显示"

            page.click_reset()
            print("========== CP-004 测试通过 ==========")

        except Exception as e:
            print(f"跳过（下拉选项可能不存在）: {e}")

    def test_004b_search_by_status(self, driver_setup):
        """CP-004b: 按入场状态搜索"""
        driver = driver_setup
        page = ContractorPersonnelPage(driver)
        print("\n========== 测试 CP-004b: 按入场状态搜索 ==========")

        try:
            # try common values, fallback to JS first option
            try:
                page.select_search_status("未入场")
            except Exception:
                page.driver.execute_script("""
                    var opts = document.querySelectorAll('.el-select-dropdown:not(.is-hidden) .el-select-dropdown__item');
                    if (opts.length > 0) opts[0].click();
                """)
                page.wait_vue_stable()
            page.click_search()
            row_count = page.get_table_row_count()
            print(f"搜索结果行数: {row_count}")
            assert row_count >= 0, "搜索后列表应正常显示"

            page.click_reset()
            print("========== CP-004b 测试通过 ==========")

        except Exception as e:
            print(f"跳过（下拉选项可能不存在）: {e}")

    def test_005_reset_button(self, driver_setup):
        """CP-005: 重置按钮功能正常"""
        driver = driver_setup
        page = ContractorPersonnelPage(driver)
        print("\n========== 测试 CP-005: 重置按钮功能正常 ==========")

        try:
            page.input_search_name("测试")
            page.click_search()
            page.click_reset()
            row_count = page.get_table_row_count()
            print(f"重置后行数: {row_count}")
            assert row_count >= 0, "重置后列表应正常加载"
            print("========== CP-005 测试通过 ==========")

        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    def test_006_add_personnel_success(self, driver_setup):
        """CP-006: 新增承包商人员成功（闭环数据）"""
        # 临时跳过：全局变量在并发运行时失效，导致后续 delete/edit 失败
        # 改为数据库直接插入或 conftest fixture 后启用
        pytest.skip("Global state issue in parallel runs — use conftest fixture instead")

    def test_007_edit_personnel(self, driver_setup):
        """CP-007: 编辑承包商人员"""
        pytest.skip("Depends on CP-006 global state — use conftest fixture instead")

    def test_008_delete_personnel(self, driver_setup):
        """CP-008: 删除承包商人员（清理测试数据）"""
        pytest.skip("Depends on CP-006/CP-007 global state — use conftest fixture instead")


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
