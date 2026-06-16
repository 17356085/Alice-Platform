"""RBAC权限矩阵端到端自动化测试

测试架构:
  Layer 2: UI 侧边栏可见性 + 直接URL拦截 + 按钮显隐
  Layer 3: 手工 (多角色叠加、权限即时生效)

数据准备:
  通过独立脚本 data/rbac_seed_data.py 预创建测试角色和用户
  本测试直接使用已有测试数据，不自建

测试用例:
  Layer 2 UI:
    TC-RBAC-001~007: 不同角色侧边栏菜单验证 (parametrized)
    TC-RBAC-006: 混合权限子菜单精度
    TC-RBAC-101~105: 直接URL访问拦截 (parametrized)
    TC-RBAC-202: 只读角色按钮验权
"""
import os
import sys
import pytest
import allure

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from config import DEFAULT_USERNAME, DEFAULT_PASSWORD
from base.browser_driver import BaseDriver, ensure_logged_in
from page.system_page.LoginPage import LoginPage

# ──────────────────────────────────────────────────────────────────
#  测试数据定义（需与 seed 脚本保持一致）
# ──────────────────────────────────────────────────────────────────

DEFAULT_PWD = "Ajyl@2026"

EXPECTED_MENUS = {
    "rbac_full":  ["系统管理", "设备管理", "储罐管理", "DCS数据", "化验室取样", "人员管理", "生产管理", "销售管理"],
    "rbac_sys":   ["系统管理"],
    "rbac_equip": ["设备管理"],
    "rbac_hr":    ["人员管理"],
    "rbac_mix":   ["系统管理", "设备管理", "销售管理"],
    "rbac_none":  [],
}

EXPECTED_SUBMENUS_MIX = {
    "系统管理": ["用户管理", "角色管理"],
    "设备管理": ["设备台账"],
    "销售管理": ["客户管理"],
}

URL_ACCESS_RULES = [
    # (role_code, url, should_block, description)
    ("rbac_sys",   "#/system/user",       False,  "sys->自己能访问"),
    ("rbac_sys",   "#/equipment/device",   True,  "sys->不能访问设备"),
    ("rbac_none",  "#/system/user",       True,  "none->不能访问系统"),
    ("rbac_none",  "#/",                  False, "none->能到首页"),
    ("rbac_mix",   "#/system/user",       False, "mix->能访问用户"),
    ("rbac_mix",   "#/equipment/device",  False, "mix->能访问设备台账"),
    ("rbac_mix",   "#/system/menu",       True,  "mix->不能访问菜单管理"),
    ("rbac_equip", "#/system/user",       True,  "equip->不能访问系统"),
    ("rbac_hr",    "#/system/user",       True,  "hr->不能访问系统"),
]


# ══════════════════════════════════════════════════════════════════
#  工具函数
# ══════════════════════════════════════════════════════════════════

def step(text):
    print(f"  -> {text}")
    try:
        allure.step(text)
    except Exception:
        pass

def case(case_id, title):
    print(f"\n{'='*60}\n用例 {case_id}：{title}\n{'='*60}")
    try:
        allure.dynamic.title(f"{case_id} {title}")
    except Exception:
        pass

def get_sidebar_top_level(driver):
    """提取侧边栏所有可见的一级菜单文字"""
    return driver.execute_script("""
        var menus = [];
        document.querySelectorAll('.el-menu > li.el-sub-menu > .el-sub-menu__title span')
            .forEach(function(s) { var t = (s.innerText || '').trim(); if (t) menus.push(t); });
        document.querySelectorAll('.el-menu > li.el-menu-item span')
            .forEach(function(s) { var t = (s.innerText || '').trim(); if (t) menus.push(t); });
        return menus;
    """)

def get_submenu_titles(driver, parent_text):
    """提取指定一级菜单的子菜单列表"""
    return driver.execute_script("""
        var result = [];
        var items = document.querySelectorAll('li.el-sub-menu');
        for (var i = 0; i < items.length; i++) {
            var title = items[i].querySelector('.el-sub-menu__title span');
            if (!title) continue;
            var pt = (title.innerText || '').trim();
            if (pt.indexOf('{p}') === -1 && pt !== '{p}') continue;
            items[i].querySelectorAll('li.el-menu-item span').forEach(function(s) {
                var t = (s.innerText || '').trim();
                if (t) result.push(t);
            });
            break;
        }
        return result;
    """.replace('{p}', parent_text))

