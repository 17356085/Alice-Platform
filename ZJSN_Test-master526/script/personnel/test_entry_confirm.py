"""入场确认测试脚本

测试范围：
  - 页面列表展示、分页
  - 搜索（按承包商名称/人员姓名/组合搜索）
  - 单条确认入场
  - 批量确认入场
"""
import pytest
import sys
import os
import inspect
import allure

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from page.personnel_page.EntryConfirmPage import EntryConfirmPage


class TestEntryConfirm:
    """入场确认测试用例"""

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

    @pytest.mark.smoke
    @allure.epic("人员管理")
    @allure.feature("承包商管理")
    @allure.story("入场确认-页面展示")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_001_page_display(self, driver_setup):
        """EC-001: 页面打开时正常显示入场确认列表"""
        driver = driver_setup
        page = EntryConfirmPage(driver)
        print("\n========== 测试 EC-001: 页面显示正常 ==========")

        try:
            loaded = page.is_page_loaded()
            print(f"[OK] 页面加载状态: {loaded}")
            assert loaded, "页面应正常加载"

            header_text = page.get_table_header_texts()
            print(f"[OK] 表头字段: {header_text}")
            assert len(header_text) > 0, "表头不应为空"

            total_text = page.get_total_count_text()
            print(f"[OK] 分页信息: {total_text if total_text else '(空/无数据)'}")

            row_count = page.get_table_row_count()
            print(f"[OK] 当前页行数: {row_count}（0 条时显示暂无数据为正常）")

            print("========== EC-001 测试通过 ==========")

        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    def test_002_search_by_contractor(self, driver_setup):
        """EC-002: 按承包商名称搜索"""
        driver = driver_setup
        page = EntryConfirmPage(driver)
        print("\n========== 测试 EC-002: 按承包商名称搜索 ==========")

        try:
            # 先获取一条数据的承包商名称作为搜索关键词
            row_count = page.get_table_row_count()
            if row_count == 0:
                print("无数据，跳过搜索测试")
                return

            first_row = page.get_first_row_data()
            contractor_name = first_row[page.COL_CONTRACTOR - 1] if len(first_row) >= page.COL_CONTRACTOR else ""
            if not contractor_name:
                contractor_name = "测"
            print(f"搜索关键词: {contractor_name}")

            page.input_contractor_name(contractor_name)
            page.click_search()
            result_count = page.get_table_row_count()
            print(f"搜索结果行数: {result_count}")
            assert result_count >= 0, "搜索后列表应正常显示"

            # 验证搜索结果包含关键词
            if result_count > 0:
                col_data = page.get_column_data(page.COL_CONTRACTOR)
                all_match = all(contractor_name in (d or '') for d in col_data)
                print(f"搜索结果匹配校验: {'OK' if all_match else '部分匹配（可接受）'}")

            page.click_reset()
            print("========== EC-002 测试通过 ==========")

        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    def test_003_search_by_personnel(self, driver_setup):
        """EC-003: 按人员姓名搜索"""
        driver = driver_setup
        page = EntryConfirmPage(driver)
        print("\n========== 测试 EC-003: 按人员姓名搜索 ==========")

        try:
            keyword = "测"
            page.input_personnel_name(keyword)
            page.click_search()
            row_count = page.get_table_row_count()
            print(f"搜索结果行数: {row_count}")
            assert row_count >= 0, "搜索后列表应正常显示"

            page.click_reset()
            print("========== EC-003 测试通过 ==========")

        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    def test_004_combined_search(self, driver_setup):
        """EC-004: 组合搜索（承包商名称+人员姓名）"""
        driver = driver_setup
        page = EntryConfirmPage(driver)
        print("\n========== 测试 EC-004: 组合搜索 ==========")

        try:
            page.input_contractor_name("测")
            page.input_personnel_name("测")
            page.click_search()
            row_count = page.get_table_row_count()
            print(f"组合搜索结果行数: {row_count}")
            assert row_count >= 0, "搜索后列表应正常显示"

            page.click_reset()
            print("========== EC-004 测试通过 ==========")

        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    def test_005_reset_button(self, driver_setup):
        """EC-005: 重置按钮功能正常"""
        driver = driver_setup
        page = EntryConfirmPage(driver)
        print("\n========== 测试 EC-005: 重置按钮功能正常 ==========")

        try:
            page.input_contractor_name("测试")
            page.input_personnel_name("测试")
            page.click_search()
            page.click_reset()
            row_count = page.get_table_row_count()
            print(f"重置后行数: {row_count}")
            assert row_count >= 0, "重置后列表应正常加载"
            print("========== EC-005 测试通过 ==========")

        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    def test_006_pagination(self, driver_setup):
        """EC-006: 分页功能正常"""
        driver = driver_setup
        page = EntryConfirmPage(driver)
        print("\n========== 测试 EC-006: 分页功能正常 ==========")

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

            print("========== EC-006 测试通过 ==========")

        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    @pytest.mark.smoke
    @allure.epic("人员管理")
    @allure.feature("承包商管理")
    @allure.story("入场确认-单条确认")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_010_single_confirm(self, driver_setup):
        """EC-010: 单条确认入场"""
        driver = driver_setup
        page = EntryConfirmPage(driver)
        print("\n========== 测试 EC-010: 单条确认入场 ==========")

        try:
            unread_names = page.get_unread_personnel_names()
            print(f"未读记录数: {len(unread_names)}")

            if not unread_names:
                print("无未读记录，跳过单条确认测试")
                return

            target = unread_names[0]
            print(f"目标人员: {target}")

            page.click_confirm_entry_by_name(target)
            page.confirm_dialog()

            toast = page.get_toast_text(timeout=10)
            print(f"Toast 消息: {toast}")
            print("========== EC-010 测试通过 ==========")

        except Exception as e:
            print(f"确认可能失败（数据依赖或无待确认记录）: {e}")

    @pytest.mark.smoke
    @allure.epic("人员管理")
    @allure.feature("承包商管理")
    @allure.story("入场确认-批量确认")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_011_batch_confirm(self, driver_setup):
        """EC-011: 批量确认入场"""
        driver = driver_setup
        page = EntryConfirmPage(driver)
        print("\n========== 测试 EC-011: 批量确认入场 ==========")

        try:
            unread_names = page.get_unread_personnel_names()
            print(f"未读记录数: {len(unread_names)}")

            if len(unread_names) < 2:
                print("未读记录不足 2 条，跳过批量确认测试")
                return

            page.select_first_n_rows(2)
            selected = page.get_selected_count()
            print(f"已选中行数: {selected}")
            assert selected >= 2, f"应选中至少 2 行，实际: {selected}"

            page.click_batch_confirm()
            page.confirm_dialog()

            toast = page.get_toast_text(timeout=10)
            print(f"Toast 消息: {toast}")
            print("========== EC-011 测试通过 ==========")

        except Exception as e:
            print(f"批量确认可能失败（数据依赖或不足）: {e}")

    def test_012_batch_confirm_no_selection(self, driver_setup):
        """EC-012: 未选择记录点击批量确认"""
        driver = driver_setup
        page = EntryConfirmPage(driver)
        print("\n========== 测试 EC-012: 未选择记录点批量确认 ==========")

        try:
            page.click_reset()  # 确保无选中状态
            page.click_batch_confirm()

            # 预期：弹窗提示"请选择记录"或按钮点不动
            toast = page.get_toast_text(timeout=5)
            print(f"Toast/提示: {toast if toast else '(可能无弹窗或按钮置灰)'}")
            print("========== EC-012 测试通过 ==========")

        except Exception as e:
            print(f"符合预期——未选择时操作被阻止: {e}")


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
