"""最终修复 + 运行测试"""
import sys, json, time
sys.path.insert(0, 'd:/Desktop/WorkStudy/ZJSN_Test-master526')

from base.browser_driver import BaseDriver, ensure_logged_in
from base.sidebar_navigator import SidebarNavigator

PWD = "Ajyl@2026"
USERS = ["rbac_test_full","rbac_test_sys","rbac_test_equip","rbac_test_hr","rbac_test_mix","rbac_test_none","rbac_test_ro"]
ROLES = ["RBAC-全权限","RBAC-仅系统管理","RBAC-仅设备管理","RBAC-仅人员管理","RBAC-混合权限",None,"RBAC-只读"]
PAIRS = list(zip(USERS, ROLES))

base = BaseDriver()
driver = base.open_browser()
driver.maximize_window()
ensure_logged_in(driver)
nav = SidebarNavigator(driver)

# ── 1. 通过 API 查询当前角色状态 ──
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
        return fetch('https://aiwechatminidemo.cimc-digital.com{path}', {{
            method: '{method}',
            headers: {{'Content-Type': 'application/json', 'Authorization': 'Bearer {token}'}},
            body: {b if data else 'undefined'}
        }}).then(r=>r.json());
    """)

ul = fetch("GET", "/api/system/user/list?pageNum=1&pageSize=20")
user_ids = {}
for u in ul.get('data',{}).get('records',[]):
    if u.get('username','').startswith('rbac_test_'):
        uid = u.get('id') or u.get('userId')
        user_ids[u['username']] = {'id': uid, 'roles': u.get('roleIds',[])}
        print(f"{u['username']:20s} id={uid:3d} roles={u.get('roleIds',[])}")

# ── 2. 通过 UI 分配角色 ──
nav.navigate_to("系统管理", "用户管理")
time.sleep(3)

for username, role_name in PAIRS:
    if not role_name:
        print(f"\n{username}: SKIP (no role)")
        continue

    print(f"\n{username} -> {role_name}", end=" ")

    # Search
    driver.execute_script(f"""
        var inp = document.querySelector('input[placeholder*="搜索"]');
        if(inp){{ inp.value='{username}'; inp.dispatchEvent(new Event('input', {{bubbles:true}})); }}
    """)
    time.sleep(0.5)
    driver.execute_script("""
        document.querySelectorAll('button').forEach(function(b){
            if(b.innerText&&b.innerText.trim()==='查询')b.click();
        });
    """)
    time.sleep(2)

    # Click '分配角色' by exact text match
    result = driver.execute_script(f"""
        var rows = document.querySelectorAll('tr.el-table__row');
        for(var i=0;i<rows.length;i++){{
            if(rows[i].innerText.indexOf('{username}')===-1)continue;
            var btns = rows[i].querySelectorAll('button');
            for(var k=0;k<btns.length;k++){{
                var t = (btns[k].innerText||'').trim();
                if(t === '分配角色'){{ btns[k].click(); return 'ok'; }}
            }}
        }}
        return 'btn_not_found';
    """)
    time.sleep(3)

    title = driver.execute_script("return document.querySelector('.el-dialog .el-dialog__title')?.innerText||'';")
    if '分配角色' not in title:
        print(f"DIALOG FAIL: {title}")
        driver.execute_script("""
            var dlg=document.querySelector('.el-dialog');
            if(dlg){var btn=dlg.querySelector('.el-dialog__footer button:not(.el-button--primary)');if(btn)btn.click();}
        """)
        time.sleep(1)
        continue

    # Check target role - click the actual INPUT element not the label
    result = driver.execute_script(f"""
        var dlg = document.querySelector('.el-dialog');
        if(!dlg) return 'NO DIALOG';
        var count = 0;
        dlg.querySelectorAll('label.el-checkbox').forEach(function(cb){{
            var t = (cb.innerText||'').trim();
            if(t === '{role_name}') {{
                // Click the actual checkbox input to trigger Vue's change detection
                var input = cb.querySelector('.el-checkbox__original, .el-checkbox__inner');
                if(input) {{
                    if(!cb.classList.contains('is-checked')) {{
                        // Use Event dispatch instead of direct click
                        input.dispatchEvent(new Event('click', {{bubbles:true}}));
                        input.dispatchEvent(new Event('change', {{bubbles:true}}));
                        count++;
                    }} else {{
                        count = -1;  // already checked
                    }}
                }}
            }}
        }});
        return count;
    """)
    time.sleep(1)
    print(f"  checkbox clicks: {result}", end="")
    time.sleep(1)

    # Confirm
    driver.execute_script("""
        var dlg = document.querySelector('.el-dialog');
        if(dlg){var btn=dlg.querySelector('.el-dialog__footer button.el-button--primary');if(btn)btn.click();}
    """)
    time.sleep(2)
    toast = driver.execute_script("return document.querySelector('.el-message__content')?.innerText||'';")
    print(toast)

# ── 3. 验证 ──
print("\n" + "="*60)
print("验证结果:")
ul2 = fetch("GET", "/api/system/user/list?pageNum=1&pageSize=20")
for u in ul2.get('data',{}).get('records',[]):
    if u.get('username','').startswith('rbac_test_'):
        print(f"  {u['username']:20s} roleIds={u.get('roleIds',[])}")

driver.quit()
print("\nDone!")