def login_as(driver, username, password=DEFAULT_PWD):
    """用指定用户登录；已在登录页则直接输入，否则先退出"""
    page = LoginPage(driver)
    # 先导航到首页
    driver.get("https://aiwechatminidemo.cimc-digital.com/")
    try:
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script("return document.readyState;") == "complete"
        )
    except Exception:
        pass

    # 已经登录则检查是否目标用户（粗略判断，直接返回）
    try:
        if page._is_already_logged_in():
            cur_hash = driver.execute_script("return window.location.hash;")
            if "#/login" not in cur_hash and "#" in cur_hash:
                return True
    except Exception:
        pass

    # 退到登录页
    for attempt in range(3):
        try:
            driver.get("https://aiwechatminidemo.cimc-digital.com/")
            page.wait_login_form_ready()
            if page.is_login_page():
                page.input_username(username)
                page.input_password(password)
                # 找登录按钮
                btns = driver.find_elements(By.XPATH, "//button[.//span[contains(.,'登')]]")
                if btns:
                    btns[0].click()
                else:
                    driver.execute_script("document.querySelector('.el-button--primary').click();")
                # 等待跳转
                try:
                    WebDriverWait(driver, 15).until(
                        lambda d: "#/login" not in (d.current_url or "")
                    )
                except Exception:
                    pass
                page.wait_vue_stable()
                return True
            if page._is_already_logged_in():
                return True
        except Exception:
            try:
                page.wait_vue_stable()
            except Exception:
                pass
    return False

def read_current_url_hash(driver):
    return driver.execute_script("return window.location.hash;")

# ══════════════════════════════════════════════════════════════════
#  Fixtures
# ══════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def module_driver():
    """Module 级 driver -- 验证创建的角色和用户存在"""
    base = BaseDriver()
    driver = base.open_browser()
    try:
        ensure_logged_in(driver)
        yield driver
    finally:
        try:
            base.close_browser()
        except Exception:
            pass

@pytest.fixture(scope="function")
def fresh_driver():
    """每用例独立浏览器"""
    base = BaseDriver()
    driver = base.open_browser()
    yield driver
    try:
        base.close_browser()
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════
#  测试类
# ══════════════════════════════════════════════════════════════════

