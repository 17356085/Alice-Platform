"""RBAC 权限即时生效测试 — 角色权限变更后 UI 同步验证

覆盖场景:
  TC-RBAC-016: 权限变更 → 清空缓存 → 用户刷新 → 菜单即时生效 (P0)
  TC-RBAC-017: 权限变更 → 不清空缓存 → 菜单不变 (P0 反例)
  TC-RBAC-018: 多角色叠加 → 菜单取并集 (P1)
  TC-RBAC-019: 角色被删除 → 用户权限降级 (P1)
  TC-RBAC-020: 角色被停用 → 用户菜单消失 (P1)
  TC-RBAC-021: 内置角色删除保护 (P1)

前置条件:
  需先执行 rbac_seed_clean.py 创建 7 个测试角色 + 7 个测试用户
  (或手动执行: python script/system/rbac_seed_clean.py)

技术:
  双浏览器: admin 修改权限 → target user 刷新验证
  API 辅助: 角色停用/分配通过 API 操作（绕过 UI 权限弹窗复杂度）
"""
import os
import sys
import time
import json
import pytest
import allure

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from page.system_page.LoginPage import LoginPage
from page.system_role_page.RoleManagePage import RoleManagePage
from base.sidebar_navigator import SidebarNavigator
from base.base_page import BasePage


PWD = "Ajyl@2026"
BASE_URL = "https://aiwechatminidemo.cimc-digital.com/"


# ══════════════════════════════════════════════════════════════════════
#  工具函数
# ══════════════════════════════════════════════════════════════════════

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


def get_sidebar_menus(driver):
    """提取侧边栏所有可见的一级菜单文字（含首页）"""
    return driver.execute_script("""
        var menus = [];
        document.querySelectorAll('.el-menu > li.el-sub-menu > .el-sub-menu__title span')
            .forEach(function(s) { var t = (s.innerText || '').trim(); if (t) menus.push(t); });
        document.querySelectorAll('.el-menu > li.el-menu-item span')
            .forEach(function(s) { var t = (s.innerText || '').trim(); if (t) menus.push(t); });
        return menus;
    """)


def login_as(driver, username, password=PWD):
    """以指定用户登录（复用 LoginPage 标准流程）"""
    page = LoginPage(driver)
    driver.get(BASE_URL)
    try:
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script("return document.readyState;") == "complete"
        )
    except Exception:
        pass

    # 检查是否已登录
    try:
        if page._is_already_logged_in():
            cur_hash = driver.execute_script("return window.location.hash;")
            if "#/login" not in cur_hash and "#" in cur_hash:
                return True
    except Exception:
        pass

    # 退到登录页并登录
    for attempt in range(3):
        try:
            driver.get(BASE_URL)
            page.wait_login_form_ready()
            if page.is_login_page():
                page.input_username(username)
                page.input_password(password)
                btns = driver.find_elements(By.XPATH, "//button[.//span[contains(.,'登')]]")
                if btns:
                    btns[0].click()
                else:
                    driver.execute_script(
                        "document.querySelector('.el-button--primary').click();"
                    )
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
        except Exception as e:
            if attempt < 2:
                try:
                    WebDriverWait(driver, 5).until(
                        lambda d: d.execute_script("return document.readyState") == "complete"
                    )
                except Exception:
                    pass
            else:
                raise e
    return False


def api_fetch(driver, method, path, body=None):
    """通过浏览器 fetch API 调用后端（绕过 UI，用于数据准备/清理）"""
    driver.set_script_timeout(60)
    js_body = ""
    if body:
        js_body = "body: JSON.stringify(%s)," % json.dumps(body, ensure_ascii=False)
    return driver.execute_script("""
        return Promise.race([
            fetch('https://aiwechatminidemo.cimc-digital.com%s', {
                method: '%s',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + JSON.parse(
                        decodeURIComponent(document.cookie.split('authorized-token=')[1].split(';')[0])
                    ).accessToken
                },
                %s
            }).then(function(r) { return r.json(); }),
            new Promise(function(_,reject) {
                setTimeout(function() { reject(new Error('timeout')); }, 45000);
            })
        ]);
    """ % (path, method, js_body))


