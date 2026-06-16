"""RBAC测试数据种子脚本 — 通过 Selenium 浏览器内的 JS XHR 创建测试数据"""
import sys, os, time, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from base.browser_driver import BaseDriver, ensure_logged_in
from base.sidebar_navigator import SidebarNavigator
from page.system_role_page.RoleManagePage import RoleManagePage

DEFAULT_PWD = "Ajyl@2026"

TEST_ROLES = [
    {"name": "RBAC-全权限",     "code": "rbac_full",    "order": 90, "desc": "RBAC测试-全权限",     "perm": "__ALL__"},
    {"name": "RBAC-仅系统管理",  "code": "rbac_sys",     "order": 91, "desc": "RBAC测试-仅系统管理",  "perm": ["系统管理"]},
    {"name": "RBAC-仅设备管理",  "code": "rbac_equip",   "order": 92, "desc": "RBAC测试-仅设备管理",  "perm": ["设备管理"]},
    {"name": "RBAC-仅人员管理",  "code": "rbac_hr",      "order": 93, "desc": "RBAC测试-仅人员管理",  "perm": ["人员管理"]},
    {"name": "RBAC-混合权限",    "code": "rbac_mix",     "order": 94, "desc": "RBAC测试-混合权限",
     "perm": ["用户管理","角色管理","设备台账","客户管理"]},
    {"name": "RBAC-零权限",     "code": "rbac_none",    "order": 95, "desc": "RBAC测试-零权限",     "perm": []},
    {"name": "RBAC-只读",       "code": "rbac_readonly","order": 96, "desc": "RBAC测试-只读",       "perm": "__ALL__"},
]

TEST_USERS = [
    ("rbac_test_full",   "RBAC全权限测试",   "rbac_full"),
    ("rbac_test_sys",    "RBAC系统管理测试", "rbac_sys"),
    ("rbac_test_equip",  "RBAC设备管理测试", "rbac_equip"),
    ("rbac_test_hr",     "RBAC人员管理测试", "rbac_hr"),
    ("rbac_test_mix",    "RBAC混合权限测试", "rbac_mix"),
    ("rbac_test_none",   "RBAC零权限测试",   "rbac_none"),
    ("rbac_test_ro",     "RBAC只读权限测试", "rbac_readonly"),
]

def step(text):
    print(f"  -> {text}")

def jxhr(driver, method, path, body=None):
    """在浏览器内通过同步 XHR 执行 API 调用（不走 Python requests）"""
    body_json = json.dumps(body) if body else 'null'
    result = driver.execute_script(f"""
        var xhr = new XMLHttpRequest();
        xhr.open('{method}', 'https://aiwechatminidemo.cimc-digital.com{path}', false);  // synchronous
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.setRequestHeader('Authorization', 'Bearer ' + JSON.parse(decodeURIComponent(document.cookie.split('authorized-token=')[1].split(';')[0])).accessToken);
        try {{
            xhr.send({body_json});
            return JSON.parse(xhr.responseText);
        }} catch(e) {{
            return {{code: -1, msg: xhr.status + ': ' + xhr.statusText, data: null}};
        }}
    """)
    return result

