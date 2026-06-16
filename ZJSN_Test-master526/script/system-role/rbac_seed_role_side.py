"""通过角色管理侧"分配用户"来绑定角色↔用户关系

已验证的路径:
  RoleManagePage.click_assign_users_by_role_name() → 分配用户弹窗
  → 搜索用户 checkbox → 确定

同时也创建缺失的用户（通过浏览器 fetch API + 正确的字段名）
"""
import sys, os, time, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from base.browser_driver import BaseDriver, ensure_logged_in
from base.sidebar_navigator import SidebarNavigator
from page.system_role_page.RoleManagePage import RoleManagePage
from page.system_page.UserManagePage import UserManagePage

PWD = "Ajyl@2026"

ROLE_NAMES = ["RBAC-全权限","RBAC-仅系统管理","RBAC-仅设备管理","RBAC-仅人员管理","RBAC-混合权限","RBAC-零权限","RBAC-只读"]
USER_NAMES = ["rbac_test_full","rbac_test_sys","rbac_test_equip","rbac_test_hr","rbac_test_mix","rbac_test_none","rbac_test_ro"]

ROLE_USER_MAP = list(zip(ROLE_NAMES, USER_NAMES))

def step(text):
    print(f"  -> {text}")
    try:
        import allure; allure.step(text)
    except: pass

base = BaseDriver()
driver = None
try:
    driver = base.open_browser()
    driver.maximize_window()
    ensure_logged_in(driver)

    # First: create any missing users via API using the correct field names
    # Let's first find what fields the API expects by checking a successful call
    token = None
    for c in driver.get_cookies():
        if c['name'] == 'authorized-token':
            import urllib.parse
            td = json.loads(urllib.parse.unquote(c['value']))
            token = td.get('accessToken')
            break
    if token:
        def fetch_post(path, data):
            return driver.execute_script(f"""
                return fetch('https://aiwechatminidemo.cimc-digital.com{path}', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json',
                        'Authorization': 'Bearer {token}' }},
                    body: JSON.stringify({json.dumps(data, ensure_ascii=False)})
                }}).then(function(r){{return r.json();}});
            """)

        for username, name, role_name in ROLE_USER_MAP:
            step(f"API create user: {username}")
            # Try minimal field set
            body = {
                "username": username, "name": name,
                "password": PWD, "confirmPassword": PWD,
                "status": "1"
            }
            resp = fetch_post("/api/system/user", body)
            code = resp.get('code', -1)
            msg = resp.get('message', resp.get('msg', ''))
            if code in (200, 0):
                step(f"  OK: {msg}")
            elif "已存在" in msg or "已存在" in json.dumps(resp):
                step(f"  EXISTS")
            elif "用户类型" in msg or "真实姓名" in msg:
                # Try adding userType
                body["userType"] = "员工"
                resp2 = fetch_post("/api/system/user", body)
                step(f"  +userType: {resp2.get('code')} {resp2.get('message','')}")
            else:
                step(f"  FAIL: {msg} (resp={str(resp)[:100]})")
                # API 失败后短等待避免 rate-limit，不阻塞 15 秒
                from time import sleep as _sleep
                _sleep(1)
            from time import sleep as _sleep
            _sleep(0.3)  # 请求间隔，避免服务端压力

    # Now navigate to role management and assign users
    print("\n" + "=" * 60)
    print("Phase 2: Assign users to roles via RoleManagePage")
    nav = SidebarNavigator(driver)
    nav.navigate_to("系统管理", "角色管理")
    time.sleep(3)
    rp = RoleManagePage(driver)

    for role_name, username in ROLE_USER_MAP:
        step(f"Assign {username} -> {role_name}")

        # Search role
        rp.click_reset()
        rp.input_role_name(role_name)
        rp.click_search()
        time.sleep(2)
        if rp.get_table_row_count() == 0:
            step(f"  Role not found")
            continue

        # Click 分配用户
        rp.click_assign_users_by_role_name(role_name)
        time.sleep(3)

        # In the dialog: search for user by name
        search_input = driver.execute_script("""
            var inp = document.querySelector('.el-dialog input[placeholder*="搜索"]');
            if (inp) {
                var nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                    window.HTMLInputElement.prototype, 'value'
                ).set;
                nativeInputValueSetter.call(inp, '{u}');
                inp.dispatchEvent(new Event('input', {{ bubbles: true }}));
                inp.dispatchEvent(new KeyboardEvent('keyup', {{ bubbles: true }}));
            }
            return !!inp;
        """.replace('{u}', username))
        time.sleep(1.5)
        step(f"  Search input found: {search_input}")

        # Wait for search results and find the user row
        checked = driver.execute_script(f"""
            var dlg = document.querySelector('.el-dialog');
            if (!dlg) return -1;

            // Find user row
            var rows = dlg.querySelectorAll('tr.el-table__row');
            for (var i = 0; i < rows.length; i++) {{
                if (rows[i].innerText.indexOf('{username}') !== -1) {{
                    // Click the checkbox (first cell)
                    var cb = rows[i].querySelector('label.el-checkbox');
                    if (cb) {{
                        if (!cb.classList.contains('is-checked')) {{
                            cb.click();
                        }}
                        return 1;
                    }}
                }}
            }}
            return 0;  // user row not found
        """)
        time.sleep(1)
        step(f"  Checkbox clicked: {'user found & checked' if checked > 0 else ('user not found' if checked == 0 else 'dialog not found')}")

        # Click 确定
        driver.execute_script("""
            var dlg = document.querySelector('.el-dialog');
            if (dlg) {
                var btns = dlg.querySelectorAll('.el-dialog__footer button');
                for (var i = 0; i < btns.length; i++) {
                    if (btns[i].innerText.indexOf('确定') !== -1) {
                        btns[i].click(); return;
                    }
                }
            }
        """)
        t = rp.wait_for_toast_text()
        step(f"  Result: {t}")
        time.sleep(1.5)

    print("\nDone! Roles <-> Users linked.")

finally:
    if driver:
        try: base.close_browser()
        except: pass