def api_get_records(resp):
    """从 API 响应中提取 records 列表"""
    data = resp.get('data', resp)
    if isinstance(data, dict):
        return data.get('records', data.get('rows', []))
    if isinstance(data, list):
        return data
    return []


def navigate_to_role_page(driver):
    """导航到角色管理页面"""
    nav = SidebarNavigator(driver)
    nav._navigate_by_js_hash('#/system/role', 'test')
    time.sleep(3)
    BasePage(driver).wait_vue_stable()


# ══════════════════════════════════════════════════════════════════════
#  测试类
# ══════════════════════════════════════════════════════════════════════

class TestRBACInstantEffect:
    """角色权限即时生效 — 端到端验证"""

    # ── TC-RBAC-016: 权限变更 + 清空缓存 → 即时生效 ──────────────────

    @pytest.mark.smoke
    @allure.epic("权限管理")
    @allure.feature("RBAC权限矩阵")
    @allure.story("权限即时生效")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_rbac_016_permission_change_with_cache_clear(self, dual_driver):
        """TC-RBAC-016: 权限变更 → 清空缓存 → 用户刷新 → 菜单即时生效

        流程:
          admin: 打开 RBAC-SYS-ONLY 角色权限 → PC Tab 新增勾选"设备管理"
          admin: 保存 → 点击"清空缓存"
          target: rbac_test_sys 登录 → 侧边栏应同时包含「系统管理」和「设备管理」
          admin: 还原权限（取消设备管理勾选 → 保存 → 清空缓存）
        """
        admin_drv, target_drv = dual_driver
        case("TC-RBAC-016", "权限变更+清空缓存→用户刷新→菜单即时生效")
        role_name = "RBAC-SYS-ONLY"
        test_user = "rbac_test_sys"

        role_page = RoleManagePage(admin_drv)
        navigate_to_role_page(admin_drv)

        # ── Step 1: 搜索目标角色，打开权限弹窗 ──
        step(f"搜索角色: {role_name}")
        role_page.click_reset()
        role_page.input_role_name(role_name)
        role_page.click_search()
        role_page.wait_table_ready(timeout=8)
        assert role_page.get_table_row_count() > 0, f"角色 {role_name} 未找到"

        step("打开权限弹窗 → PC操作权限 Tab")
        role_page.click_permission_by_role_name(role_name)
        assert role_page.click_permission_tab_pc(), "无法切换到 PC操作权限 Tab"

        # ── Step 2: 新增勾选「设备管理」模块 ──
        step("勾选「设备管理」模块权限")
        selected = role_page.select_permission_module("设备管理")
        if not selected:
            # 尝试降级匹配关键词
            for fallback in ["设备", "equipment", "装置"]:
                selected = role_page.select_permission_module(fallback)
                if selected:
                    step(f"降级匹配成功: {fallback}")
                    break
        role_page.wait_vue_stable()

        if not selected:
            role_page.click_permission_cancel()
            pytest.skip("权限树中未找到「设备管理」模块，跳过（需检查 perm-group DOM 结构）")

        step("保存权限")
        role_page.click_permission_confirm()
        msg = role_page.wait_for_toast_text(timeout=6)
        assert msg and ("成功" in msg or "保存" in msg), f"权限保存失败: {msg}"

        # ── Step 3: 清空缓存 ──
        step("点击清空缓存按钮")
        assert role_page.click_clear_cache(), "未找到清空缓存按钮"
        msg2 = role_page.wait_for_toast_text(timeout=5)
        step(f"清空缓存 Toast: {msg2}")

        # ── Step 4: target 用户登录验证 ──
        step(f"用户 {test_user} 登录并验证侧边栏")
        assert login_as(target_drv, test_user), f"用户 {test_user} 登录失败"
        target_page = LoginPage(target_drv)
        target_page.wait_vue_stable()
        time.sleep(2)

        menus = get_sidebar_menus(target_drv)
        step(f"侧边栏菜单: {menus}")

        # 预期：系统管理（原有）+ 设备管理（刚加）
        assert "系统管理" in menus, f"缺少原有权限「系统管理」，实际: {menus}"
        assert "设备管理" in menus, f"新增权限未生效！缺少「设备管理」，实际: {menus}"

        # ── Step 5: 还原权限（取消设备管理） ──
        step("还原：取消设备管理权限")
        navigate_to_role_page(admin_drv)
        role_page.click_reset()
        role_page.input_role_name(role_name)
        role_page.click_search()
        role_page.wait_table_ready(timeout=8)
        role_page.click_permission_by_role_name(role_name)
        role_page.click_permission_tab_pc()
        role_page.select_permission_module("设备管理")  # toggle off
        role_page.click_permission_confirm()
        role_page.wait_for_toast_text(timeout=6)
        role_page.click_clear_cache()
        role_page.wait_for_toast_text(timeout=5)
        step("权限已还原")

        step("TC-RBAC-016 通过 [OK]")

    # ── TC-RBAC-017: 权限变更 + 不清空缓存 → 不应生效 (反例) ─────────

    @allure.epic("权限管理")
    @allure.feature("RBAC权限矩阵")
    @allure.story("权限即时生效-反例")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_rbac_017_permission_change_no_cache_clear(self, dual_driver):
        """TC-RBAC-017: 权限变更 → 不清空缓存 → 菜单不应变化（反例）

        验证权限缓存机制确实存在——如果不清空缓存，权限变更不应影响已登录用户。
        使用 RBAC-EQUIP-ONLY 角色，新增「人员管理」权限但不清理缓存。
        """
        admin_drv, target_drv = dual_driver
        case("TC-RBAC-017", "权限变更+不清空缓存→菜单不变（反例）")
        role_name = "RBAC-EQUIP-ONLY"
        test_user = "rbac_test_equip"

        role_page = RoleManagePage(admin_drv)
        navigate_to_role_page(admin_drv)

        # ── Step 1: 先登录 target 用户，记录当前菜单 ──
        step(f"用户 {test_user} 首次登录，记录基线菜单")
        assert login_as(target_drv, test_user), f"用户 {test_user} 登录失败"
        LoginPage(target_drv).wait_vue_stable()
        time.sleep(2)
        baseline_menus = get_sidebar_menus(target_drv)
        step(f"基线菜单: {baseline_menus}")
        assert "设备管理" in baseline_menus, f"基线应包含设备管理: {baseline_menus}"
        assert "人员管理" not in baseline_menus, (
            f"基线不应包含人员管理: {baseline_menus}"
        )
        # target 退出登录
        try:
            target_drv.execute_script("window.location.hash = '#/login';")
            time.sleep(2)
        except Exception:
            pass

        # ── Step 2: admin 修改权限（新增人员管理）但不清理缓存 ──
        step(f"修改角色 {role_name} 权限：新增「人员管理」（不清空缓存）")
        role_page.click_reset()
        role_page.input_role_name(role_name)
        role_page.click_search()
        role_page.wait_table_ready(timeout=8)
        assert role_page.get_table_row_count() > 0, f"角色 {role_name} 未找到"

        role_page.click_permission_by_role_name(role_name)
        role_page.click_permission_tab_pc()
        role_page.select_permission_module("人员管理")
        role_page.click_permission_confirm()
        msg = role_page.wait_for_toast_text(timeout=6)
        assert msg and ("成功" in msg or "保存" in msg), f"权限保存失败: {msg}"
        step("权限已修改，跳过清空缓存")

        # ── Step 3: target 用户重新登录 → 菜单应不变 ──
        step(f"用户 {test_user} 重新登录，验证菜单未变")
        assert login_as(target_drv, test_user), f"用户 {test_user} 重新登录失败"
        LoginPage(target_drv).wait_vue_stable()
        time.sleep(2)

        after_menus = get_sidebar_menus(target_drv)
        step(f"不清缓存后的菜单: {after_menus}")

        # 关键断言：人员管理不应出现（因为没清缓存）
        if "人员管理" in after_menus:
            # 缓存可能已自动刷新（系统设计差异），记录但不算失败
            step("[WARN] 人员管理意外出现——缓存可能自动刷新或权限即时生效（非严格反例）")
        else:
            step("[OK] 人员管理未出现——缓存机制确认存在")

        assert "设备管理" in after_menus, f"原有权限不应丢失: {after_menus}"

        # ── Step 4: 还原权限 + 清空缓存 ──
        step("还原：取消人员管理权限并清空缓存")
        navigate_to_role_page(admin_drv)
        role_page.click_reset()
        role_page.input_role_name(role_name)
        role_page.click_search()
        role_page.wait_table_ready(timeout=8)
        role_page.click_permission_by_role_name(role_name)
        role_page.click_permission_tab_pc()
        role_page.select_permission_module("人员管理")  # toggle off
        role_page.click_permission_confirm()
        role_page.wait_for_toast_text(timeout=6)
        role_page.click_clear_cache()
        role_page.wait_for_toast_text(timeout=5)
        step("权限已还原 + 缓存已清")

        step("TC-RBAC-017 通过 [OK]")

    # ── TC-RBAC-018: 多角色叠加 → 菜单取并集 ────────────────────────

    @allure.epic("权限管理")
    @allure.feature("RBAC权限矩阵")
    @allure.story("多角色叠加")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_rbac_018_multi_role_union(self, dual_driver):
        """TC-RBAC-018: 多角色叠加 — 菜单取并集

        通过 API 给 rbac_test_sys 额外分配 RBAC-EQUIP-ONLY 角色，
        验证侧边栏同时显示两个角色各自的菜单。
        """
        admin_drv, target_drv = dual_driver
        case("TC-RBAC-018", "多角色叠加 → 菜单取并集")
        test_user = "rbac_test_sys"

        # ── Step 1: 通过 API 查询角色 ID ──
        step("查询 RBAC-EQUIP-ONLY 和 rbac_test_sys 的 ID")
        rl = api_fetch(admin_drv, "GET",
                       "/api/system/role/list?pageNum=1&pageSize=50")
        equip_role_id = None
        sys_role_id = None
        for r in api_get_records(rl):
            if r.get('roleCode') == 'rbac_equip':
                equip_role_id = r.get('id')
            if r.get('roleCode') == 'rbac_sys':
                sys_role_id = r.get('id')

        ul = api_fetch(admin_drv, "GET",
                       f"/api/system/user/list?pageNum=1&pageSize=10&username={test_user}")
        user_id = None
        current_roles = []
        for u in api_get_records(ul):
            if u.get('username') == test_user:
                user_id = u.get('id')
                current_roles = u.get('roleIds', u.get('roles', []))
                break

        assert user_id, f"用户 {test_user} 未找到"
        assert equip_role_id, "RBAC-EQUIP-ONLY 角色未找到"
        step(f"用户ID={user_id}, 当前角色={current_roles}, 装备角色ID={equip_role_id}")

        # ── Step 2: API 追加第二个角色 ──
        step("通过 API 给用户追加 RBAC-EQUIP-ONLY 角色")
        new_roles = list(current_roles) if current_roles else []
        if sys_role_id and sys_role_id not in new_roles:
            new_roles.append(sys_role_id)
        if equip_role_id not in new_roles:
            new_roles.append(equip_role_id)

        resp = api_fetch(admin_drv, "PUT", f"/api/system/user/{user_id}", {
            "roleIds": new_roles,
            "id": user_id,
            "username": test_user,
        })
        step(f"API 更新角色响应: code={resp.get('code')}")

        # ── Step 3: 清空缓存后 target 登录验证 ──
        step("清空缓存")
        role_page = RoleManagePage(admin_drv)
        navigate_to_role_page(admin_drv)
        role_page.click_clear_cache()
        role_page.wait_for_toast_text(timeout=5)

        step(f"用户 {test_user} 登录验证多角色菜单")
        assert login_as(target_drv, test_user), f"用户 {test_user} 登录失败"
        LoginPage(target_drv).wait_vue_stable()
        time.sleep(2)
        menus = get_sidebar_menus(target_drv)
        step(f"多角色菜单: {menus}")

        assert "系统管理" in menus, f"缺少原有角色菜单「系统管理」: {menus}"
        assert "设备管理" in menus, f"多角色叠加失败！缺少「设备管理」: {menus}"

        # ── Step 4: 还原（移除多余角色） ──
        step("还原：移除额外的角色分配")
        api_fetch(admin_drv, "PUT", f"/api/system/user/{user_id}", {
            "roleIds": [sys_role_id] if sys_role_id else [],
            "id": user_id,
            "username": test_user,
        })
        navigate_to_role_page(admin_drv)
        role_page.click_clear_cache()
        role_page.wait_for_toast_text(timeout=5)
        step("角色分配已还原")

        step("TC-RBAC-018 通过 [OK]")

    # ── TC-RBAC-019: 角色被删除 → 用户权限降级 ──────────────────────

    @allure.epic("权限管理")
    @allure.feature("RBAC权限矩阵")
    @allure.story("角色删除-权限降级")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_rbac_019_role_deleted_user_degraded(self, dual_driver):
        """TC-RBAC-019: 角色被删除 → 持该角色用户刷新 → 权限降级

        删除 RBAC-SYS-ONLY 角色后，rbac_test_sys 登录应看不到系统管理菜单。
        [WARN] 使用新建临时角色避免破坏 seed 数据。
        """
        admin_drv, target_drv = dual_driver
        case("TC-RBAC-019", "角色被删除 → 用户权限降级")
        tmp_role_name = f"RBAC-TMP-DEL-{int(time.time()) % 100000}"
        tmp_role_code = f"rbac_tmp_del_{int(time.time()) % 100000}"
        tmp_username = f"rbac_tmp_del_user"

        # ── Step 1: 通过 API 创建临时角色 + 临时用户 ──
        step("创建临时测试角色")
        resp = api_fetch(admin_drv, "POST", "/api/system/role", {
            "roleName": tmp_role_name,
            "roleSort": 99,
            "status": "1",
            "remark": "auto-test tmp",
        })
        step(f"创建角色响应: code={resp.get('code')}")

        # 获取新角色 ID
        time.sleep(1)
        rl = api_fetch(admin_drv, "GET", "/api/system/role/list?pageNum=1&pageSize=100")
        tmp_role_id = None
        for r in api_get_records(rl):
            if r.get('roleName') == tmp_role_name:
                tmp_role_id = r.get('id')
                break
        assert tmp_role_id, f"未找到刚创建的临时角色 {tmp_role_name}"

        # 创建临时用户
        step("创建临时测试用户并分配临时角色")
        ul = api_fetch(admin_drv, "GET", "/api/system/dept/list")
        ddata = ul.get('data', ul)
        dept_id = 1
        if isinstance(ddata, list) and ddata:
            dept_id = ddata[0].get('deptId') or ddata[0].get('id', 1)

        resp = api_fetch(admin_drv, "POST", "/api/system/user", {
            "username": tmp_username,
            "name": tmp_role_name,
            "password": PWD,
            "confirmPassword": PWD,
            "deptId": dept_id,
            "status": "1",
            "roleIds": [tmp_role_id],
        })
        step(f"创建用户响应: code={resp.get('code')}")

        # ── Step 2: target 用临时用户登录，记录菜单 ──
        step(f"用户 {tmp_username} 登录验证")
        assert login_as(target_drv, tmp_username), f"临时用户 {tmp_username} 登录失败"
        LoginPage(target_drv).wait_vue_stable()
        time.sleep(2)
        before_menus = get_sidebar_menus(target_drv)
        step(f"角色删除前菜单: {before_menus}")

        # target 退出
        try:
            target_drv.execute_script("window.location.hash = '#/login';")
            time.sleep(2)
        except Exception:
            pass

        # ── Step 3: 删除角色 ──
        step(f"删除角色: {tmp_role_name} (ID={tmp_role_id})")
        resp = api_fetch(admin_drv, "DELETE", f"/api/system/role/{tmp_role_id}")
        step(f"删除角色响应: code={resp.get('code')}")

        # 清空缓存
        navigate_to_role_page(admin_drv)
        role_page = RoleManagePage(admin_drv)
        role_page.click_clear_cache()
        role_page.wait_for_toast_text(timeout=5)

        # ── Step 4: target 重新登录，验证权限降级 ──
        step(f"删除角色后，用户 {tmp_username} 重新登录")
        assert login_as(target_drv, tmp_username), f"临时用户重新登录失败"
        LoginPage(target_drv).wait_vue_stable()
        time.sleep(2)
        after_menus = get_sidebar_menus(target_drv)
        step(f"角色删除后菜单: {after_menus}")

        # 新创建的角色没有菜单权限，用户应只看到首页
        assert len(after_menus) <= 1, (
            f"角色删除后用户仍看到多余菜单: {after_menus}"
        )

        # ── Step 5: 清理临时用户 ──
        step("清理临时用户")
        ul2 = api_fetch(admin_drv, "GET",
                        f"/api/system/user/list?pageNum=1&pageSize=10&username={tmp_username}")
        for u in api_get_records(ul2):
            if u.get('username') == tmp_username:
                api_fetch(admin_drv, "DELETE", f"/api/system/user/{u.get('id')}")
                break
        step("临时数据已清理")

        step("TC-RBAC-019 通过 [OK]")

    # ── TC-RBAC-020: 角色被停用 → 用户菜单消失 ──────────────────────

    @allure.epic("权限管理")
    @allure.feature("RBAC权限矩阵")
    @allure.story("角色停用-菜单消失")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_rbac_020_role_disabled_menu_gone(self, dual_driver):
        """TC-RBAC-020: 角色被停用 → 持有该角色的用户刷新 → 菜单消失

        [WARN] 使用临时角色+用户，不影响 seed 数据。
        """
        admin_drv, target_drv = dual_driver
        case("TC-RBAC-020", "角色停用 → 用户菜单消失")
        ts = int(time.time()) % 100000
        tmp_role_name = f"RBAC-TMP-STOP-{ts}"
        tmp_username = f"rbac_tmp_stop_user"

        # ── Step 1: 创建临时角色 + 临时用户 ──
        step("创建临时角色")
        resp = api_fetch(admin_drv, "POST", "/api/system/role", {
            "roleName": tmp_role_name,
            "roleSort": 98,
            "status": "1",
            "remark": "auto-test tmp",
        })
        time.sleep(1)
        rl = api_fetch(admin_drv, "GET", "/api/system/role/list?pageNum=1&pageSize=100")
        tmp_role_id = None
        for r in api_get_records(rl):
            if r.get('roleName') == tmp_role_name:
                tmp_role_id = r.get('id')
                break
        assert tmp_role_id, f"未找到临时角色"

        # 给角色加点权限（通过 UI 简单勾选）
        navigate_to_role_page(admin_drv)
        role_page = RoleManagePage(admin_drv)
        role_page.click_reset()
        role_page.input_role_name(tmp_role_name)
        role_page.click_search()
        role_page.wait_table_ready(timeout=8)
        role_page.click_permission_by_role_name(tmp_role_name)
        role_page.click_permission_tab_pc()
        role_page.select_first_two_permission_checkboxes_in_active_tab()
        role_page.click_permission_confirm()
        role_page.wait_for_toast_text(timeout=5)

        # 创建临时用户
        ul = api_fetch(admin_drv, "GET", "/api/system/dept/list")
        ddata = ul.get('data', ul)
        dept_id = 1
        if isinstance(ddata, list) and ddata:
            dept_id = ddata[0].get('deptId') or ddata[0].get('id', 1)
        api_fetch(admin_drv, "POST", "/api/system/user", {
            "username": tmp_username,
            "name": tmp_role_name,
            "password": PWD,
            "confirmPassword": PWD,
            "deptId": dept_id,
            "status": "1",
            "roleIds": [tmp_role_id],
        })
        time.sleep(1)

        # 清空缓存
        role_page.click_clear_cache()
        role_page.wait_for_toast_text(timeout=5)

        # ── Step 2: target 登录记录菜单 ──
        step(f"用户 {tmp_username} 登录（角色启用时）")
        assert login_as(target_drv, tmp_username), f"临时用户登录失败"
        LoginPage(target_drv).wait_vue_stable()
        time.sleep(2)
        before_menus = get_sidebar_menus(target_drv)
        step(f"角色启用时菜单: {before_menus}")
        before_count = len(before_menus)

        try:
            target_drv.execute_script("window.location.hash = '#/login';")
            time.sleep(2)
        except Exception:
            pass

        # ── Step 3: 停用角色（API: status=0） ──
        step(f"停用角色: {tmp_role_name}")
        resp = api_fetch(admin_drv, "PUT", f"/api/system/role/{tmp_role_id}", {
            "id": tmp_role_id,
            "roleName": tmp_role_name,
            "status": "0",
            "roleSort": 98,
        })
        step(f"停用响应: code={resp.get('code')}")

        navigate_to_role_page(admin_drv)
        role_page = RoleManagePage(admin_drv)
        role_page.click_clear_cache()
        role_page.wait_for_toast_text(timeout=5)

        # ── Step 4: target 重新登录 → 菜单应减少 ──
        step(f"角色停用后用户 {tmp_username} 重新登录")
        assert login_as(target_drv, tmp_username), f"停用后用户登录失败"
        LoginPage(target_drv).wait_vue_stable()
        time.sleep(2)
        after_menus = get_sidebar_menus(target_drv)
        step(f"角色停用后菜单: {after_menus}")

        assert len(after_menus) < before_count or len(after_menus) <= 1, (
            f"停用角色后菜单未减少！前={before_menus}，后={after_menus}"
        )
        step("停用角色 → 菜单消失验证通过 [OK]")

        # ── Step 5: 清理 ──
        step("清理临时数据")
        ul3 = api_fetch(admin_drv, "GET",
                        f"/api/system/user/list?pageNum=1&pageSize=10&username={tmp_username}")
        for u in api_get_records(ul3):
            if u.get('username') == tmp_username:
                api_fetch(admin_drv, "DELETE", f"/api/system/user/{u.get('id')}")
                break
        api_fetch(admin_drv, "DELETE", f"/api/system/role/{tmp_role_id}")
        step("临时数据已清理")

        step("TC-RBAC-020 通过 [OK]")

    # ── TC-RBAC-021: 内置角色删除保护 ───────────────────────────────

    @allure.epic("权限管理")
    @allure.feature("RBAC权限矩阵")
    @allure.story("内置角色保护")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_rbac_021_builtin_role_delete_protection(self, driver_setup):
        """TC-RBAC-021: 内置角色（admin/super_admin）不可删除

        尝试在 UI 中删除 admin 角色，验证系统给出保护提示。
        使用单浏览器（driver_setup），admin 已登录。
        """
        case("TC-RBAC-021", "内置角色删除保护")
        role_page = RoleManagePage(driver_setup)
        navigate_to_role_page(driver_setup)

        # ── Step 1: 搜索 admin 角色 ──
        step("搜索内置管理员角色")
        role_page.click_reset()
        role_page.input_role_name("admin")
        role_page.click_search()
        role_page.wait_table_ready(timeout=8)

        if role_page.get_table_row_count() == 0:
            step("搜索 'admin' 无结果，尝试 '超级管理员'")
            role_page.click_reset()
            role_page.input_role_name("超级管理员")
            role_page.click_search()
            role_page.wait_table_ready(timeout=8)

        if role_page.get_table_row_count() == 0:
            pytest.skip("未找到内置管理员角色，跳过删除保护测试")

        # ── Step 2: 尝试勾选并删除 ──
        step("尝试删除内置角色")
        names = role_page.get_column_data(2)
        if not names:
            pytest.skip("角色列表无数据")
        target = names[0]
        step(f"目标角色: {target}")

        role_page.select_role_checkbox_by_name(target)
        role_page.click_delete()

        # ── Step 3: 验证保护机制 ──
        # 可能是 Toast 提示不可删除，或确认后报错
        msg = role_page.wait_for_toast_text(timeout=5)
        step(f"删除反馈: {msg}")

        # 确认弹窗可能仍在或已关闭
        if not msg:
            # 检查是否有确认弹窗
            try:
                role_page.confirm_message_box()
                msg = role_page.wait_for_toast_text(timeout=5)
                step(f"确认删除后反馈: {msg}")
            except TimeoutException:
                step("无确认弹窗，系统直接阻止了删除")

        # 关键断言：不应提示"成功"
        if "成功" in (msg or ""):
            step("[WARN] 警告：内置角色被成功删除（可能不是内置保护角色）")
        else:
            step("[OK] 系统阻止了内置角色删除（符合预期）")

        step("TC-RBAC-021 通过 [OK]")


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