def main():
    base = BaseDriver()
    driver = None
    try:
        driver = base.open_browser()
        driver.maximize_window()
        ensure_logged_in(driver)

        # Verify XHR works
        step("Testing API connectivity...")
        test = jxhr(driver, "GET", "/api/system/role/list")
        step(f"role list: {len(json.dumps(test.get('data',[])))} bytes")

        # ── Phase 1: API 创建角色 ──
        print("\n" + "=" * 60)
        print("Phase 1: API create roles")

        rl = jxhr(driver, "GET", "/api/system/role/list")
        step(f"Response: code={rl.get('code')} data_type={type(rl.get('data')).__name__}")
        data = rl.get('data', [])
        if isinstance(data, dict):
            step(f"data keys={list(data.keys())}")
            records = data.get('records', [])
        elif isinstance(data, list):
            records = data
        else:
            records = []
        existing = {}
        for r in records:
            if isinstance(r, dict):
                existing[r.get('roleCode', '')] = r
            else:
                step(f"  unexpected item type: {type(r).__name__} = {str(r)[:80]}")
        step(f"Existing roles ({len(existing)}): {list(existing.keys())}")

        created_role_ids = {}
        for rd in TEST_ROLES:
            if rd['code'] in existing:
                rid = existing[rd['code']].get('roleId') or existing[rd['code']].get('id')
                created_role_ids[rd['code']] = rid
                step(f"  SKIP {rd['code']} (id={rid})")
                continue

            resp = jxhr(driver, "POST", "/api/system/role", {
                "roleName": rd['name'], "roleCode": rd['code'],
                "roleSort": rd['order'], "remark": rd.get('desc',''), "status": "1"
            })
            if resp.get('code') in (200, 0):
                step(f"  OK {rd['code']}")
                time.sleep(1)
                # re-fetch to get ID
                rl2 = jxhr(driver, "GET", "/api/system/role/list")
                for r in rl2.get('data', []):
                    if r.get('roleCode') == rd['code']:
                        created_role_ids[rd['code']] = r.get('roleId') or r.get('id')
            else:
                step(f"  FAIL {rd['code']}: {resp.get('msg','')}")

        step(f"Role IDs: {created_role_ids}")

        # ── Phase 2: UI 分配权限 ──
        print("\n" + "=" * 60)
        print("Phase 2: UI assign permissions")
        nav = SidebarNavigator(driver)
        nav.navigate_to("系统管理", "角色管理")
        time.sleep(3)
        rp = RoleManagePage(driver)

        for rd in TEST_ROLES:
            step(f"Permissions: {rd['name']}")
            rp.click_reset()
            rp.input_role_name(rd['name'])
            rp.click_search()
            time.sleep(2)
            if rp.get_table_row_count() == 0:
                step(f"  WARN role not found")
                continue

            rp.click_permission_by_role_name(rd['name'])
            time.sleep(2)
            rp.click_permission_tab_pc()
            time.sleep(1.5)

            # expand all groups
            driver.execute_script("""
                document.querySelectorAll('.perm-group__arrow').forEach(function(a){
                    try{a.click();}catch(e){}
                });
            """)
            time.sleep(2)

            if rd['perm'] == "__ALL__":
                cnt = driver.execute_script("""
                    var c=0,p=document.querySelector('.el-tab-pane.is-active');
                    if(p) p.querySelectorAll('label.el-checkbox:not(.is-checked)').forEach(function(cb){cb.click();c++;});
                    return c;
                """)
                step(f"  all: {cnt} checked")
            elif rd['perm']:
                for gn in rd['perm']:
                    cnt = driver.execute_script(f"""
                        var c=0,p=document.querySelector('.el-tab-pane.is-active');
                        if(!p) return 0;
                        p.querySelectorAll('div.perm-group').forEach(function(g){{
                            var n=g.querySelector('.perm-group__name');
                            if(!n) return;
                            if(((n.innerText||'').trim()).indexOf('{gn}')===-1) return;
                            g.querySelectorAll('label.el-checkbox:not(.is-checked)').forEach(function(cb){{cb.click();c++;}});
                        }});
                        return c;
                    """)
                    step(f"  {gn}: {cnt} checked")
                    time.sleep(0.5)

            rp.click_permission_confirm()
            t = rp.wait_for_toast_text(8)
            step(f"  saved: {t}")
            time.sleep(1.5)

        # ── Phase 3: API 创建用户 ──
        print("\n" + "=" * 60)
        print("Phase 3: API create users")

        # Get first department
        dept_list = jxhr(driver, "GET", "/api/system/dept/list")
        dl_data = dept_list.get('data', dept_list)
        dept_ids = []
        if isinstance(dl_data, list):
            for d in dl_data:
                did = d.get('deptId')
                if did: dept_ids.append(did)
        first_dept_id = dept_ids[0] if dept_ids else 1
        step(f"Dept IDs: {dept_ids[:5]} (using {first_dept_id})")

        for username, name, role_code in TEST_USERS:
            step(f"User: {username}")

            # Check if exists
            exist = jxhr(driver, "GET", f"/api/system/user/list?username={username}&pageNum=1&pageSize=1")
            records = exist.get('data', {}).get('records', []) if isinstance(exist.get('data'), dict) else []
            if any(u.get('username') == username for u in records):
                step(f"  SKIP (exists)")
                continue

            body = {
                "username": username, "name": name,
                "password": DEFAULT_PWD, "confirmPassword": DEFAULT_PWD,
                "phone": "138" + str(int(time.time()))[-8:],
                "deptId": first_dept_id, "status": "1"
            }
            rid = created_role_ids.get(role_code)
            if rid:
                body["roleIds"] = [rid]

            resp = jxhr(driver, "POST", "/api/system/user", body)
            if resp.get('code') in (200, 0):
                step(f"  OK created")
            else:
                step(f"  FAIL: {resp.get('msg','')}")
                step(f"  body: {json.dumps(body, ensure_ascii=False)[:200]}")
            time.sleep(0.5)

        print(f"\nDone! Roles={list(created_role_ids.keys())} Users={[u[0] for u in TEST_USERS]}")

    finally:
        if driver:
            try: base.close_browser()
            except: pass

if __name__ == '__main__':
    main()