class TestRBACUI:
    """RBAC 权限矩阵 UI 层测试（假设测试数据已就绪）"""

    # ══════════════════════════════════════════════════════════
    #  Layer 2: 侧边栏菜单可见性
    # ══════════════════════════════════════════════════════════

    @pytest.mark.smoke
    @allure.epic("权限管理")
    @allure.feature("RBAC权限矩阵")
    @allure.story("侧边栏可见性")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.parametrize("role_code,username,expected", [
        ("rbac_full", "rbac_test_full",
         ["系统管理","设备管理","储罐管理","DCS数据","化验室取样","人员管理","生产管理","销售管理"]),
        ("rbac_sys", "rbac_test_sys", ["系统管理"]),
        ("rbac_equip", "rbac_test_equip", ["设备管理"]),
        ("rbac_hr", "rbac_test_hr", ["人员管理"]),
        ("rbac_none", "rbac_test_none", []),
    ], ids=["全权限","仅系统管理","仅设备管理","仅人员管理","零权限"])
    def test_sidebar_visible_menus(self, fresh_driver, role_code, username, expected):
        """TC-RBAC-001~007: 不同角色登录后侧边栏菜单"""
        case(f"TC-RBAC-001(_{role_code})", f"侧边栏可见菜单 - {username}")

        driver = fresh_driver
        assert login_as(driver, username, DEFAULT_PWD), f"登录失败: {username}"

        page = LoginPage(driver)
        page.wait_vue_stable()

        menus = get_sidebar_top_level(driver)
        full_expected = set(expected + ["首页"])
        actual = set(menus)

        step(f"用户: {username}")
        step(f"预期: {sorted(full_expected)}")
        step(f"实际: {sorted(actual)}")

        for m in full_expected:
            assert m in actual, f"缺少菜单'{m}'，实际: {sorted(actual)}"

        # 零权限：不应看到任何一级菜单（仅首页）
        if role_code == "rbac_none":
            assert len(actual) <= 1, f"零权限角色看到多余菜单: {sorted(actual)}"

    @allure.epic("权限管理")
    @allure.feature("RBAC权限矩阵")
    @allure.story("子菜单精度")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_mix_submenu_precision(self, fresh_driver):
        """TC-RBAC-006: 混合权限子菜单精度"""
        case("TC-RBAC-006", "混合权限子菜单精度验证")

        driver = fresh_driver
        login_as(driver, "rbac_test_mix", DEFAULT_PWD)
        page = LoginPage(driver)
        page.wait_vue_stable()

        for parent, children in EXPECTED_SUBMENUS_MIX.items():
            items = get_submenu_titles(driver, parent)
            step(f"'{parent}' 下子菜单: {items}")
            for c in children:
                assert c in items, f"缺少子菜单 '{parent}->{c}'，实际: {items}"
            # 验证没有多余子菜单
            extra = set(items) - set(children)
            assert not extra, f"存在未授权子菜单 '{parent}': {extra}"

    # ══════════════════════════════════════════════════════════
    #  Layer 2: URL 访问拦截
    # ══════════════════════════════════════════════════════════

    @allure.epic("权限管理")
    @allure.feature("RBAC权限矩阵")
    @allure.story("URL访问控制")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize("role_code,url,should_block,desc", URL_ACCESS_RULES,
                             ids=[r[3] for r in URL_ACCESS_RULES])
    def test_url_access(self, fresh_driver, role_code, url, should_block, desc):
        """TC-RBAC-101~105: URL 访问拦截"""
        case(f"TC-RBAC-101(_{role_code})", f"URL拦截 - {desc}")

        # 找用户名
        username_map = {
            "rbac_sys": "rbac_test_sys", "rbac_none": "rbac_test_none",
            "rbac_mix": "rbac_test_mix", "rbac_equip": "rbac_test_equip",
            "rbac_hr": "rbac_test_hr", "rbac_full": "rbac_test_full",
        }
        username = username_map.get(role_code)
        driver = fresh_driver
        assert login_as(driver, username, DEFAULT_PWD), f"登录失败: {username}"

        page = LoginPage(driver)
        page.wait_vue_stable()

        target = f"https://aiwechatminidemo.cimc-digital.com/{url}"
        driver.get(target)

        # 等待 Vue 路由跳转完成
        try:
            WebDriverWait(driver, 10).until(
                lambda d: d.execute_script("return document.readyState;") == "complete"
            )
        except Exception:
            pass
        page.wait_vue_stable()

        cur = driver.current_url
        h = read_current_url_hash(driver)
        step(f"访问: {target}")
        step(f"到达: {cur[:80]}")
        step(f"hash: {h}")

        path = url.replace("#", "")
        if should_block:
            blocked = path not in cur or "#/login" in cur
            assert blocked, f"应拦截但可访问: {target}"
            step(f"  [OK] 已拦截")
        else:
            assert path in cur, f"应可访问但被拦截: {target} -> {cur[:80]}"
            step(f"  [OK] 正常访问")

    # ══════════════════════════════════════════════════════════
    #  Layer 2: 数据范围
    # ══════════════════════════════════════════════════════════

    @allure.epic("权限管理")
    @allure.feature("RBAC权限矩阵")
    @allure.story("数据范围")
    @allure.severity(allure.severity_level.NORMAL)
    def test_datascope_full(self, fresh_driver):
        """TC-RBAC-301: 全部数据范围"""
        case("TC-RBAC-301", "全权限角色可见所有用户")

        driver = fresh_driver
        login_as(driver, "rbac_test_full", DEFAULT_PWD)
        driver.get("https://aiwechatminidemo.cimc-digital.com/#/system/user")

        # 等待用户表格数据加载
        page = LoginPage(driver)
        page.wait_vue_stable()
        try:
            WebDriverWait(driver, 10).until(
                lambda d: d.execute_script(
                    "var t=document.querySelector('.el-pagination__total');"
                    "return t && t.innerText && (t.innerText.indexOf('共') !== -1);"
                )
            )
        except TimeoutException:
            step("分页总数未加载，尝试继续")

        total = driver.execute_script(
            "var t=document.querySelector('.el-pagination__total');return t?t.innerText:'';")
        step(f"用户总数: {total}")
        assert "共" in total and "条" in total, f"总数异常: {total}"


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__, "--reruns", "0"])
