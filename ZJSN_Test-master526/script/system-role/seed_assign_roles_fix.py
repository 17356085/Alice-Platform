"""修复：通过文本匹配正确点击"分配角色"按钮"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from base.browser_driver import BaseDriver, ensure_logged_in
from base.sidebar_navigator import SidebarNavigator

PAIRS = [
    ("rbac_test_full",   "RBAC-全权限"),
    ("rbac_test_sys",    "RBAC-仅系统管理"),
    ("rbac_test_equip",  "RBAC-仅设备管理"),
    ("rbac_test_hr",     "RBAC-仅人员管理"),
    ("rbac_test_mix",    "RBAC-混合权限"),
    ("rbac_test_none",   None),
    ("rbac_test_ro",     "RBAC-只读"),
]

def step(text):
    print(f"  -> {text}")

base = BaseDriver()
driver = None
try:
    driver = base.open_browser()
    driver.maximize_window()
    ensure_logged_in(driver)
    nav = SidebarNavigator(driver)
    nav.navigate_to("系统管理", "用户管理")
    time.sleep(3)

    for username, role_name in PAIRS:
        step(f"{username} -> {role_name}")

        if not role_name:
            step(f"  SKIP (no role)")
            continue

        # Search user
        driver.execute_script("""
            var btns = document.querySelectorAll('button');
            btns.forEach(function(b){if(b.innerText&&b.innerText.trim()==='重置')b.click();});
        """)
        time.sleep(1)
        # Type username into search
        driver.execute_script(f"""
            var inp = document.querySelector('input[placeholder*=\"搜索\"]');
            if(inp){{inp.value='{username}';inp.dispatchEvent(new Event('input',{{bubbles:true}}));}}
        """)
        time.sleep(0.5)
        # Click 查询
        driver.execute_script("""
            var btns = document.querySelectorAll('button');
            btns.forEach(function(b){if(b.innerText&&b.innerText.trim()==='查询')b.click();});
        """)
        time.sleep(2)
        step(f"  Search done")

        # Click 分配角色 via text match
        clicked = driver.execute_script(f"""
            var rows = document.querySelectorAll('tr.el-table__row');
            for(var i=0;i<rows.length;i++){{
                if(rows[i].innerText.indexOf('{username}')===-1) continue;
                var btns = rows[i].querySelectorAll('button');
                for(var k=0;k<btns.length;k++){{
                    var t = (btns[k].innerText||'').trim();
                    if(t === '分配角色'){{btns[k].click();return 'ok';}}
                }}
            }}
            return 'not found';
        """)
        time.sleep(3)
        step(f"  Click 分配角色: {clicked}")

        # Check title
        title = driver.execute_script("""
            var dlg=document.querySelector('.el-dialog');
            return dlg?dlg.querySelector('.el-dialog__title')?.innerText||'':'no dlg';
        """)
        step(f"  Dialog title: {title}")
        if '分配角色' not in title:
            step(f"  WRONG dialog! Expected 分配角色")
            # Close
            driver.execute_script("""
                var dlg=document.querySelector('.el-dialog');
                if(dlg){var c=dlg.querySelector('.el-dialog__footer button:not(.el-button--primary)');if(c)c.click();}
            """)
            time.sleep(1)
            continue

        # Check the target role checkbox
        checked = driver.execute_script(f"""
            var dlg=document.querySelector('.el-dialog');
            if(!dlg) return 'no dlg';
            var cbs=dlg.querySelectorAll('label.el-checkbox');
            var result=[];
            cbs.forEach(function(cb){{
                var t=(cb.innerText||'').trim();
                if(t==='{role_name}'){{
                    var isChecked=cb.classList.contains('is-checked');
                    result.push({{text:t,checked:isChecked}});
                    if(!isChecked){{cb.click();result.push('clicked');}}
                }}
            }});
            return JSON.stringify(result);
        """)
        time.sleep(1)
        step(f"  Role checkbox: {checked}")

        # Confirm
        driver.execute_script("""
            var dlg=document.querySelector('.el-dialog');
            if(dlg){var btn=dlg.querySelector('.el-dialog__footer button.el-button--primary');if(btn)btn.click();}
        """)
        time.sleep(2)
        toast = driver.execute_script("return document.querySelector('.el-message__content')?.innerText||'';")
        step(f"  Toast: {toast}")
        time.sleep(1)

    print("\nDone!")

finally:
    if driver:
        try: base.close_browser()
        except: pass
