"""Debug: select a department in the add-user dialog via JS"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from base.browser_driver import BaseDriver, ensure_logged_in
from base.sidebar_navigator import SidebarNavigator
from page.system_page.UserManagePage import UserManagePage

base = BaseDriver()
driver = None
try:
    driver = base.open_browser()
    ensure_logged_in(driver)
    nav = SidebarNavigator(driver)
    nav.navigate_to("系统管理", "用户管理")
    time.sleep(3)

    up = UserManagePage(driver)
    up.click_reset_button()
    up.click_add_user_button()
    time.sleep(2)

    up.input_dialog_input("用户名", "test_dept_debug")
    up.input_dialog_input("姓名", "部门选择测试")
    up.input_password_in_dialog("Ajyl@2026")

    # Click the 部门 select to open it
    sel_result = driver.execute_script("""
        var dlg = document.querySelector('.el-dialog');
        if (!dlg) return 'no dialog';

        // Find the 部门 form item
        var items = dlg.querySelectorAll('.el-form-item');
        var target = null;
        items.forEach(function(item) {
            var label = item.querySelector('.el-form-item__label');
            if (label && label.innerText.indexOf('部门') !== -1) target = item;
        });
        if (!target) return 'no 部门 item';

        // Click the select wrapper
        var select = target.querySelector('.el-select__wrapper, .el-select');
        if (select) {
            select.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
            select.click();
            return 'clicked select';
        }
        return 'no select found';
    """)
    print(f"1. Select click: {sel_result}")
    time.sleep(2)

    # Check what's visible now
    popper_info = driver.execute_script("""
        var infos = [];
        document.querySelectorAll('.el-popper').forEach(function(p) {
            if (p.offsetWidth > 0 && p.offsetHeight > 0) {
                infos.push({
                    text: (p.innerText || '').substring(0, 200),
                    treeItems: p.querySelectorAll('.el-tree-node__content').length,
                    content: p.innerHTML.substring(0, 500)
                });
            }
        });
        return infos;
    """)
    for info in popper_info:
        print(f"2. Visible popper: text={info.get('text','')[:100]}")
        print(f"   treeItems={info.get('treeItems',0)}")
        print(f"   content={info.get('content','')[:200]}")

    # Try clicking tree node via JS
    clicked = driver.execute_script("""
        var popper = document.querySelector('.el-popper');
        if (!popper) return 'no popper';

        // Find and click first tree node
        var nodes = popper.querySelectorAll('.el-tree-node__content');
        if (nodes.length === 0) return 'no tree nodes';

        // Click first node (root) to expand it
        nodes[0].click();
        return 'clicked first node: ' + (nodes[0].innerText || '').trim();
    """)
    time.sleep(2)
    print(f"3. Tree click: {clicked}")

    # Check for children
    children_info = driver.execute_script("""
        var popper = document.querySelector('.el-popper');
        if (!popper) return 'no popper';
        var allNodes = popper.querySelectorAll('.el-tree-node__content');
        var texts = [];
        allNodes.forEach(function(n) {
            texts.push((n.innerText || '').trim());
        });
        return texts;
    """)
    print(f"4. All tree nodes after click: {children_info}")

    # Close dialog
    driver.execute_script("""
        var dlg = document.querySelector('.el-dialog');
        if (dlg) {
            var cancel = dlg.querySelector('.el-dialog__footer button:not(.el-button--primary)');
            if (cancel) cancel.click();
        }
    """)
    time.sleep(1)
    print("\nDone")

finally:
    if driver:
        try: driver.quit()
        except: pass
