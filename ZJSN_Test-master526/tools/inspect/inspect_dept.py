"""Debug: actually open add user dialog and select department"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from base.browser_driver import BaseDriver, ensure_logged_in
from base.sidebar_navigator import SidebarNavigator

base = BaseDriver()
driver = None
try:
    driver = base.open_browser()
    driver.maximize_window()
    ensure_logged_in(driver)
    nav = SidebarNavigator(driver)
    nav.navigate_to("系统管理", "用户管理")
    time.sleep(3)

    # Search for test user first - check if exists
    exists = driver.execute_script("""
        return fetch('https://aiwechatminidemo.cimc-digital.com/api/system/user/list?pageNum=1&pageSize=1&username=rbac_test_full',{
            headers:{'Authorization':'Bearer '+JSON.parse(decodeURIComponent(document.cookie.split('authorized-token=')[1].split(';')[0])).accessToken}
        }).then(r=>r.json());
    """)
    recs = exists.get('data',{}).get('records',[])
    if any(u.get('username')=='rbac_test_full' for u in recs):
        print("rbac_test_full already EXISTS!")
    else:
        print("rbac_test_full does NOT exist")

    # Click 新增
    driver.execute_script("""
        var btns = document.querySelectorAll('button');
        for (var i = 0; i < btns.length; i++) {
            if (btns[i].innerText && btns[i].innerText.trim() === '新增') {
                btns[i].click();
                break;
            }
        }
    """)
    time.sleep(2)

    # Now look at the department dropdown structure
    dept_info = driver.execute_script("""
        var dlg = document.querySelector('.el-dialog');
        if (!dlg) return 'NO DIALOG';

        // Find 部门 form item
        var items = dlg.querySelectorAll('.el-form-item');
        var target = null;
        items.forEach(function(item) {
            var label = item.querySelector('.el-form-item__label');
            if (label && label.innerText.indexOf('部门') !== -1) target = item;
        });
        if (!target) return 'NO 部门 FORM ITEM';

        // Get the inner HTML of the 部门 form item
        var html = target.innerHTML;
        // Find the el-select
        var select = target.querySelector('.el-select');
        if (select) {
            return {
                html: html.substring(0, 1000),
                hasTreeSelect: !!target.querySelector('.el-tree-select, .el-tree'),
                hasSelect: !!select,
                selectClasses: select.className,
                placeholder: target.innerText.substring(0, 200)
            };
        }
        return {html: html.substring(0, 500), hasSelect: false};
    """)

    import json
    print(json.dumps(dept_info, ensure_ascii=False, indent=2))

    # Now click the department select and see what opens
    driver.execute_script("""
        var dlg = document.querySelector('.el-dialog');
        var items = dlg.querySelectorAll('.el-form-item');
        var target = null;
        items.forEach(function(item) {
            var label = item.querySelector('.el-form-item__label');
            if (label && label.innerText.indexOf('部门') !== -1) target = item;
        });
        if (target) {
            var trigger = target.querySelector('.el-select__wrapper, .el-select__selection, .el-select');
            if (trigger) {
                trigger.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
                trigger.click();
            }
        }
    """)
    time.sleep(2)

    # Check what options appear
    options = driver.execute_script("""
        var poppers = document.querySelectorAll('.el-popper');
        var result = [];
        poppers.forEach(function(p) {
            if (p.offsetWidth > 0 || p.offsetHeight > 0) {
                var treeItems = p.querySelectorAll('.el-tree-node__content');
                var listItems = p.querySelectorAll('.el-select-dropdown__item');
                result.push({
                    visible: p.offsetWidth > 0,
                    treeItems: treeItems.length,
                    listItems: listItems.length,
                    text: (p.innerText || '').substring(0, 300),
                    hasTree: !!p.querySelector('.el-tree'),
                });
            }
        });
        return result;
    """)
    print("\nVisible poppers:")
    for o in options:
        print(f"  visible={o['visible']} tree={o['treeItems']} list={o['listItems']} hasTree={o['hasTree']}")
        print(f"  text={o['text'][:200]}")

    # Close dialog
    driver.execute_script("""
        var dlg = document.querySelector('.el-dialog');
        if (dlg) {
            var btn = dlg.querySelector('.el-dialog__footer button:not(.el-button--primary)');
            if (btn) btn.click();
        }
    """)
    time.sleep(1)

finally:
    if driver:
        try: driver.quit()
        except: pass
