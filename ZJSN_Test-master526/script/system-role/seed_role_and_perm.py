"""一步到位：清理重复角色 + 分配用户角色 + 配置页面权限"""
import sys, json, time
sys.path.insert(0, 'd:/Desktop/WorkStudy/ZJSN_Test-master526')

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from base.browser_driver import BaseDriver, ensure_logged_in
from base.sidebar_navigator import SidebarNavigator

BASE = 'https://aiwechatminidemo.cimc-digital.com'
PWD = 'Ajyl@2026'

# Mapping: role_name -> [user_ids, role_ids_to_assign, expected_sidebar_menu]
ROLE_CONFIG = [
    ("RBAC-全权限",    "rbac_test_full",    ["系统管理","设备管理","储罐管理","DCS数据","化验室取样","人员管理","生产管理","销售管理"]),
    ("RBAC-仅系统管理", "rbac_test_sys",     ["系统管理"]),
    ("RBAC-仅设备管理", "rbac_test_equip",   ["设备管理"]),
    ("RBAC-仅人员管理", "rbac_test_hr",      ["人员管理"]),
    ("RBAC-混合权限",   "rbac_test_mix",     ["系统管理","设备管理","销售管理"]),
]

def step(text):
    print(f"  -> {text}")

base = BaseDriver()
driver = base.open_browser()
driver.maximize_window()
ensure_logged_in(driver)
time.sleep(2)

# Get token for API calls
token = None
for c in driver.get_cookies():
    if c['name'] == 'authorized-token':
        import urllib.parse
        td = json.loads(urllib.parse.unquote(c['value']))
        token = td.get('accessToken')
        break

def fetch(method, path, data=None):
    b = json.dumps(data, ensure_ascii=False) if data else 'null'
    return driver.execute_script(f"""
        return fetch('{BASE}{path}', {{
            method: '{method}',
            headers: {{'Content-Type': 'application/json', 'Authorization': 'Bearer {token}'}},
            body: {b if data else 'undefined'}
        }}).then(r=>r.json());
    """)

# ── Step 1: 删除重复角色 ──
print("=" * 60)
print("Step 1: Delete duplicate roles")
dup_ids = [37, 38, 39]  # old duplicates to remove
for rid in dup_ids:
    r = fetch("DELETE", f"/api/system/role/{rid}")
    msg = r.get('message', '')
    print(f"  Delete role id={rid}: {msg}")
    time.sleep(0.5)

# ── Step 2: 获取最新角色和用户 ID ──
print("\n" + "=" * 60)
print("Step 2: Get fresh role & user IDs")

rl = fetch("GET", "/api/system/role/list")
role_name_to_id = {}
for rec in rl.get('data',{}).get('records',[]):
    name = rec.get('roleName','')
    if 'RBAC-' in name:
        rid = rec.get('roleId') or rec.get('id')
        role_name_to_id[name] = rid
        print(f"  Role: {name:20s} id={rid}")

ul = fetch("GET", "/api/system/user/list?pageNum=1&pageSize=50")
user_name_to_id = {}
for u in ul.get('data',{}).get('records',[]):
    un = u.get('username','')
    if 'rbac_test_' in un:
        uid = u.get('id') or u.get('userId')
        user_name_to_id[un] = uid
        print(f"  User: {un:20s} id={uid}")

# ── Step 3: 通过浏览器 API 直接分配角色（非UI点击） ──
print("\n" + "=" * 60)
print("Step 3: Assign roles to users via API")

for role_name, username, _ in ROLE_CONFIG:
    rid = role_name_to_id.get(role_name)
    uid = user_name_to_id.get(username)
    if not rid or not uid:
        print(f"  SKIP {username} -> {role_name}: rid={rid} uid={uid}")
        continue

    r = fetch("PUT", "/api/system/user/role", {"userId": uid, "roleIds": [rid]})
    msg = r.get('message', '')
    print(f"  {username:20s} -> {role_name:15s}: {msg}")
    time.sleep(1)

# ── Step 4: 在角色管理页面配置页面权限 ──
print("\n" + "=" * 60)
print("Step 4: Configure page permissions for each role")

nav = SidebarNavigator(driver)
nav.navigate_to("系统管理", "角色管理")
time.sleep(3)

perm_groups_config = {
    "RBAC-全权限":    "__ALL__",
    "RBAC-仅系统管理": ["系统管理"],
    "RBAC-仅设备管理": ["设备管理"],
    "RBAC-仅人员管理": ["人员管理"],
    "RBAC-混合权限":   ["用户管理","角色管理","设备台账","客户管理"],
}

from page.system_role_page.RoleManagePage import RoleManagePage
rp = RoleManagePage(driver)

for role_name, pem_groups in perm_groups_config.items():
    step(f"Role: {role_name}")

    # Search role
    rp.click_reset()
    rp.input_role_name(role_name)
    rp.click_search()
    time.sleep(2)

    if rp.get_table_row_count() == 0:
        step(f"  NOT FOUND")
        continue

    # Click 权限 button
    rp.click_permission_by_role_name(role_name)
    time.sleep(2.5)

    # Switch to PC操作权限 Tab
    rp.click_permission_tab_pc()
    time.sleep(2)

    # Expand all perm-groups by clicking each arrow
    driver.execute_script("""
        document.querySelectorAll('.perm-group__arrow, .perm-group__header i[class*="icon"]').forEach(function(a){
            try{a.click();}catch(e){}
        });
    """)
    time.sleep(2)

    if pem_groups == "__ALL__":
        # Check ALL checkboxes in the active pane
        cnt = driver.execute_script("""
            var c=0;
            var p=document.querySelector('.el-tab-pane.is-active');
            if(!p) return 0;
            p.querySelectorAll('label.el-checkbox:not(.is-checked)').forEach(function(cb){
                // Click the INPUT element, not the label
                var inp = cb.querySelector('.el-checkbox__original');
                if(inp) { inp.click(); c++; }
            });
            return c;
        """)
        step(f"  Checked {cnt} permissions (INPUT click)")
    else:
        for gn in pem_groups:
            # Expand all first to ensure all checkboxes are visible
            cnt = driver.execute_script(f"""
                var c=0;
                var p=document.querySelector('.el-tab-pane.is-active');
                if(!p) return 0;
                p.querySelectorAll('div.perm-group').forEach(function(g){{
                    var n=g.querySelector('.perm-group__name');
                    if(!n) return;
                    var nm=(n.innerText||'').trim();
                    if(nm.indexOf('{gn}')===-1) return;
                    // Click the input inside each unchecked checkbox in this group
                    g.querySelectorAll('label.el-checkbox:not(.is-checked)').forEach(function(cb){{
                        var inp=cb.querySelector('.el-checkbox__original');
                        if(inp){{inp.click();c++;}}
                    }});
                }});
                return c;
            """)
            step(f"  {gn}: {cnt} checked")
            time.sleep(0.5)

    # Save
    rp.click_permission_confirm()
    t = rp.wait_for_toast_text(8)
    step(f"  Saved: {t}")
    time.sleep(1.5)

# ── Final verification ──
print("\n" + "=" * 60)
print("Final verification:")
ul2 = fetch("GET", "/api/system/user/list?pageNum=1&pageSize=50")
for u in ul2.get('data',{}).get('records',[]):
    un = u.get('username','')
    if 'rbac_test_' in un:
        print(f"  {un:20s} roleIds={u.get('roleIds',[])}")

print("\nDone!")
driver.quit()
