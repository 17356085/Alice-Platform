"""用户管理模块测试脚本"""
import pytest
import sys
import os
import inspect
import allure
from datetime import datetime

# 将项目根目录添加到系统路径，以便正确导入模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config import DEFAULT_PASSWORD
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from page.system_page.UserManagePage import UserManagePage
from base.cleanup_tracker import get_cleanup_tracker

CREATED_USERNAME = None
CREATED_DAY_TAG = None
CREATED_PHONE = None
CREATED_NAME = None
UPDATED_NAME = None


def _generate_user_test_data():
    """生成本轮用户闭环测试数据：新增、查询、修改、删除都使用同一条数据。"""
    day_tag = datetime.now().strftime("%Y%m%d%H%M")
    username = f"test_{day_tag}"
    # 生成 11 位手机号，避免固定手机号重复导致新增失败。
    phone = f"138{day_tag[-8:]}"
    name = f"测试{day_tag}新增"
    updated_name = f"测试{day_tag}修改"
    return username, day_tag, phone, name, updated_name


class TestUserManage:
    """用户管理模块测试用例"""

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
    @allure.epic("系统管理")
    @allure.feature("用户管理")
    @allure.story("页面基础展示")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_001_page_display(self, driver_setup):
        """SY-USER-001: 页面打开时正常显示用户列表"""
        driver = driver_setup
        user_manage = UserManagePage(driver)
        print("\n========== 测试 SY-USER-001: 页面显示正常 ==========")
        
        try:
            # 1. 验证总条数元素可见
            total_text = user_manage.get_total_count_text()
            print(f"[OK] 获取到总条数信息: {total_text}")
            assert any(char.isdigit() for char in total_text), "总条数应包含数字"

            # 2. 验证表头字段是否完整
            header_text = user_manage.get_username_header_text()
            assert header_text == "用户名", f"表头应为'用户名'，实际为'{header_text}'"
            print("[OK] 表头字段验证通过：包含'用户名'")

            # 3. 验证列表有数据行
            row_count = user_manage.get_table_row_count()
            print(f"[OK] 当前页加载了 {row_count} 条数据")
            assert row_count > 0, "列表不应为空"
            
            print("========== SY-USER-001 测试通过 ==========")

        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    def test_002_pagination(self, driver_setup):
        """SY-USER-002: 分页功能正常"""
        driver = driver_setup
        user_manage = UserManagePage(driver)
        print("\n========== 测试 SY-USER-002: 分页功能正常 ==========")
        
        try:
            # 1. 获取第一页第一行的用户名
            page1_user = user_manage.get_first_row_username()
            print(f"第 1 页第 1 个用户：{page1_user}")

            # 2. 点击下一页
            user_manage.click_next_page()
                        
            # 3. 获取第二页第一行的用户名
            page2_user = user_manage.get_first_row_username()
            print(f"第 2 页第 1 个用户：{page2_user}")

            # 4. 断言：验证数据发生了变化
            assert page1_user != page2_user, f"分页失败：两页的第一行用户相同 ({page1_user})"
                        
            print("[OK] 分页功能验证通过：数据已更新")
            print("========== SY-USER-002 测试通过 ==========")

        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    def _require_created_username(self):
        global CREATED_USERNAME
        assert CREATED_USERNAME, "未获取到新增用户名，请先执行 SY-USER-003 新增用例"
        return CREATED_USERNAME

    def _add_user(self, user_manage, username, name, phone):
        user_manage.click_reset_button()
        user_manage.click_add_user_button()
        user_manage.input_dialog_input("用户名", username)
        user_manage.input_dialog_input("姓名", name)
        user_manage.input_password_in_dialog("123456")
        try:
            user_manage.input_dialog_input("手机号", phone)
        except Exception:
            pass
        selected_department = user_manage.select_dialog_option_by_text("部门", "人力行政部")
        if not selected_department:
            selected_department = user_manage.select_dialog_first_valid_option("部门")
        user_manage.click_dialog_confirm()

        toast = user_manage.get_toast_text(timeout=4)
        if not toast:
            err = user_manage.get_form_error_text(timeout=2)
            if err:
                try:
                    user_manage.click_dialog_cancel()
                except Exception:
                    pass
                raise AssertionError(f"新增未成功，表单校验提示: {err}")
            if not user_manage.wait_dialog_closed(timeout=3):
                try:
                    user_manage.click_dialog_cancel()
                except Exception:
                    pass
                raise AssertionError("新增未成功：弹窗未关闭且未获取到提示信息")
        return toast

    def _search_by_username(self, user_manage, username):
        user_manage.click_reset_button()
        user_manage.input_search_username(username)
        user_manage.click_search_button()

    def _delete_by_username(self, user_manage, username):
        self._search_by_username(user_manage, username)
        if user_manage.get_table_row_count() == 0:
            raise AssertionError(f"未查询到待删除用户: {username}")
        user_manage.click_more_user(username)
        user_manage.click_more_delete()
        user_manage.confirm_delete_message_box()
        toast = user_manage.get_toast_text(timeout=4)
        assert "成功" in toast or "删除" in toast or toast, f"删除提示异常: {toast}"
        self._search_by_username(user_manage, username)
        assert not user_manage.is_username_present(username), f"删除后仍能查到用户名: {username}"

    def test_003_add_user_success(self, driver_setup):
        """SY-USER-003: 新增用户成功（闭环数据=同一条 test_时间 数据）"""
        driver = driver_setup
        user_manage = UserManagePage(driver)
        print("\n========== 用例 SY-USER-003：新增用户成功 ==========")

        try:
            global CREATED_USERNAME, CREATED_DAY_TAG, CREATED_PHONE, CREATED_NAME, UPDATED_NAME
            target_username, day_tag, phone, name, updated_name = _generate_user_test_data()
            CREATED_USERNAME = target_username
            CREATED_DAY_TAG = day_tag
            CREATED_PHONE = phone
            CREATED_NAME = name
            UPDATED_NAME = updated_name
            print(f"本轮闭环测试数据：用户名={CREATED_USERNAME}, 姓名={CREATED_NAME}, 手机号={CREATED_PHONE}, 修改后姓名={UPDATED_NAME}")

            get_cleanup_tracker().register(
                entity_type="user", entity_name=CREATED_USERNAME,
                cleanup_method="api"
            )

            toast = self._add_user(
                user_manage,
                username=CREATED_USERNAME,
                name=CREATED_NAME,
                phone=CREATED_PHONE,
            )
            assert "成功" in toast or "新增" in toast or toast, f"新增提示异常: {toast}"
        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    def test_004_fuzzy_search(self, driver_setup):
        """SY-USER-004: 支持模糊搜索"""
        driver = driver_setup
        user_manage = UserManagePage(driver)
        print("\n========== 用例 SY-USER-004：模糊搜索验证 ==========")

        try:
            username = self._require_created_username()
            keyword = CREATED_DAY_TAG or username
            user_manage.click_reset_button()
            user_manage.input_search_username(keyword)
            user_manage.click_search_button()

            usernames = user_manage.get_column_data(2)
            print(f"模糊搜索关键字 '{keyword}' 结果: {usernames}")

            assert len(usernames) > 0, "模糊搜索结果不应为空"
            assert any(username.lower() in name.lower() for name in usernames), f"模糊搜索结果未包含闭环用户 {username}: {usernames}"

            user_manage.click_reset_button()
            print("========== SY-USER-004 测试通过 ==========")
        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    def test_005_empty_search(self, driver_setup):
        """SY-USER-005: 空值搜索显示全部"""
        driver = driver_setup
        user_manage = UserManagePage(driver)
        print("\n========== 用例 SY-USER-005：空值搜索验证 ==========")

        try:
            user_manage.click_reset_button()
            initial_count = user_manage.get_table_row_count()
            if initial_count == 0:
                user_manage.click_search_button()
                initial_count = user_manage.get_table_row_count()

            user_manage.input_search_username("")
            user_manage.click_search_button()

            after_search_count = user_manage.get_table_row_count()
            print(f"初始行数: {initial_count}, 空值搜索后行数: {after_search_count}")
            assert initial_count == after_search_count, "空值搜索应显示全部数据"

            print("========== SY-USER-005 测试通过 ==========")
        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    def test_006_add_user_phone_too_short_validation(self, driver_setup):
        """SY-USER-006: 新增用户手机号长度过短校验"""
        driver = driver_setup
        user_manage = UserManagePage(driver)
        print("\n========== 用例 SY-USER-006：新增用户手机号长度过短校验 ==========")

        try:
            digits = datetime.now().strftime("%Y%m%d%H%M%S")
            unique_username = f"test{digits}a"
            user_manage.click_add_user_button()
            user_manage.input_dialog_input("用户名", unique_username)
            user_manage.input_dialog_input("姓名", "自动化员工")
            user_manage.input_password_in_dialog("123456")
            user_manage.input_dialog_input("手机号", "12345")
            try:
                user_manage.select_dialog_option_by_text("部门", "人力行政部")
            except Exception:
                pass
            user_manage.click_dialog_confirm()
            msg = user_manage.get_toast_text(timeout=1.5)
            if not msg:
                msg = user_manage.get_form_error_text(timeout=3)
            assert "手机号格式不正确" in msg, f"手机号校验提示不符合预期: {msg}"

            user_manage.click_dialog_cancel()
            print("========== SY-USER-006 测试通过 ==========")
        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    def test_007_add_user_phone_too_long_validation(self, driver_setup):
        """SY-USER-007: 新增用户手机号长度过长校验"""
        driver = driver_setup
        user_manage = UserManagePage(driver)
        print("\n========== 用例 SY-USER-007：新增用户手机号长度过长校验 ==========")

        try:
            digits = datetime.now().strftime("%Y%m%d%H%M%S")
            unique_username = f"test{digits}b"
            user_manage.click_add_user_button()
            user_manage.input_dialog_input("用户名", unique_username)
            user_manage.input_dialog_input("姓名", "自动化员工")
            user_manage.input_password_in_dialog("123456")
            user_manage.input_dialog_input("手机号", "1" * 21)
            try:
                user_manage.select_dialog_option_by_text("部门", "人力行政部")
            except Exception:
                pass
            user_manage.click_dialog_confirm()
            msg = user_manage.get_toast_text(timeout=1.5)
            if not msg:
                msg = user_manage.get_form_error_text(timeout=3)
            assert "手机号格式不正确" in msg, f"手机号校验提示不符合预期: {msg}"

            user_manage.click_dialog_cancel()
            print("========== SY-USER-007 测试通过 ==========")
        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    def test_008_edit_user_success(self, driver_setup):
        """SY-USER-008: 编辑用户成功（操作对象=刚新增用户）"""
        driver = driver_setup
        user_manage = UserManagePage(driver)
        print("\n========== 用例 SY-USER-008：编辑用户成功 ==========")

        try:
            target_user = self._require_created_username()
            new_name = UPDATED_NAME or f"测试{CREATED_DAY_TAG or datetime.now().strftime('%Y%m%d%H%M%S')}修改"

            self._search_by_username(user_manage, target_user)
            row_count = user_manage.get_table_row_count()
            print(f"搜索结果行数: {row_count}")
            assert row_count > 0, f"用户 '{target_user}' 不存在，无法编辑"

            user_manage.click_edit_user(target_user)
            user_manage.input_edit_name(new_name)
            user_manage.click_dialog_confirm()

            toast_text = user_manage.get_toast_text()
            assert "成功" in toast_text or "修改成功" in toast_text, f"预期提示'修改成功'，实际为: {toast_text}"

            self._search_by_username(user_manage, target_user)
            actual_names = user_manage.get_column_data(3)
            assert new_name in actual_names, f"姓名未更新成功，预期: {new_name}, 实际: {actual_names}"

            print("========== SY-USER-008 测试通过 ==========")
        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    def test_009_reset_button_functionality(self, driver_setup):
        """SY-USER-009: 重置按钮功能正常"""
        driver = driver_setup
        user_manage = UserManagePage(driver)
        print("\n========== 用例 SY-USER-009：重置按钮功能验证 ==========")
        
        try:
            user_manage.click_reset_button()
            user_manage.input_search_username("admin")
            try:
                user_manage.select_role("超级管理员")
            except Exception:
                pass
            try:
                user_manage.select_status("启用")
            except Exception:
                pass
            
            user_manage.click_reset_button()
            
            input_el = WebDriverWait(driver, 5).until(EC.presence_of_element_located(user_manage.SEARCH_USERNAME_INPUT))
            v = (input_el.get_attribute("value") or "").strip()
            assert v == "", f"重置后搜索项应为空，实际用户名输入框值: {v}"

            placeholder = (input_el.get_attribute("placeholder") or "").strip()
            assert "搜索" in placeholder, f"重置后搜索框 placeholder 异常: {placeholder}"

            try:
                role_text = (driver.find_element(*user_manage.ROLE_SELECT).text or "").strip()
                assert "全部角色" in role_text, f"重置后角色应为“全部角色”，实际: {role_text}"
            except Exception as e:
                pytest.fail(f"重置后角色断言失败: {e}")

            status_ok = False
            try:
                item = driver.find_element(
                    By.XPATH,
                    '//form//div[contains(@class,"el-form-item")][.//label[contains(normalize-space(.),"状态")]]',
                )
                if item.find_elements(By.XPATH, './/div[contains(@class,"el-select")]'):
                    text = (item.text or "").strip()
                    status_ok = "全部" in text
                else:
                    checked = item.find_elements(By.XPATH, './/label[contains(@class,"is-checked")][.//span[normalize-space(.)="全部"]]')
                    status_ok = bool(checked)
            except Exception:
                status_ok = False
            assert status_ok, "重置后状态应为“全部”"

            print("========== SY-USER-009 测试通过 ==========")
        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    def test_010_add_user_required_username_validation(self, driver_setup):
        """SY-USER-010: 新增用户必填项校验(用户名)"""
        driver = driver_setup
        user_manage = UserManagePage(driver)
        print("\n========== 用例 SY-USER-010：新增用户必填项校验(用户名) ==========")

        try:
            user_manage.click_add_user_button()
            user_manage.clear_dialog_input("用户名")
            user_manage.click_dialog_confirm()

            msg = user_manage.get_toast_text()
            if not msg:
                msg = user_manage.get_form_error_text()
            assert "请输入" in msg and "用户名" in msg, f"必填校验提示不符合预期: {msg}"

            user_manage.click_dialog_cancel()
            print("========== SY-USER-010 测试通过 ==========")
        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    def test_011_add_user_username_unique_validation(self, driver_setup):
        """SY-USER-011: 新增用户用户名唯一性校验（使用刚新增用户名）"""
        driver = driver_setup
        user_manage = UserManagePage(driver)
        print("\n========== 用例 SY-USER-011：新增用户用户名唯一性校验 ==========")

        try:
            username = self._require_created_username()
            user_manage.click_add_user_button()
            user_manage.input_dialog_input("用户名", username)
            user_manage.input_dialog_input("姓名", f"测试重复{datetime.now().strftime('%Y%m%d%H%M%S')}")
            user_manage.input_password_in_dialog("123456")
            try:
                user_manage.input_dialog_input("手机号", "139" + (CREATED_DAY_TAG or datetime.now().strftime("%Y%m%d%H%M%S"))[-8:])
            except Exception:
                pass
            try:
                user_manage.select_dialog_option_by_text("部门", "人力行政部")
            except Exception:
                pass
            user_manage.click_dialog_confirm()
            msg = user_manage.get_toast_text(timeout=1.5)
            if not msg:
                msg = user_manage.get_form_error_text(timeout=3)
            assert "数据已存在" in msg or "已存在" in msg, f"唯一性校验提示不符合预期: {msg}"

            user_manage.click_dialog_cancel()
            print("========== SY-USER-011 测试通过 ==========")
        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    def test_012_search_created_user_by_username(self, driver_setup):
        """SY-USER-012: 查询刚新增用户（按用户名）"""
        driver = driver_setup
        user_manage = UserManagePage(driver)
        print("\n========== 用例 SY-USER-012：查询新增用户（按用户名） ==========")

        try:
            username = self._require_created_username()
            self._search_by_username(user_manage, username)
            row_count = user_manage.get_table_row_count()
            assert row_count >= 1, "搜索结果不应为空"
            results = user_manage.get_column_data(2)
            assert any(username.lower() in name.lower() for name in results), f"搜索结果不匹配: {results}"
        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    def test_013_search_by_name_phone(self, driver_setup):
        """SY-USER-013: 按姓名/手机号搜索（查询刚新增数据）"""
        driver = driver_setup
        user_manage = UserManagePage(driver)
        print("\n========== 用例 SY-USER-013：按姓名/手机号搜索 ==========")

        try:
            username = self._require_created_username()
            target_name = UPDATED_NAME or CREATED_NAME
            if not target_name or not CREATED_PHONE:
                pytest.skip("未获取到闭环测试姓名或手机号，跳过按姓名/手机号搜索")

            user_manage.click_reset_button()
            user_manage.input_search_username(target_name)
            user_manage.click_search_button()

            names = user_manage.get_column_data(3)
            usernames = user_manage.get_column_data(2)
            print(f"按姓名 '{target_name}' 搜索结果: {names}")
            assert target_name in names, f"姓名搜索结果不匹配，预期包含: {target_name}, 实际: {names}"
            assert username in usernames, f"姓名搜索结果未包含闭环用户 {username}: {usernames}"

            user_manage.click_reset_button()
            target_phone = CREATED_PHONE
            user_manage.input_search_username(target_phone)
            user_manage.click_search_button()

            phones = user_manage.get_column_data(4)
            usernames = user_manage.get_column_data(2)
            print(f"按手机号 '{target_phone}' 搜索结果: {phones}")
            assert target_phone in phones, f"手机号搜索结果不匹配，预期包含: {target_phone}, 实际: {phones}"
            assert username in usernames, f"手机号搜索结果未包含闭环用户 {username}: {usernames}"

            user_manage.click_reset_button()
            print("========== SY-USER-013 测试通过 ==========")
        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    def test_014_reset_password_success(self, driver_setup):
        """SY-USER-014: 重置密码成功（操作对象=刚新增并已编辑用户）"""
        driver = driver_setup
        user_manage = UserManagePage(driver)
        print("\n========== 用例 SY-USER-014：重置密码成功 ==========")
        
        try:
            target_user = self._require_created_username()
            self._search_by_username(user_manage, target_user)
            if user_manage.get_table_row_count() == 0:
                pytest.fail(f"用户 '{target_user}' 不存在，无法重置密码")

            user_manage.click_more_user(target_user)
            user_manage.click_more_reset_pwd()
            user_manage.confirm_reset_password_message_box()
            toast_text = user_manage.get_toast_text(timeout=5)
            assert "重置成功" in toast_text and "新密码为" in toast_text and DEFAULT_PASSWORD in toast_text, f"重置密码提示失败: {toast_text}"
            print("========== SY-USER-014 测试通过 ==========")
        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    def test_015_batch_delete_created_user(self, driver_setup):
        """SY-USER-015: 批量删除（删除测试放最后，包含刚新增用户和本用例新增用户）"""
        driver = driver_setup
        user_manage = UserManagePage(driver)
        print("\n========== 用例 SY-USER-015：批量删除（含两条测试用户） ==========")

        try:
            global CREATED_USERNAME, CREATED_DAY_TAG, CREATED_PHONE, CREATED_NAME, UPDATED_NAME
            username = self._require_created_username()
            base_tag = CREATED_DAY_TAG or datetime.now().strftime("%Y%m%d%H%M")
            # 用户名限制 2 到 20 个字符；主用户 test_yyyyMMddHHmm 长度 17，批量用户用 test_yyyyMMddHHmm_b 长度 19。
            batch_username = f"test_{base_tag}_b"
            batch_phone = "137" + base_tag[-8:]
            batch_name = f"测试{base_tag}批量删除"

            self._add_user(
                user_manage,
                username=batch_username,
                name=batch_name,
                phone=batch_phone,
            )

            user_manage.click_reset_button()
            user_manage.input_search_username(base_tag)
            user_manage.click_search_button()

            expected_users = [username, batch_username]
            usernames = user_manage.get_column_data(2)
            print(f"批量删除前搜索关键字 '{base_tag}' 的用户名结果: {usernames}")
            for u in expected_users:
                assert u in usernames, f"批量删除前未查询到用户 {u}，实际结果: {usernames}"
                user_manage.select_user_checkbox(u)

            user_manage.click_batch_delete_button()
            user_manage.confirm_delete_message_box()
            toast = user_manage.get_toast_text(timeout=4)
            assert "成功" in toast or "删除" in toast or toast, f"批量删除提示异常: {toast}"

            for u in expected_users:
                self._search_by_username(user_manage, u)
                assert not user_manage.is_username_present(u), f"批量删除后仍能查到用户名: {u}"

            CREATED_USERNAME = None
            CREATED_DAY_TAG = None
            CREATED_PHONE = None
            CREATED_NAME = None
            UPDATED_NAME = None
        except Exception as e:
            pytest.fail(f"测试失败：{e}")

if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
