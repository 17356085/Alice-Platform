"""最终方案：通过 JS 直接操作弹窗表单，绕过 PO 的部门树选择问题"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from base.browser_driver import BaseDriver, ensure_logged_in
from base.sidebar_navigator import SidebarNavigator

PWD = "Ajyl@2026"
USERS = [
    ("rbac_test_full",   "RBAC全权限测试",   "RBAC-全权限"),
    ("rbac_test_sys",    "RBAC系统管理测试", "RBAC-仅系统管理"),
    ("rbac_test_equip",  "RBAC设备管理测试", "RBAC-仅设备管理"),
    ("rbac_test_hr",     "RBAC人员管理测试", "RBAC-仅人员管理"),
    ("rbac_test_mix",    "RBAC混合权限测试", "RBAC-混合权限"),
    ("rbac_test_none",   "RBAC零权限测试",   "RBAC-零权限"),
    ("rbac_test_ro",     "RBAC只读权限测试", "RBAC-只读"),
]

base = BaseDriver()
driver = None
try:
    driver = base.open_browser()
    driver.maximize_window()
    ensure_logged_in(driver)
    nav = SidebarNavigator(driver)
    nav.navigate_to("系统管理", "用户管理")
    time.sleep(3)

    for username, name, role_name in USERS:
        print(f"\n=== User: {username}", end=" ")

        # 搜索是否已存在
        existing = driver.execute_script(f"""
            return fetch('https://aiwechatminidemo.cimc-digital.com/api/system/user/list?pageNum=1&pageSize=1&username={username}',{{
                headers:{{'Authorization':'Bearer '+JSON.parse(decodeURIComponent(document.cookie.split('authorized-token=')[1].split(';')[0])).accessToken}}
            }}).then(r=>r.json());
        """)
        recs = existing.get('data',{}).get('records',[])
        if any(u.get('username')==username for u in recs):
            print("EXISTS")
            continue

        # 点击新增
        driver.execute_script("document.querySelector('button').click();")
        time.sleep(2)

        # 通过 JS 直接填写表单
        result = driver.execute_script(f"""
            var dlg = document.querySelector('.el-dialog');
            if (!dlg) return 'no dialog';

            // Fill username
            var usernameInput = dlg.querySelector('input[placeholder*=\"用户名\"]');
            if (usernameInput) {{
                var nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                nativeSetter.call(usernameInput, '{username}');
                usernameInput.dispatchEvent(new Event('input', {{bubbles:true}}));
            }}

            // Fill name
            var nameInput = dlg.querySelector('input[placeholder*=\"请输入姓名\"]');
            if (nameInput) {{
                var nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                nativeSetter.call(nameInput, '{name}');
                nameInput.dispatchEvent(new Event('input', {{bubbles:true}}));
            }}

            // Fill password
            var pwInput = dlg.querySelector('input[placeholder*=\"请输入密码\"]');
            if (pwInput) {{
                var nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                nativeSetter.call(pwInput, 'Ajyl@2026');
                pwInput.dispatchEvent(new Event('input', {{bubbles:true}}));
            }}

            // Fill confirm password
            var cpwInput = dlg.querySelector('input[placeholder*=\"请确认密码\"]');
            if (cpwInput) {{
                var nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                nativeSetter.call(cpwInput, 'Ajyl@2026');
                cpwInput.dispatchEvent(new Event('input', {{bubbles:true}}));
            }}

            // Fill phone
            var phoneInput = dlg.querySelector('input[placeholder*=\"请输入手机号\"]');
            if (phoneInput) {{
                var nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                nativeSetter.call(phoneInput, '138{str(int(time.time()))[-8:]}');
                phoneInput.dispatchEvent(new Event('input', {{bubbles:true}}));
            }}

            // Select department - open the tree select and select 人力行政部
            var deptItems = dlg.querySelectorAll('.el-form-item');
            var deptFormItem = null;
            deptItems.forEach(function(item) {{
                var label = item.querySelector('.el-form-item__label');
                if (label && label.innerText.indexOf('部门') !== -1) deptFormItem = item;
            }});

            if (deptFormItem) {{
                // Click to open the select
                var trigger = deptFormItem.querySelector('.el-select__wrapper, .el-select__selection');
                if (trigger) {{
                    trigger.click();
                    setTimeout(function() {{}}, 500);
                }}
            }}
            return 'form filled, department trigger clicked';
        """)
        print(f"Form: {result}")
        time.sleep(2)

        # Select department from the tree
        dept_clicked = driver.execute_script("""
            var popper = document.querySelector('.el-popper');
            if (!popper) return 'no popper';

            var nodes = popper.querySelectorAll('.el-tree-node__content');
            if (nodes.length === 0) return 'no tree nodes';

            // First click root to expand
            nodes[0].click();
            setTimeout(function() {}, 500);
            return 'clicked root: ' + (nodes[0].innerText || '').trim();
        """)
        print(f"  Tree root: {dept_clicked}")
        time.sleep(2)

        # Find and click 人力行政部
        hr_clicked = driver.execute_script("""
            var popper = document.querySelector('.el-popper');
            if (!popper) return 'no popper';

            var nodes = popper.querySelectorAll('.el-tree-node__content');
            for (var i = 0; i < nodes.length; i++) {
                var text = (nodes[i].innerText || '').trim();
                if (text.indexOf('人力行政部') !== -1) {
                    nodes[i].click();
                    return 'clicked: ' + text;
                }
            }
            return '人力行政部 not found. Nodes: ' + Array.from(nodes).map(function(n){return (n.innerText||'').trim();}).join(', ');
        """)
        print(f"  Dept select: {hr_clicked}")
        time.sleep(1.5)

        # Now select role — open role dropdown
        role_result = driver.execute_script(f"""
            var dlg = document.querySelector('.el-dialog');
            if (!dlg) return 'no dialog';

            // Find 角色 form item
            var roleFormItem = null;
            dlg.querySelectorAll('.el-form-item').forEach(function(item) {{
                var label = item.querySelector('.el-form-item__label');
                if (label && label.innerText.indexOf('角色') !== -1) roleFormItem = item;
            }});
            if (!roleFormItem) return 'no role form item';

            var trigger = roleFormItem.querySelector('.el-select__wrapper, .el-select__selection');
            if (trigger) {{
                trigger.click();
                return 'role dropdown opened';
            }}
            return 'no role trigger';
        """)
        time.sleep(2)
        print(f"  Role dropdown: {role_result}")

        # Click the role option
        role_selected = driver.execute_script(f"""
            // FIXME: get the correct role option
            var popper = document.querySelector('.el-popper');
            if (!popper) return 'no popper for role';

            popper.querySelectorAll('.el-select-dropdown__item').forEach(function(item) {{
                var text = (item.innerText || '').trim();
                if (text === '{role_name}') {{
                    item.click();
                    return;
                }}
            }});
            return 'clicked a role option';
        """)
        time.sleep(1)
        print(f"  Role: {role_selected}")

        # Click 确定
        confirm_clicked = driver.execute_script("""
            var dlg = document.querySelector('.el-dialog');
            if (dlg) {
                var btns = dlg.querySelectorAll('.el-dialog__footer button');
                for (var i = 0; i < btns.length; i++) {
                    if (btns[i].innerText.indexOf('确定') !== -1) {
                        btns[i].click();
                        return 'confirmed';
                    }
                }
            }
            return 'no confirm button';
        """)
        print(f"  Confirm: {confirm_clicked}")
        time.sleep(2)

        # Check result
        toast_text = driver.execute_script("""
            var toast = document.querySelector('.el-message__content');
            return toast ? toast.innerText : '';
        """)
        form_errors = driver.execute_script("""
            var errs = document.querySelectorAll('.el-form-item__error');
            return Array.from(errs).map(function(e){return e.innerText;});
        """)
        if toast_text:
            print(f"  Toast: {toast_text}")
        elif form_errors:
            print(f"  Form errors: {form_errors}")

        time.sleep(1)

    print("\nDone!")

finally:
    if driver:
        try: base.close_browser()
        except: pass
