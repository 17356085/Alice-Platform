#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""RBAC seed data V3 — 纯 API 方式，无 UI 依赖

Architecture:
  1. API: 删除旧 RBAC 测试数据
  2. API: 创建 7 个测试角色
  3. API: 获取菜单树 → 按模块分配权限
  4. API: 创建 7 个测试用户
  5. 验证

优势：不依赖 UI 权限弹窗（Phase 3 稳定性问题），执行快 (~15s vs ~2min)
"""
import sys, os, time, json

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from base.browser_driver import BaseDriver, ensure_logged_in

PWD = "Ajyl@2026"
TOKEN_CACHE = {"value": None}

# ══════════════════════════════════════════════════════════════════════
#  数据定义
# ══════════════════════════════════════════════════════════════════════

ROLES = [
    ("RBAC-ALL",        "rbac_full",    90, "all"),
    ("RBAC-SYS-ONLY",   "rbac_sys",     91, ["系统管理"]),
    ("RBAC-EQUIP-ONLY", "rbac_equip",   92, ["设备管理"]),
    ("RBAC-HR-ONLY",    "rbac_hr",      93, ["人员管理"]),
    ("RBAC-MIXED",      "rbac_mix",     94, ["系统管理", "设备管理", "销售管理"]),
    ("RBAC-NONE",       "rbac_none",    95, []),
    ("RBAC-READONLY",   "rbac_readonly",96, "all"),
]

USERS = [
    ("rbac_test_full",   "RBAC-ALL-Test",       "RBAC-ALL"),
    ("rbac_test_sys",    "RBAC-SYS-Test",       "RBAC-SYS-ONLY"),
    ("rbac_test_equip",  "RBAC-EQUIP-Test",     "RBAC-EQUIP-ONLY"),
    ("rbac_test_hr",     "RBAC-HR-Test",        "RBAC-HR-ONLY"),
    ("rbac_test_mix",    "RBAC-MIXED-Test",     "RBAC-MIXED"),
    ("rbac_test_none",   "RBAC-NONE-Test",      "RBAC-NONE"),
    ("rbac_test_ro",     "RBAC-READONLY-Test",  "RBAC-READONLY"),
]

# ══════════════════════════════════════════════════════════════════════
#  API helpers
# ══════════════════════════════════════════════════════════════════════

def api(driver, method, path, body=None):
    """浏览器内 fetch API 调用"""
    driver.set_script_timeout(60)
    js_body = ("body: JSON.stringify(%s)," % json.dumps(body, ensure_ascii=False)) if body else ""
    return driver.execute_script("""
        var token = JSON.parse(
            decodeURIComponent(document.cookie.split('authorized-token=')[1].split(';')[0])
        ).accessToken;
        return fetch('https://aiwechatminidemo.cimc-digital.com%s', {
            method: '%s',
            headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token },
            %s
        }).then(function(r) { return r.json(); });
    """ % (path, method, js_body))


def get_records(resp):
    data = resp.get('data', resp)
    if isinstance(data, dict):
        return data.get('records', data.get('rows', []))
    if isinstance(data, list):
        return data
    return []


def get_all_menus(driver):
    """获取所有菜单（含 ID）"""
    resp = api(driver, "GET", "/api/system/menu/list?pageNum=1&pageSize=500")
    return get_records(resp)


def build_menu_tree(menus):
    """构建 parent_id → children 映射"""
    tree = {}
    id_to_item = {}
    for m in menus:
        mid = m["id"]
        id_to_item[mid] = m
        pid = m.get("parentId", 0)
        tree.setdefault(pid, []).append(mid)
    return tree, id_to_item


def get_module_menu_ids(menus, module_names):
    """获取指定模块的所有子孙菜单 ID（含 type=1/2/3 全部）

    Args:
        menus: 所有菜单列表
        module_names: 模块名称列表（顶层目录 menuName），如 ["系统管理", "设备管理"]

    Returns:
        list: 所有相关菜单 ID（包含 type=1 目录 + type=2 页面 + type=3 按钮权限）
    """
    tree, id_to_item = build_menu_tree(menus)

    # 找到顶层模块 ID
    module_ids = []
    for m in menus:
        if m.get("menuType") == 1 and m.get("parentId") == 0:
            if m["menuName"] in module_names:
                module_ids.append(m["id"])

    # 递归收集所有子孙（不过滤 type）
    result = set()
    def collect(pid):
        for cid in tree.get(pid, []):
            result.add(cid)
            collect(cid)

    for mid in module_ids:
        result.add(mid)
        collect(mid)

    return list(result)


def get_all_menu_ids(menus):
    """获取所有菜单 ID"""
    return [m["id"] for m in menus]


# ══════════════════════════════════════════════════════════════════════
#  Main
# ══════════════════════════════════════════════════════════════════════

def main():
    base = BaseDriver()
    driver = base.open_browser()
    try:
        ensure_logged_in(driver)
        time.sleep(2)

        # ── Phase 1: Cleanup ────────────────────────────────────────
        print("=" * 50)
        print("[Phase 1] Cleaning old RBAC test data")
        print("=" * 50)

        rl = api(driver, "GET", "/api/system/role/list?pageNum=1&pageSize=200")
        for r in get_records(rl):
            rid = r.get('id')
            rname = r.get('roleName', '')
            if rname.startswith('RBAC-'):
                resp = api(driver, "DELETE", "/api/system/role/%s" % rid)
                print("  DEL role [%s] %s -> code=%s" % (rid, rname, resp.get('code')))
                time.sleep(0.3)

        ul = api(driver, "GET", "/api/system/user/list?pageNum=1&pageSize=50&username=rbac_test")
        for u in get_records(ul):
            uid = u.get('id')
            uname = u.get('username', '')
            resp = api(driver, "DELETE", "/api/system/user/%s" % uid)
            print("  DEL user  [%s] %s -> code=%s" % (uid, uname, resp.get('code')))
            time.sleep(0.3)

        # ── Phase 2: Create roles ───────────────────────────────────
        print()
        print("=" * 50)
        print("[Phase 2] Creating roles")
        print("=" * 50)

        role_ids = {}
        for rname, rcode, rorder, _ in ROLES:
            body = {"roleName": rname, "roleSort": rorder, "status": "1",
                    "remark": "RBAC test for %s" % rcode}
            resp = api(driver, "POST", "/api/system/role", body)
            if resp.get('code') in (200, 0):
                print("  [OK] Role created: %s (code=%s)" % (rname, rcode))
            else:
                print("  [FAIL] Role create %s: %s" % (rname, resp.get('message', '')))
            time.sleep(0.3)

        time.sleep(1)
        rl2 = api(driver, "GET", "/api/system/role/list?pageNum=1&pageSize=200")
        # Accumulate roles by name, taking the LAST (newest) ID to avoid stale duplicates
        for r in get_records(rl2):
            rname = r.get('roleName', '')
            if rname in [rn for rn, _, _, _ in ROLES]:
                role_ids[rname] = r.get('id')  # last write wins
        for rname, rid in role_ids.items():
            print("  Role [%s] = %s" % (rid, rname))

        if not role_ids:
            print("[FATAL] No role IDs found. Aborting.")
            raise SystemExit(1)

        # ── Phase 3: Assign permissions via API ──────────────────────
        print()
        print("=" * 50)
        print("[Phase 3] Assigning permissions via API")
        print("=" * 50)

        all_menus = get_all_menus(driver)
        all_ids = get_all_menu_ids(all_menus)
        print("  Total menus: %d" % len(all_menus))

        for rname, _rcode, _rorder, modules in ROLES:
            rid = role_ids.get(rname)
            if not rid:
                print("  [SKIP] %s: role not found" % rname)
                continue

            # Determine menu IDs
            if modules == "all":
                menu_ids = all_ids
            elif isinstance(modules, list) and len(modules) > 0:
                menu_ids = get_module_menu_ids(all_menus, modules)
            else:
                menu_ids = []  # RBAC-NONE

            print("  %s → %d menu IDs (modules=%s)" % (rname, len(menu_ids), modules))

            # Save menus
            resp = api(driver, "PUT", "/api/system/role/%s/menus" % rid, menu_ids)
            code = resp.get('code', -1)
            if code in (200, 0):
                print("    [OK] Menus saved")
            else:
                print("    [FAIL] Menus save: code=%s msg=%s" % (code, resp.get('message', '')))
            time.sleep(0.3)

            # Save data scope
            resp2 = api(driver, "PUT", "/api/system/role/%s/data-scope" % rid,
                        {"dataScope": 1})
            code2 = resp2.get('code', -1)
            if code2 not in (200, 0):
                print("    [WARN] Data scope save: code=%s" % code2)
            time.sleep(0.2)

        # ── Phase 4: Create users ───────────────────────────────────
        print()
        print("=" * 50)
        print("[Phase 4] Creating users")
        print("=" * 50)

        dl = api(driver, "GET", "/api/system/dept/list")
        ddata = dl.get('data', dl)
        dept_id = 1
        if isinstance(ddata, list) and ddata:
            dept_id = ddata[0].get('deptId') or ddata[0].get('id', 1)

        for username, name, role_name in USERS:
            rid = role_ids.get(role_name)
            if not rid:
                print("  [SKIP] %s: role %s not found" % (username, role_name))
                continue

            now = int(time.time())
            body = {
                "username": username,
                "name": name,
                "realName": name,
                "password": PWD,
                "confirmPassword": PWD,
                "phone": "138%s" % str(now)[-8:],
                "phonenumber": "138%s" % str(now)[-8:],
                "deptId": dept_id,
                "status": "1",
                "userType": "1",
                "roleIds": [rid],
            }
            resp = api(driver, "POST", "/api/system/user", body)
            code = resp.get('code', -1)
            print("  %s %s -> %s (code=%s)" % (
                "[OK]" if code in (200, 0) else "[FAIL]", username, role_name, code))
            time.sleep(0.3)

        # ── Phase 5: Clear cache via UI ──────────────────────────────
        print()
        print("=" * 50)
        print("[Phase 5] Clear cache via UI (required for API permissions)")
        print("=" * 50)

        from base.sidebar_navigator import SidebarNavigator
        from page.system_role_page.RoleManagePage import RoleManagePage

        nav = SidebarNavigator(driver)
        nav._navigate_by_js_hash('#/system/role', 'cache-clear')
        time.sleep(2)
        RoleManagePage(driver).wait_vue_stable()
        rp = RoleManagePage(driver)
        if rp.click_clear_cache():
            msg = rp.wait_for_toast_text(timeout=5)
            print("  Cache cleared: %s" % (msg or 'no toast'))
        else:
            print("  [WARN] Clear cache button not found")

        # ── Phase 6: Verify ─────────────────────────────────────────
        print()
        print("=" * 50)
        print("[Phase 6] Verification")
        print("=" * 50)

        rl3 = api(driver, "GET", "/api/system/role/list?pageNum=1&pageSize=50")
        rbac_roles = [r.get('roleName', '') for r in get_records(rl3)
                      if r.get('roleName', '').startswith('RBAC-')]
        print("  RBAC roles: %d → %s" % (len(rbac_roles), rbac_roles))

        ul3 = api(driver, "GET",
                  "/api/system/user/list?pageNum=1&pageSize=20&username=rbac_test")
        rbac_users = [u.get('username', '') for u in get_records(ul3)]
        print("  RBAC users: %d → %s" % (len(rbac_users), rbac_users))

        print()
        print("=" * 50)
        print("[DONE] RBAC seed data created (V3 API)")
        print("  Roles: %d" % len(rbac_roles))
        print("  Users: %d" % len(rbac_users))
        print("=" * 50)

    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass


if __name__ == "__main__":
    main()
