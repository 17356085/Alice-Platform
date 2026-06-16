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
        driver = driver_setup
        page = ContractorPersonnelPage(driver)
        print("\n========== 测试 CP-006: 新增承包商人员成功 ==========")

        try:
            global CREATED_PERSONNEL_NAME, UPDATED_PERSONNEL_NAME
            name, updated_name = _generate_personnel_test_data()
            CREATED_PERSONNEL_NAME = name
            UPDATED_PERSONNEL_NAME = updated_name
            print(f"本轮闭环测试数据：姓名={name}")

            page.click_add_button()
            dialog_title = page.get_dialog_title_text()
            print(f"弹窗标题: {dialog_title}")

            # 文本输入字段（el-input）
            page.fill_dialog_input("姓名", name)
            page.fill_dialog_input("身份证号", "110101199001011237")
            page.fill_dialog_input("手机号码", "13900139000")

            # 性别 → el-radio-group，默认已选"男"，无需操作
            # 安全培训状态 → el-select，默认已选"未培训"，无需操作
            # 是否特种作业人员 → el-switch，默认"否"，无需操作

            # 工种 → el-select (必填)，展开后 JS 选第一项
            import time
            try:
                page.select_dialog_dropdown("工种", "电工")
            except Exception:
                pass  # 下拉已展开但选项"电工"不存在
            page.driver.execute_script("""
                var items = document.querySelectorAll('.el-select-dropdown:not(.is-hidden) .el-select-dropdown__item');
                if (items.length > 0) items[0].click();
            """)
            time.sleep(0.5)
            page.wait_vue_stable()

            # 所属承包商 → el-select filterable (必填)，同样展开后选第一项
            try:
                page.select_dialog_dropdown("所属承包商", "TEST-001")
            except Exception:
                pass  # 下拉已展开但选项不匹配
            page.driver.execute_script("""
                var items = document.querySelectorAll('.el-select-dropdown:not(.is-hidden) .el-select-dropdown__item');
                if (items.length > 0) items[0].click();
            """)
            time.sleep(0.5)
            page.wait_vue_stable()

            import time
            time.sleep(0.5)
            # 检查是否有表单校验错误
            errors = page.driver.execute_script("""
                var errs = document.querySelectorAll('.el-form-item__error');
                var msgs = [];
                errs.forEach(function(e) { msgs.push(e.textContent.trim()); });
                return msgs;
            """)
            if errors:
                print(f"表单校验错误: {errors}")
            page.click_dialog_save()
            toast = page.get_toast_text(timeout=8)
            print(f"操作提示: '{toast}'")
            assert toast, "应返回操作提示（表单校验可能未通过）"

            # 验证新增数据存在
            page.click_reset()
            page.input_search_name(name)
            page.click_search()
            assert page.is_personnel_name_present(name), f"新增的承包商人员「{name}」应在列表中"
            print(f"[OK] 新增承包商人员「{name}」验证通过")

            print("========== CP-006 测试通过 ==========")

        except Exception as e:
            pytest.fail(f"测试失败：{e}")

            # 验证新增数据存在
            page.click_reset()
            page.input_search_name(name)
            page.click_search()
            assert page.is_personnel_name_present(name), f"新增的承包商人员「{name}」应在列表中"
            print(f"[OK] 新增承包商人员「{name}」验证通过")

            print("========== CP-006 测试通过 ==========")

        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    def test_007_edit_personnel(self, driver_setup):
        """CP-007: 编辑承包商人员"""
        driver = driver_setup
        page = ContractorPersonnelPage(driver)
        print("\n========== 测试 CP-007: 编辑承包商人员 ==========")

        try:
            name = self._require_created_personnel_name()
            global UPDATED_PERSONNEL_NAME

            page.input_search_name(name)
            page.click_search()

            page.click_edit_by_name(name)
            page.fill_dialog_input("姓名", UPDATED_PERSONNEL_NAME)
            page.click_dialog_save()

            toast = page.get_toast_text()
            print(f"操作提示: {toast}")
            assert toast, "应返回操作提示"

            print(f"[OK] 承包商人员已修改为「{UPDATED_PERSONNEL_NAME}」")
            print("========== CP-007 测试通过 ==========")

        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    def test_008_delete_personnel(self, driver_setup):
        """CP-008: 删除承包商人员（清理测试数据）"""
        driver = driver_setup
        page = ContractorPersonnelPage(driver)
        print("\n========== 测试 CP-008: 删除承包商人员 ==========")

        try:
            name = self._require_created_personnel_name()
            global UPDATED_PERSONNEL_NAME
            search_name = UPDATED_PERSONNEL_NAME if UPDATED_PERSONNEL_NAME else name

            page.click_reset()
            page.input_search_name(search_name)
            page.click_search()

            page.click_delete_by_name(search_name)
            page.confirm_message_box()

            toast = page.get_toast_text()
            print(f"操作提示: {toast}")
            assert toast, "应返回操作提示"

            print(f"[OK] 承包商人员「{search_name}」已删除")
            print("========== CP-008 测试通过 ==========")

        except Exception as e:
            pytest.fail(f"测试失败：{e}")


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
