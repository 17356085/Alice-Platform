"""调试脚本 v2 — 检查登录后侧边栏渲染情况"""
import os, sys, time, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base.browser_driver import BaseDriver, ensure_logged_in

base = BaseDriver()
driver = base.open_browser()
try:
    print("[1] 登录...")
    ensure_logged_in(driver)

    # 等待 Vue 渲染
    print("[2] 等待页面渲染 (5s)...")
    time.sleep(5)

    # 保存截图
    driver.save_screenshot("debug_output/after_login.png")
    print("[3] 截图已保存")

    # 检查关键信息
    info = driver.execute_script("""
        var result = {};

        // 1. 检查 iframe
        result.iframes = document.querySelectorAll('iframe').length;

        // 2. 检查 sidebar
        var sidebar = document.querySelector('.sidebar-container, .el-aside, [class*=sidebar]');
        result.hasSidebar = !!sidebar;
        if (sidebar) {
            result.sidebarTag = sidebar.tagName;
            result.sidebarClass = sidebar.className;
            result.sidebarDisplay = window.getComputedStyle(sidebar).display;
            result.sidebarWidth = sidebar.offsetWidth;
        }

        // 3. 检查 el-menu
        var menus = document.querySelectorAll('.el-menu');
        result.elMenuCount = menus.length;
        for (var i = 0; i < menus.length; i++) {
            var m = menus[i];
            if (m.offsetHeight > 0) {
                result['menu_' + i] = {
                    tag: m.tagName,
                    class: m.className,
                    display: window.getComputedStyle(m).display,
                    width: m.offsetWidth,
                    height: m.offsetHeight,
                };
            }
        }

        // 4. 检查 el-sub-menu__title
        var titles = document.querySelectorAll('.el-sub-menu__title');
        result.subMenuTitleCount = titles.length;
        var visibleTitles = [];
        for (var i = 0; i < titles.length; i++) {
            if (titles[i].offsetHeight > 0) {
                visibleTitles.push((titles[i].textContent || '').trim().substring(0, 30));
            }
        }
        result.visibleSubMenuTitles = visibleTitles;

        // 5. 检查 el-menu-item
        var items = document.querySelectorAll('.el-menu-item');
        result.menuItemCount = items.length;
        var visibleItems = [];
        for (var i = 0; i < items.length; i++) {
            if (items[i].offsetHeight > 0) {
                visibleItems.push((items[i].textContent || '').trim().substring(0, 30));
            }
        }
        result.visibleMenuItems = visibleItems;

        // 6. 检查当前 URL
        result.url = window.location.href;
        result.hash = window.location.hash;

        // 7. 检查 body 直属子元素
        var bodyChildren = [];
        for (var i = 0; i < document.body.children.length; i++) {
            var c = document.body.children[i];
            var cls = String(c.className || '').substring(0, 50);
            bodyChildren.push(c.tagName + '.' + cls);
        }
        result.bodyChildren = bodyChildren;

        return JSON.stringify(result, null, 2);
    """)

    print("[4] 页面结构信息:")
    print(info)

    # 保存到文件
    with open("debug_output/login_page_info.json", "w", encoding="utf-8") as f:
        f.write(info)
    print("\n[5] 信息已保存到 debug_output/login_page_info.json")

finally:
    base.close_browser()
