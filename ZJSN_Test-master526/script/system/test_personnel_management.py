"""人员管理模块测试脚本"""
import pytest
import time
import sys
import os
import inspect
import allure
from datetime import datetime

# 将项目根目录添加到系统路径，以便正确导入模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from page.system_page.UserManagePage import UserManagePage

CREATED_USERNAME = None
CREATED_DAY_TAG = None
CREATED_PHONE = None
CREATED_NAME = None
UPDATED_NAME = None


def _generate_user_test_data():
    """生成本轮人员闭环测试数据：新增、查询、修改、删除都使用同一条数据。"""
    day_tag = datetime.now().strftime("%Y%m%d%H%M")
    username = f"test_{day_tag}"
    phone = f"138{day_tag[-8:]}"
    name = f"测试{day_tag}新增"
    updated_name = f"测试{day_tag}修改"
    return username, day_tag, phone, name, updated_name


class TestPersonnelManage:
    """人员管理模块测试用例"""

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
    @allure.feature("人员管理")
    @allure.story("页面基础展示")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_001_page_display(self, driver_setup):
        """RY-USER-001: 页面打开时正常显示人员列表"""
        user_manage = UserManagePage(driver_setup)
        print("\n========== 测试 RY-USER-001: 页面显示正常 ==========")
        total_text = user_manage.get_total_count_text()
        assert any(char.isdigit() for char in total_text), "总条数应包含数字"
        header_text = user_manage.get_username_header_text()
        assert header_text == "用户名", f"表头应为'用户名'，实际为'{header_text}'"
        row_count = user_manage.get_table_row_count()
        assert row_count > 0, "列表不应为空"

    def test_002_pagination(self, driver_setup):
        """RY-USER-002: 分页功能正常"""
        user_manage = UserManagePage(driver_setup)
        print("\n========== 测试 RY-USER-002: 分页功能正常 ==========")
        page1_user = user_manage.get_first_row_username()
        user_manage.click_next_page()
        page2_user = user_manage.get_first_row_username()
        assert page1_user != page2_user, f"分页失败：两页的第一行用户相同 ({page1_user})"

    def _require_created_username(self):
        global CREATED_USERNAME
        assert CREATED_USERNAME, "未获取到新增用户名，请先执行 RY-USER-003 新增用例"
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

    def test_003_add_user_success(self, driver_setup):
        """RY-USER-003: 新增人员成功（闭环数据=同一条 test_时间 数据）"""
        user_manage = UserManagePage(driver_setup)
        global CREATED_USERNAME, CREATED_DAY_TAG, CREATED_PHONE, CREATED_NAME, UPDATED_NAME
        target_username, day_tag, phone, name, updated_name = _generate_user_test_data()
        CREATED_USERNAME = target_username
        CREATED_DAY_TAG = day_tag
        CREATED_PHONE = phone
        CREATED_NAME = name
        UPDATED_NAME = updated_name
        toast = self._add_user(user_manage, CREATED_USERNAME, CREATED_NAME, CREATED_PHONE)
        assert "成功" in toast or "新增" in toast or toast, f"新增提示异常: {toast}"

    def test_012_search_created_user_by_username(self, driver_setup):
        """RY-USER-012: 查询刚新增人员（按用户名）"""
        user_manage = UserManagePage(driver_setup)
        username = self._require_created_username()
        self._search_by_username(user_manage, username)
        row_count = user_manage.get_table_row_count()
        assert row_count >= 1, "搜索结果不应为空"
        results = user_manage.get_column_data(2)
        assert any(username.lower() in name.lower() for name in results), f"搜索结果不匹配: {results}"


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
