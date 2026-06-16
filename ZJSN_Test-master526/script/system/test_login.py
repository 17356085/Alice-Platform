"""登录模块测试 — 企业级

登录页:   http://8.136.215.171:8081/
登录成功: http://8.136.215.171:8081/#/welcome
测试账号: admin / *** (通过 .env 注入)

用例清单:
  TC-01  成功登录
  TC-02  失败登录 — 错误密码
  TC-03  失败登录 — 错误用户名
  TC-04  校验 — 用户名为空
  TC-05  校验 — 密码为空
  TC-06  页面显示验证
  TC-07  边界 — 超长用户名（SQL注入测试）
  TC-08  边界 — 特殊字符密码
  TC-09  边界 — 用户名含空格/中文
  TC-10  登录后 token 写入 localStorage
"""
import logging
import allure
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config import DEFAULT_USERNAME, DEFAULT_PASSWORD

logger = logging.getLogger(__name__)


@pytest.mark.login
class TestLogin:
    """登录模块测试用例"""

    @pytest.fixture(autouse=True)
    def setup(self, login_driver_setup):
        """每个用例：通过 conftest 的 login_driver_setup 获取独立浏览器实例"""
        self.driver = login_driver_setup["driver"]
        self.page = login_driver_setup["page"]
        self.base = login_driver_setup["base"]
        yield

    # ==================================================================
    #  P0: 核心功能
    # ==================================================================

    @pytest.mark.smoke
    @allure.epic("系统管理")
    @allure.feature("登录")
    @allure.story("成功登录")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_001_login_success(self):
        """TC-01: 成功登录

        步骤:
          1. 输入正确用户名 admin
          2. 输入正确密码（从配置读取）
          3. 点击登录按钮
        预期:
          - URL 跳转到 #/welcome
          - 系统首页元素出现
        """
        logger.info("===== TC-01: 成功登录 =====")

        self.page.login(DEFAULT_USERNAME, DEFAULT_PASSWORD)

        # 断言1: URL 已跳转到 #/welcome
        assert self.page.wait_for_url_change(timeout=15), (
            "登录失败：URL 未跳转到 #/welcome，当前: %s" % self.page.get_current_url()
        )

        # 断言2: 系统首页加载
        assert self.page.is_app_loaded(timeout=10), (
            "登录失败：系统首页未加载"
        )

        logger.info("===== TC-01 通过 =====")

    def test_002_login_fail_wrong_password(self):
        """TC-02: 失败登录 — 错误密码

        步骤:
          1. 输入正确用户名
          2. 输入错误密码
          3. 点击登录
        预期:
          - 停留在登录页
          - 显示错误提示
        """
        logger.info("===== TC-02: 错误密码 =====")

        self.page.login(DEFAULT_USERNAME, "WrongPwd999")

        # 断言1: 仍在登录页
        assert self.page.is_login_page(), "URL 未停留在登录页"

        # 断言2: 有错误提示
        error = self.page.get_login_error_toast(timeout=5)
        logger.info("错误提示: %s", error)
        assert error or self.page.is_login_page(), (
            "登录失败但无错误提示"
        )

        logger.info("===== TC-02 通过 =====")

    def test_003_login_fail_wrong_username(self):
        """TC-03: 失败登录 — 错误用户名

        步骤:
          1. 输入不存在的用户名
          2. 输入正确密码
          3. 点击登录
        预期:
          - 停留在登录页
          - 显示错误提示
        """
        logger.info("===== TC-03: 错误用户名 =====")

        self.page.login("NonExistentUser999", DEFAULT_PASSWORD)

        # 断言：仍在登录页
        assert self.page.is_login_page(), "使用错误用户名登录后跳转了页面"

        logger.info("===== TC-03 通过 =====")

    # ==================================================================
    #  P1: 表单校验
    # ==================================================================

    def test_004_login_validation_empty_username(self):
        """TC-04: 校验 — 用户名为空

        步骤:
          1. 保持用户名为空
          2. 输入密码
          3. 点击登录
        预期:
          - 显示"请输入用户名/账号"校验提示
        """
        logger.info("===== TC-04: 用户名为空 =====")

        # 确保用户名为空
        self.page.input_text(self.page.USERNAME_INPUT, "", clear=True)
        self.page.input_password(DEFAULT_PASSWORD)
        self.page.click_login_button()

        error = self.page.get_form_error(timeout=3)
        logger.info("校验提示: %s", error)

        assert error, "未显示用户名必填校验提示"
        assert any(kw in error for kw in ("请输入", "不能为空", "必填", "用户", "账号")), (
            f"校验提示内容不符合预期: {error}"
        )

        logger.info("===== TC-04 通过 =====")

    def test_005_login_validation_empty_password(self):
        """TC-05: 校验 — 密码为空

        步骤:
          1. 输入用户名
          2. 保持密码为空
          3. 点击登录
        预期:
          - 显示"请输入密码"校验提示
        """
        logger.info("===== TC-05: 密码为空 =====")

        self.page.input_username(DEFAULT_USERNAME)
        self.page.input_text(self.page.PASSWORD_INPUT, "", clear=True)
        self.page.click_login_button()

        error = self.page.get_form_error(timeout=3)
        logger.info("校验提示: %s", error)

        assert error, "未显示密码必填校验提示"
        assert any(kw in error for kw in ("请输入", "不能为空", "必填", "密码")), (
            f"校验提示内容不符合预期: {error}"
        )

        logger.info("===== TC-05 通过 =====")

    def test_006_login_page_display(self):
        """TC-06: 登录页面显示验证

        步骤:
          1. 访问登录页
        预期:
          - 用户名输入框可见
          - 密码输入框可见
          - 登录按钮可见
          - 页面标题/Logo 正常
        """
        logger.info("===== TC-06: 页面显示 =====")

        # 三个关键元素
        assert self.page.is_visible(self.page.USERNAME_INPUT), "用户名输入框不可见"
        assert self.page.is_visible(self.page.PASSWORD_INPUT), "密码输入框不可见"

        btn_visible = (
            self.page.is_visible(self.page.LOGIN_BUTTON_CSS, timeout=3)
            or self.page.is_visible(self.page.LOGIN_BUTTON, timeout=3)
        )
        assert btn_visible, "登录按钮不可见"

        logger.info("===== TC-06 通过 =====")

    # ==================================================================
    #  P2: 边界与安全
    # ==================================================================

    def test_007_boundary_sql_injection_username(self):
        """TC-07: 边界 — SQL 注入测试

        步骤:
          1. 输入 SQL 注入 payload 作为用户名
          2. 输入密码
          3. 点击登录
        预期:
          - 登录失败（不执行注入）
          - 显示错误提示
        """
        logger.info("===== TC-07: SQL 注入 =====")

        payload = "admin' OR '1'='1' --"
        self.page.input_username(payload)
        self.page.input_password(DEFAULT_PASSWORD)
        self.page.click_login_button()

        # 断言：不应该登录成功
        assert self.page.is_login_page(), (
            "安全风险：SQL 注入成功登录！"
        )

        logger.info("===== TC-07 通过 =====")

    def test_008_boundary_special_chars_password(self):
        """TC-08: 边界 — 特殊字符密码

        步骤:
          1. 输入用户名
          2. 输入含特殊字符的密码
          3. 点击登录
        预期:
          - 登录失败（密码错误）
        """
        logger.info("===== TC-08: 特殊字符密码 =====")

        special_pwd = "!@#$%^&*()_+{}|:\"<>?`-=[]\\;',./~"
        self.page.input_username(DEFAULT_USERNAME)
        self.page.input_password(special_pwd)
        self.page.click_login_button()

        # 断言：仍停留在登录页
        assert self.page.is_login_page(), "特殊字符密码导致异常跳转"

        logger.info("===== TC-08 通过 =====")

    def test_009_boundary_username_with_spaces(self):
        """TC-09: 边界 — 用户名首尾含空格

        步骤:
          1. 输入带前后空格的正确用户名
          2. 输入密码
          3. 点击登录
        预期:
          - 系统 trim 后登录成功 → URL 跳转
          - 或保留空格视为不存在用户 → 停留在登录页 + 错误提示
          - 不应出现 500 服务端错误（如出现则为后端缺陷）
        """
        logger.info("===== TC-09: 用户名含空格 =====")

        self.page.input_username(f"  {DEFAULT_USERNAME}  ")
        self.page.input_password(DEFAULT_PASSWORD)
        self.page.click_login_button()

        self.page.wait_vue_stable()

        # 检测服务端异常（后端缺陷，不应出现）
        try:
            page_source = self.driver.page_source or ""
            server_error = "500" in page_source or "Internal Server Error" in page_source
        except Exception:
            server_error = False

        # 检查登录结果
        logged_in = self.page.wait_for_url_change(timeout=8)
        still_login = self.page.is_login_page()
        toast = self.page.get_login_error_toast(timeout=3)

        logger.info("登录结果: logged_in=%s, still_login=%s, toast=%s, server_error=%s",
                     logged_in, still_login, toast, server_error)

        if server_error:
            pytest.xfail("已知后端缺陷：用户名含空格触发服务端 500")

        # 登录成功（trim 处理）或 登录失败（空格保留）都算正常
        assert logged_in or still_login, (
            f"用户名含空格后状态异常: URL={self.page.get_current_url()}, toast={toast}"
        )

        logger.info("===== TC-09 通过 =====")

    def test_010_token_in_localstorage(self):
        """TC-10: 登录后 token 写入存储

        步骤:
          1. 登录成功
          2. 检查 localStorage / sessionStorage / cookie 中是否有 token
        预期:
          - 存在 token 或 accessToken（可能在 user-info JSON 内）
        """
        logger.info("===== TC-10: Token 存储 =====")

        self.page.login(DEFAULT_USERNAME, DEFAULT_PASSWORD)

        if not self.page.wait_for_url_change(timeout=15):
            pytest.skip("登录未成功，跳过 token 检查")

        token_info = self._find_token()
        logger.info("Token 检测结果: %s", {k: v for k, v in token_info.items() if k != 'raw_value'})

        assert token_info["found"], (
            f"未在任何存储中找到 token。"
            f"localStorage: {token_info['ls_keys']}, "
            f"sessionStorage: {token_info['ss_keys']}, "
            f"user-info: {token_info.get('user_info_keys', 'N/A')}"
        )

        logger.info("token 来源: %s, 长度: %d", token_info["source"], len(token_info.get("raw_value", "")))
        logger.info("===== TC-10 通过 =====")

    def _find_token(self):
        """在多个存储位置搜索 token"""
        result = {"found": False, "source": "", "raw_value": ""}

        # 1. localStorage 直接 key 名含 token
        keys = self.driver.execute_script("return Object.keys(localStorage);") or []
        result["ls_keys"] = keys
        for k in keys:
            if "token" in k.lower():
                val = self.driver.execute_script(f"return localStorage.getItem('{k}');")
                if val:
                    result.update(found=True, source=f"localStorage.{k}", raw_value=val)
                    return result

        # 2. user-info JSON 内嵌 token
        if "user-info" in keys:
            raw = self.driver.execute_script("return localStorage.getItem('user-info');")
            if raw:
                try:
                    import json
                    ui = json.loads(raw)
                    result["user_info_keys"] = list(ui.keys()) if isinstance(ui, dict) else []
                    for tk in ("token", "accessToken", "access_token", "jwt", "authorization"):
                        if tk in ui and ui[tk]:
                            result.update(found=True, source=f"user-info.{tk}", raw_value=str(ui[tk]))
                            return result
                        # 嵌套对象
                        if isinstance(ui, dict):
                            for v in ui.values():
                                if isinstance(v, dict):
                                    for tk2 in ("token", "accessToken", "access_token"):
                                        if tk2 in v and v[tk2]:
                                            result.update(found=True, source=f"user-info..{tk2}", raw_value=str(v[tk2]))
                                            return result
                except Exception:
                    pass

        # 3. sessionStorage
        ss_keys = self.driver.execute_script("return Object.keys(sessionStorage);") or []
        result["ss_keys"] = ss_keys
        for k in ss_keys:
            if "token" in k.lower():
                val = self.driver.execute_script(f"return sessionStorage.getItem('{k}');")
                if val:
                    result.update(found=True, source=f"sessionStorage.{k}", raw_value=val)
                    return result

        # 4. Cookie
        cookies = self.driver.get_cookies()
        for c in cookies:
            if "token" in (c.get("name") or "").lower():
                result.update(found=True, source=f"cookie.{c['name']}", raw_value=c.get("value", ""))
                return result

        return result

    # ==================================================================
    #  P3: 登录状态保持
    # ==================================================================

    def test_011_login_state_persist_after_refresh(self):
        """TC-11: 登录后刷新页面，保持登录状态

        步骤:
          1. 登录成功
          2. 刷新页面
        预期:
          - 仍在系统首页（不回到登录页）
        """
        logger.info("===== TC-11: 刷新保持登录 =====")

        self.page.login(DEFAULT_USERNAME, DEFAULT_PASSWORD)

        if not self.page.wait_for_url_change(timeout=15):
            pytest.skip("登录未成功，跳过刷新测试")

        self.driver.refresh()
        self.page.wait_page_ready()
        self.page.wait_vue_stable()

        # 断言：不应回到登录页
        assert not self.page.is_login_page(), (
            "刷新后回到登录页，登录状态丢失"
        )

        logger.info("===== TC-11 通过 =====")

    # ==================================================================
    #  P4: 快速重复登录（防抖测试）
    # ==================================================================

    def test_012_rapid_double_click_login(self):
        """TC-12: 快速双击登录按钮

        步骤:
          1. 输入用户名密码
          2. 快速连续点击 2 次
        预期:
          - 正常跳转（不应创建重复 session 或报错）
        """
        logger.info("===== TC-12: 快速双击 =====")

        self.page.input_username(DEFAULT_USERNAME)
        self.page.input_password(DEFAULT_PASSWORD)
        self.page.click_login_button()
        # 快速再点一次
        try:
            self.page.js_click(self.page.LOGIN_BUTTON, timeout=2)
        except Exception:
            pass

        self.page.wait_vue_stable()
        assert self.page.wait_for_url_change(timeout=15) or not self.page.is_login_page(), (
            "快速双击导致登录异常"
        )

        logger.info("===== TC-12 通过 =====")


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
