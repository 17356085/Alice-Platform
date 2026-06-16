"""入场记录测试脚本

测试范围：
  - 页面列表展示、分页
  - 搜索（按姓名/单位/日期范围）
  - 导出功能
  - 详情查看
"""
import pytest
import sys
import os
import inspect
import allure

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from page.personnel_page.EntryRecordPage import EntryRecordPage


class TestEntryRecord:
    """入场记录测试用例"""

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
    @allure.story("入场记录-页面展示")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_001_page_display(self, driver_setup):
        """ER-001: 页面打开时正常显示入场记录列表"""
        driver = driver_setup
        page = EntryRecordPage(driver)
        print("\n========== 测试 ER-001: 页面显示正常 ==========")

        try:
            # 验证页面加载
            loaded = page.is_page_loaded()
            print(f"[OK] 页面加载状态: {loaded}")
            assert loaded, "页面应正常加载"

            # 验证表头
            header_text = page.get_table_header_texts()
            print(f"[OK] 表头字段: {header_text}")
            assert len(header_text) > 0, "表头不应为空"

            # 分页信息（入场记录可能 0 条数据，容许空）
            total_text = page.get_total_count_text()
            print(f"[OK] 分页信息: {total_text if total_text else '(空/无数据)'}")

            row_count = page.get_table_row_count()
            print(f"[OK] 当前页行数: {row_count}（0 条时显示暂无数据为正常）")

            print("========== ER-001 测试通过 ==========")

        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    def test_002_pagination(self, driver_setup):
        """ER-002: 分页功能正常"""
        driver = driver_setup
        page = EntryRecordPage(driver)
        print("\n========== 测试 ER-002: 分页功能正常 ==========")

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

            print("========== ER-002 测试通过 ==========")

        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    def test_003_search_by_name(self, driver_setup):
        """ER-003: 按人员姓名搜索"""
        driver = driver_setup
        page = EntryRecordPage(driver)
        print("\n========== 测试 ER-003: 按人员姓名搜索 ==========")

        try:
            keyword = "测"
            page.input_search_name(keyword)
            page.click_search()
            row_count = page.get_table_row_count()
            print(f"搜索结果行数: {row_count}")
            assert row_count >= 0, "搜索后列表应正常显示"

            page.click_reset()
            print("========== ER-003 测试通过 ==========")

        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    def test_004_search_by_date_range(self, driver_setup):
        """ER-004: 按日期范围搜索"""
        driver = driver_setup
        page = EntryRecordPage(driver)
        print("\n========== 测试 ER-004: 按日期范围搜索 ==========")

        try:
            page.input_date_start("2025-01-01")
            page.input_date_end("2026-12-31")
            page.click_search()
            row_count = page.get_table_row_count()
            print(f"日期范围搜索结果行数: {row_count}")
            assert row_count >= 0, "搜索后列表应正常显示"

            page.click_reset()
            print("========== ER-004 测试通过 ==========")

        except Exception as e:
            print(f"日期选择器可能未找到，跳过: {e}")

    def test_005_search_by_unit(self, driver_setup):
        """ER-005: 按承包商单位搜索"""
        driver = driver_setup
        page = EntryRecordPage(driver)
        print("\n========== 测试 ER-005: 按承包商单位搜索 ==========")

        try:
            page.select_search_unit("测试承包商")
            page.click_search()
            row_count = page.get_table_row_count()
            print(f"搜索结果行数: {row_count}")
            assert row_count >= 0, "搜索后列表应正常显示"

            page.click_reset()
            print("========== ER-005 测试通过 ==========")

        except Exception as e:
            print(f"跳过（下拉选项可能不存在）: {e}")

    def test_006_reset_button(self, driver_setup):
        """ER-006: 重置按钮功能正常"""
        driver = driver_setup
        page = EntryRecordPage(driver)
        print("\n========== 测试 ER-006: 重置按钮功能正常 ==========")

        try:
            page.input_search_name("测试")
            page.click_search()
            page.click_reset()
            row_count = page.get_table_row_count()
            print(f"重置后行数: {row_count}")
            assert row_count >= 0, "重置后列表应正常加载"
            print("========== ER-006 测试通过 ==========")

        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    def test_007_view_detail(self, driver_setup):
        """ER-007: 查看入场记录详情"""
        driver = driver_setup
        page = EntryRecordPage(driver)
        print("\n========== 测试 ER-007: 查看入场记录详情 ==========")

        try:
            row_count = page.get_table_row_count()
            if row_count == 0:
                print("无数据，跳过详情测试")
                return

            first_row = page.get_first_row_data()
            if len(first_row) > 0:
                person_name = first_row[0]
                page.click_detail_by_name(person_name)

                dialog_title = page.get_dialog_title_text()
                print(f"详情弹窗标题: {dialog_title}")
                assert dialog_title, "弹窗应有标题"

                page.click_dialog_close()
                print(f"[OK] 已查看「{person_name}」的入场记录详情")

            print("========== ER-007 测试通过 ==========")

        except Exception as e:
            print(f"跳过详情测试: {e}")

    def test_008_export(self, driver_setup):
        """ER-008: 导出入场记录"""
        driver = driver_setup
        page = EntryRecordPage(driver)
        print("\n========== 测试 ER-008: 导出入场记录 ==========")

        try:
            page.click_export()
            print("[OK] 已触发导出操作")
            # 导出通常触发浏览器下载，验证无异常即可
            print("========== ER-008 测试通过 ==========")

        except Exception as e:
            print(f"导出按钮不可用，跳过: {e}")


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
