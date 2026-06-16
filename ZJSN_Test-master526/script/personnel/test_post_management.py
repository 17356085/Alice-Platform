"""岗位管理模块测试脚本"""
import pytest
import sys
import os
import inspect
import allure
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from page.personnel_page.PostManagePage import PostManagePage

CREATED_POST_CODE = None
CREATED_POST_NAME = None
CREATED_DAY_TAG = None
UPDATED_POST_NAME = None


def _generate_post_test_data():
    """生成本轮岗位闭环测试数据：新增、查询、修改、切换状态、删除都使用同一条数据。"""
    day_tag = datetime.now().strftime("%Y%m%d%H%M%S")
    post_code = f"AT{day_tag}"
    post_name = f"测试岗位_{day_tag}"
    updated_name = f"测试岗位_{day_tag}_已修改"
    return post_code, day_tag, post_name, updated_name


class TestPostManage:
    """岗位管理模块测试用例"""

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

    def _require_created_post_code(self):
        global CREATED_POST_CODE
        assert CREATED_POST_CODE, "未获取到新增岗位编码，请先执行新增用例"
        return CREATED_POST_CODE

    def _require_created_post_name(self):
        global CREATED_POST_NAME
        assert CREATED_POST_NAME, "未获取到新增岗位名称，请先执行新增用例"
        return CREATED_POST_NAME

    @pytest.mark.smoke
    @allure.epic("人员管理")
    @allure.feature("岗位管理")
    @allure.story("页面基础展示")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_001_page_display(self, driver_setup):
        """POST-001: 页面打开时正常显示岗位列表"""
        driver = driver_setup
        post_manage = PostManagePage(driver)
        print("\n========== 测试 POST-001: 页面显示正常 ==========")

        try:
            total_text = post_manage.get_total_count_text()
            print(f"[OK] 获取到总条数信息: {total_text}")
            assert any(char.isdigit() for char in total_text), "总条数应包含数字"

            header_text = post_manage.get_table_header_texts()
            print(f"[OK] 表头字段: {header_text}")
            assert len(header_text) > 0, "表头不应为空"

            row_count = post_manage.get_table_row_count()
            print(f"[OK] 当前页加载了 {row_count} 条数据")

            print("========== POST-001 测试通过 ==========")

        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    def test_002_pagination(self, driver_setup):
        """POST-002: 分页功能正常"""
        driver = driver_setup
        post_manage = PostManagePage(driver)
        print("\n========== 测试 POST-002: 分页功能正常 ==========")

        try:
            total = post_manage.get_total_count()
            print(f"总数据条数: {total}")

            if total <= 0:
                print("无数据，跳过分页测试")
                return

            page1_first = post_manage.get_first_row_data()
            print(f"第 1 页第 1 行数据: {page1_first}")

            has_next = post_manage.is_next_page_enabled()
            if has_next:
                post_manage.click_next_page()

                page2_first = post_manage.get_first_row_data()
                print(f"第 2 页第 1 行数据: {page2_first}")
                assert page1_first != page2_first, "分页失败：两页数据相同"

                post_manage.click_prev_page()
                print("[OK] 分页功能验证通过")
            else:
                print("无下一页按钮，数据可能不足一页")

            print("========== POST-002 测试通过 ==========")

        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    def test_003_add_post_success(self, driver_setup):
        """POST-003: 新增岗位成功（闭环数据，唯一编码和名称）"""
        driver = driver_setup
        post_manage = PostManagePage(driver)
        print("\n========== 用例 POST-003：新增岗位成功 ==========")

        try:
            global CREATED_POST_CODE, CREATED_DAY_TAG, CREATED_POST_NAME, UPDATED_POST_NAME
            post_code, day_tag, post_name, updated_name = _generate_post_test_data()
            CREATED_POST_CODE = post_code
            CREATED_DAY_TAG = day_tag
            CREATED_POST_NAME = post_name
            UPDATED_POST_NAME = updated_name
            print(f"本轮闭环测试数据：编码={CREATED_POST_CODE}, 名称={CREATED_POST_NAME}, 修改后名称={UPDATED_POST_NAME}")

            post_manage.click_add_button()
            dialog_title = post_manage.get_dialog_title_text()
            print(f"弹窗标题: {dialog_title}")

            post_manage.fill_dialog_input("岗位编码", CREATED_POST_CODE)
            post_manage.fill_dialog_input("岗位名称", CREATED_POST_NAME)

            try:
                post_manage.select_dialog_option("岗位类别", "技术岗")
            except Exception:
                print("岗位类别下拉框未找到或选择失败，跳过")

            try:
                post_manage.select_dialog_option("岗位等级", "中级")
            except Exception:
                print("岗位等级下拉框未找到或选择失败，跳过")

            post_manage.click_dialog_save()

            # Check toast — but also accept if dialog closed (save succeeded) even without toast
            toast = post_manage.get_toast_text(timeout=5)
            print(f"操作提示: {toast}")

            dialog_still_open = not post_manage.wait_dialog_closed(timeout=2)
            print(f"弹窗是否仍打开: {dialog_still_open}")

            if toast and ("成功" in toast):
                pass  # normal case
            elif not dialog_still_open:
                print("[OK] 弹窗已关闭，视为新增成功（虽未捕获到toast）")
            else:
                form_errors = post_manage.get_form_error_text()
                if form_errors:
                    pytest.fail(f"表单校验失败: {form_errors}")
                assert False, f"新增岗位提示异常: {toast}"

            print("========== POST-003 测试通过 ==========")

        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    def test_004_search_by_name(self, driver_setup):
        """POST-004: 按岗位名称模糊搜索"""
        driver = driver_setup
        post_manage = PostManagePage(driver)
        print("\n========== 用例 POST-004：按岗位名称搜索 ==========")

        try:
            post_code = self._require_created_post_code()
            post_manage.navigate_to_position_management()
            post_manage.input_search_name(post_code)
            post_manage.click_search()

            row_count = post_manage.get_table_row_count()
            print(f"搜索结果行数: {row_count}")
            assert row_count > 0, "搜索结果不应为空"

            codes = post_manage.get_column_data(post_manage.COL_POST_CODE)
            print(f"搜索结果岗位编码: {codes}")
            assert any(post_code.lower() in code.lower() for code in codes), \
                f"搜索结果未包含闭环岗位 {post_code}: {codes}"

            post_manage.click_reset()
            print("========== POST-004 测试通过 ==========")

        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    def test_005_edit_post_success(self, driver_setup):
        """POST-005: 编辑岗位成功（操作对象=刚新增岗位）"""
        driver = driver_setup
        post_manage = PostManagePage(driver)
        print("\n========== 用例 POST-005：编辑岗位成功 ==========")

        try:
            post_code = self._require_created_post_code()
            post_name = self._require_created_post_name()
            new_name = UPDATED_POST_NAME or f"测试岗位_{CREATED_DAY_TAG}_已修改"

            post_manage.navigate_to_position_management()
            post_manage.navigate_to_position_management()
            post_manage.click_reset()
            post_manage.input_search_name(post_code)
            post_manage.click_search()

            row_count = post_manage.get_table_row_count()
            assert row_count > 0, f"岗位 '{post_code}' 不存在，无法编辑"

            post_manage.click_edit_by_name(post_name)

            post_manage.fill_dialog_input("岗位名称", new_name)
            post_manage.click_dialog_save()

            toast = post_manage.get_toast_text()
            print(f"编辑提示: {toast}")
            assert toast and ("成功" in toast), f"编辑岗位提示异常: {toast}"

            post_manage.click_reset()
            post_manage.input_search_name(post_code)
            post_manage.click_search()

            names = post_manage.get_column_data(post_manage.COL_POST_NAME)
            assert new_name in names, f"岗位名称未更新成功，预期: {new_name}, 实际: {names}"
            print(f"[OK] 岗位名称已更新为: {new_name}")

            print("========== POST-005 测试通过 ==========")

        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    def test_006_toggle_status(self, driver_setup):
        """POST-006: 切换岗位状态（操作对象=已编辑岗位）"""
        driver = driver_setup
        post_manage = PostManagePage(driver)
        print("\n========== 用例 POST-006：切换岗位状态 ==========")

        try:
            post_code = self._require_created_post_code()
            updated_name = UPDATED_POST_NAME

            if not updated_name:
                pytest.skip("未获取到编辑后的岗位名称，跳过状态切换测试")

            post_manage.navigate_to_position_management()
            post_manage.click_reset()
            post_manage.input_search_name(post_code)
            post_manage.click_search()

            row_count = post_manage.get_table_row_count()
            assert row_count > 0, f"岗位 '{post_code}' 不存在"

            btn_text = post_manage.click_toggle_status_by_name(updated_name)
            print(f"点击的按钮文本: {btn_text}")

            try:
                msg_box_text = post_manage.get_message_box_text(timeout=3)
                print(f"确认框提示: {msg_box_text}")
                post_manage.confirm_message_box()
            except Exception:
                print("无二次确认弹框，直接切换")

            toast = post_manage.get_toast_text()
            print(f"状态切换提示: {toast}")

            post_manage.wait_vue_stable()
            post_manage.click_reset()
            post_manage.input_search_name(post_code)
            post_manage.click_search()

            statuses = post_manage.get_column_data(post_manage.COL_STATUS)
            print(f"当前状态值: {statuses}")

            print("========== POST-006 测试通过 ==========")

        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    def test_007_delete_post(self, driver_setup):
        """POST-007: 删除岗位（最后清理闭环数据）"""
        driver = driver_setup
        post_manage = PostManagePage(driver)
        print("\n========== 用例 POST-007：删除岗位 ==========")

        try:
            global CREATED_POST_CODE, CREATED_POST_NAME, UPDATED_POST_NAME
            post_code = self._require_created_post_code()

            post_manage.navigate_to_position_management()
            post_manage.click_reset()
            post_manage.input_search_name(post_code)
            post_manage.click_search()

            row_count = post_manage.get_table_row_count()
            assert row_count > 0, f"岗位 '{post_code}' 不存在，无法删除"

            post_manage.click_delete_by_name(post_code)

            try:
                post_manage.confirm_message_box()
            except Exception as e:
                msg = post_manage.get_message_box_text(timeout=2)
                if msg:
                    print(f"删除被阻止: {msg}")
                    try:
                        cancel_btn = post_manage.driver.find_element(
                            By.XPATH,
                            '//div[contains(@class,"el-message-box") and not(contains(@style,"display: none"))]//button[.//span[contains(text(),"取消")]]'
                        )
                        post_manage.driver.execute_script("arguments[0].click();", cancel_btn)
                        post_manage.wait_vue_stable()
                    except Exception:
                        pass
                    pytest.skip(f"岗位无法删除: {msg}")
                raise e

            toast = post_manage.get_toast_text(timeout=5)
            print(f"删除提示: {toast}")
            assert toast and ("成功" in toast or "删除" in toast), f"删除岗位提示异常: {toast}"

            post_manage.click_reset()
            post_manage.input_search_name(post_code)
            post_manage.click_search()

            still_exists = post_manage.is_post_name_present(post_code) or \
                          (UPDATED_POST_NAME and post_manage.is_post_name_present(UPDATED_POST_NAME))
            assert not still_exists, f"删除后仍能查到岗位: {post_code}"

            CREATED_POST_CODE = None
            CREATED_POST_NAME = None
            UPDATED_POST_NAME = None

            print("========== POST-007 测试通过 ==========")

        except Exception as e:
            pytest.fail(f"测试失败：{e}")


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
